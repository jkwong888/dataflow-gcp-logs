#!/bin/bash

python3 batch_reviews.py \
    --output_table=jkwng-dataflow-dev-a8f6:jkwng_data_a8f6.batch_reviews \
    --gcs_input_path=gs://jkwng-bucket-a8f6/reviews_raw \
    --gcs_temp_location=gs://jkwng-bucket-a8f6/batch_reviews_tmp \
    --date=20221106 \
    --hour_of_day=19  \
    --runner=DataflowRunner \
    --gcs_input_path=gs://jkwng-bucket-a8f6/reviews_raw \
    --project=jkwng-dataflow-dev-a8f6 \
    --region=us-central1 \
    --date=20221106 \
    --job_name=batchreviews-20221106-19-`date +%Y%m%d-%H%M%S` \
    --subnetwork=https://www.googleapis.com/compute/v1/projects/jkwng-nonprod-vpc/regions/us-central1/subnetworks/dataflow-dev \
    --staging_location=gs://jkwng-bucket-a8f6/dataflow_staging \
    --temp_location=gs://jkwng-bucket-a8f6/dataflow_temp \
    --service_account_email=dataflow-sa@jkwng-dataflow-dev-a8f6.iam.gserviceaccount.com 