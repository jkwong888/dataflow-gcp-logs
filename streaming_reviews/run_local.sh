#!/bin/bash

python3 streaming_beam.py \
    --input_subscription=projects/jkwng-dataflow-dev-a8f6/subscriptions/jkwng-dataflow-reviews-subscription-a8f6 \
    --output_table=jkwng-dataflow-dev-a8f6:jkwng_data_a8f6.streaming_reviews \
    --gcs_output_path=gs://jkwng-bucket-a8f6/reviews_raw \
    --streaming_window_interval_sec=60 \
    --raw_window_interval_sec=60 \
    --num_shards=1