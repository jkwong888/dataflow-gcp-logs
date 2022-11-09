#!/usr/bin/env python
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""An Apache Beam streaming pipeline example.

It reads JSON encoded messages from Pub/Sub, transforms the message data and
writes the results to BigQuery.
"""

import argparse
import json
import logging
import time
import random
import pandas as pd
from typing import Any, Dict, List

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window

# Defines the BigQuery schema for the output table.
SCHEMA = ",".join(
    [
        "url:STRING",
        "num_reviews:INTEGER",
        "score:FLOAT64",
        "first_date:TIMESTAMP",
        "last_date:TIMESTAMP",
    ]
)


def parse_json_message(message: str) -> Dict[str, Any]:
    """Parse the input json message and add 'score' & 'processing_time' keys."""
    row = json.loads(message)
    return {
        "url": row["url"],
        "score": row["review"],
        "post_time": row["post_time"],
        "processing_time": int(time.time()),
    }

class WriteToGCS(beam.DoFn):
    def __init__(self, output_path):
        self.output_path = output_path

    def process(self, key_value, window=beam.DoFn.WindowParam):
        """Write messages in a batch to Google Cloud Storage."""

        ts_format = "%Y%m%d/reviews-%H%M"
        window_start = window.start.to_utc_datetime().strftime(ts_format)
        window_end = window.end.to_utc_datetime().strftime(ts_format)
        shard_id, batch = key_value
        filename = "{}/{}.{:02d}".format(self.output_path, window_start, shard_id)

        df = pd.DataFrame.from_dict(batch, orient='columns')
        #print(df)
        df.to_parquet(filename, engine="pyarrow", storage_options={"content_type": 'application/x-parquet'})

        #with beam.io.gcsio.GcsIO().open(filename=filename, mode="w") as f:
        #    f.write(f"{batch}".encode("utf-8"))




def run(
    input_subscription: str,
    output_table: str,
    gcs_output_path: str,
    streaming_window_interval_sec: int = 300,
    raw_window_interval_sec: int = 900,
    num_shards: int = 4,
    beam_args: List[str] = None,
) -> None:
    """Build and run the pipeline."""
    options = PipelineOptions(beam_args, save_main_session=True, streaming=True)

    with beam.Pipeline(options=options) as pipeline:

        rawJSON = (
            pipeline
            | "Read from PubSub"
            >> beam.io.ReadFromPubSub(
                subscription=input_subscription
            ).with_output_types(bytes)
            | "UTF-8 bytes to string" >> beam.Map(lambda msg: msg.decode("utf-8"))
            | "Parse JSON messages" >> beam.Map(parse_json_message)
        )

        _ = (
            rawJSON 
            | "Raw GCS Output window" >> beam.WindowInto(window.FixedWindows(raw_window_interval_sec, 0))
            #| "add timestamp" >> beam.ParDo(AddTimestamp())
            | "Add key" >> beam.WithKeys(lambda _: num_shards) # default 4 shards
            | "Group by key" >> beam.GroupByKey()
            | "Write parquet to GCS" >> beam.ParDo(WriteToGCS(gcs_output_path))
        )

        messages = (
            rawJSON
            | "Fixed-size windows" >> beam.WindowInto(window.FixedWindows(streaming_window_interval_sec, 0))
            | "Add URL keys" >> beam.WithKeys(lambda msg: msg["url"])
            | "Group by URLs" >> beam.GroupByKey()
            | "Get statistics"
            >> beam.MapTuple(
                lambda url, messages: {
                    "url": url,
                    "num_reviews": len(messages),
                    "score": sum(msg["score"] for msg in messages) / len(messages),
                    "first_date": min(msg["processing_time"] for msg in messages),
                    "last_date": max(msg["processing_time"] for msg in messages),
                }
            )
        )

        # Output the results into BigQuery table.
        _ = messages | "Write to Big Query" >> beam.io.WriteToBigQuery(
            output_table, schema=SCHEMA
        )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_table",
        help="Output BigQuery table for results specified as: "
        "PROJECT:DATASET.TABLE or DATASET.TABLE.",
    )
    parser.add_argument(
        "--gcs_output_path",
        help="Output storage bucket, will put messages in <raw> directory "
        "gs://<bucket-name>/path",
    )
    parser.add_argument(
        "--input_subscription",
        help="Input PubSub subscription of the form "
        '"projects/<PROJECT>/subscriptions/<SUBSCRIPTION>."',
    )
    parser.add_argument(
        "--streaming_window_interval_sec",
        default=300,
        type=int,
        help="Window interval in seconds for grouping incoming messages for write to BQ table(default 300).",
    )
    parser.add_argument(
        "--raw_window_interval_sec",
        default=900,
        type=int,
        help="Window interval in seconds for grouping messages to write to BQ(default 900).",
    )

    parser.add_argument(
        "--num_shards",
        default=4,
        type=int,
        help="Number of shards to write output to GCS (default 4)",
    )

    args, beam_args = parser.parse_known_args()

    run(
        input_subscription=args.input_subscription,
        output_table=args.output_table,
        gcs_output_path=args.gcs_output_path,
        streaming_window_interval_sec=args.streaming_window_interval_sec,
        raw_window_interval_sec=args.raw_window_interval_sec,
        num_shards=args.num_shards,
        beam_args=beam_args,
    )