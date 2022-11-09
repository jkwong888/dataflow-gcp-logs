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
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window

# Defines the BigQuery schema for the output table.
SCHEMA = ",".join(
    [
        "url:STRING",
        "num_reviews:INTEGER",
        "avg_score:FLOAT64",
        "date:TIMESTAMP",
    ]
)


class GenerateRecord(beam.DoFn):
  def __init__(self, date):
    self.date = date

  def process(self, record):
    # a record looks like: ('url', (avg_score count))
    # we want to return: {'url': url, 'avg_score': avg_score, 'num_reviews': count, 'date': date})

    yield {
        'url': record[0], 
        'avg_score': record[1][0], 
        'num_reviews': record[1][1], 
        'date': self.date,
    }

class AverageFn(beam.CombineFn):
  def create_accumulator(self):
    sum = 0.0
    count = 0
    accumulator = sum, count
    return accumulator

  def add_input(self, accumulator, input):
    sum, count = accumulator
    return sum + input, count + 1

  def merge_accumulators(self, accumulators):
    # accumulators = [(sum1, count1), (sum2, count2), (sum3, count3), ...]
    sums, counts = zip(*accumulators)
    # sums = [sum1, sum2, sum3, ...]
    # counts = [count1, count2, count3, ...]
    return sum(sums), sum(counts)

  def extract_output(self, accumulator):
    sum, count = accumulator
    if count == 0:
      return float('NaN')
    return (sum / count, count)

def run(
    project: str,
    dataset: str,
    table: str,
    gcs_input_path: str,
    gcs_temp_location: str,
    record_date: datetime,
    beam_args: List[str] = None,
) -> None:
    """Build and run the pipeline."""
    options = PipelineOptions(beam_args, save_main_session=True)

    with beam.Pipeline(options=options) as pipeline:
        score_records = (
            pipeline
            | "Read input from parquet" >> beam.io.ReadFromParquet("/".join([gcs_input_path, record_date.strftime("%Y%m%d"), ""]))
            | "Filter by hour" >> beam.Filter(lambda x: datetime.fromtimestamp(x["post_time"] / 1000.0, tz=timezone.utc).hour == record_date.hour)
            | "Format Map" >> beam.Map(lambda record: (record['url'], record['score']))
            | "Average" >> beam.CombinePerKey(AverageFn())
            | 'format' >> beam.ParDo(GenerateRecord(record_date))
        )

        _ = (
            score_records
            | "Write to Big Query" >> beam.io.WriteToBigQuery(
                table=table, 
                dataset=dataset,
                project=project,
                schema=SCHEMA,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                custom_gcs_temp_location=gcs_temp_location)
        )

        _ = (
            score_records 
            | "printy" >> beam.Map(lambda x: logging.info(x))
        )


"""
        total_scores = (
            scores
            | "sum all scores" >> beam.CombineValues(sum)
        )

        count_scores = (
            scores
            | "count of scores" >> beam.Map(lambda record: (record[0], len(record[1])))
        )
        score_records = (({
            'totals': total_scores, 'counts': count_scores
        })
            | "merge" >> beam.CoGroupByKey()
            | 'format' >> beam.ParDo(GenerateRecord(record_date))
        )

        _ = (
            score_records 
            | "printy" >> beam.Map(lambda x: logging.info(x))
        )

        # Output the results into BigQuery table.
        _ = (
            score_records 
            | "Write to Big Query" >> beam.io.WriteToBigQuery(
                table=table, 
                dataset=dataset,
                project=project,
                schema=SCHEMA,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                custom_gcs_temp_location=gcs_temp_location)
        )
"""

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_table",
        help="Output BigQuery table for results specified as: "
        "PROJECT:DATASET.TABLE or DATASET.TABLE.",
    )

    parser.add_argument(
        "--gcs_input_path",
        help="Input storage bucket, root of where parquet records are dumped"
        "gs://<bucket-name>/path",
    )

    parser.add_argument(
        "--gcs_temp_location",
        help="storage bucket for temp bq loads, "
        "gs://<bucket-name>/path",
    )

    parser.add_argument(
        "--date",
        help="the day to generate the aggregates for"
        "YYYYmmDD",
    )

    parser.add_argument(
        "--hour_of_day",
        help="the hour of day to generate the aggregates for"
        "0-23",
    )

    args, beam_args = parser.parse_known_args()

    record_date = datetime.strptime(args.date, "%Y%m%d")
    record_date = record_date.replace(hour=int(args.hour_of_day))

    logging.info("Processing date: %s", record_date)

    dataset_table = args.output_table.split('.')
    table = dataset_table[1]
    pr_dataset = dataset_table[0]
    project_dataset = pr_dataset.split(':')
    project = project_dataset[0]
    dataset = project_dataset[1]
    logging.info("Output to: project: %s, dataset: %s, table: %s", project, dataset, table)

    run(
        project=project,
        dataset=dataset,
        table=table,
        gcs_input_path=args.gcs_input_path,
        gcs_temp_location=args.gcs_temp_location,
        record_date=record_date,
        beam_args=beam_args,
    )