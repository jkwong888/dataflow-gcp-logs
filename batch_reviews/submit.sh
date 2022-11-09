#!/bin/bash

BUCKET=jkwng-bucket-a8f6
VERSION=1.0.2
TEMPLATE_PATH=gs://$BUCKET/samples/dataflow/templates/batch-reviews.json
TEMPLATE_IMAGE=gcr.io/jkwng-images/dataflow-batch-reviews:$VERSION
VPC_PROJECT=jkwng-nonprod-vpc
PROJECT=jkwng-dataflow-dev-a8f6
SUBSCRIPTION=jkwng-dataflow-reviews-subscription-a8f6
DATASET=jkwng_data_a8f6
TABLE=batch_reviews
REGION=us-central1
SUBNETWORK=dataflow-dev
SERVICE_ACCOUNT=dataflow-sa@jkwng-dataflow-dev-a8f6.iam.gserviceaccount.com

#gcloud builds submit --tag "$TEMPLATE_IMAGE"

#gcloud dataflow flex-template build $TEMPLATE_PATH \
#  --image "$TEMPLATE_IMAGE" \
#  --sdk-language "PYTHON" \
#  --metadata-file "metadata.json" \
#  --subnetwork=https://www.googleapis.com/compute/v1/projects/${VPC_PROJECT}/regions/${REGION}/subnetworks/${SUBNETWORK} \
#  --service-account-email=${SERVICE_ACCOUNT} \
#  --staging-location=gs://${BUCKET}/dataflow_staging \
#  --temp-location=gs://${BUCKET}/dataflow_temp \
#  --worker-region=${REGION}


gcloud dataflow flex-template run "batch-reviews-`date +%Y%m%d-%H%M%S`" \
    --template-file-gcs-location=${TEMPLATE_PATH} \
    --parameters gcs_input_path=gs://${BUCKET}/reviews_raw \
    --parameters output_table=${PROJECT}:${DATASET}.${TABLE} \
    --parameters hour_of_day=19 \
    --parameters date=20221106 \
    --parameters gcs_temp_location=gs://${BUCKET}/batch_reviews_tmp \
    --staging-location=gs://${BUCKET}/dataflow_staging \
    --temp-location=gs://${BUCKET}/dataflow_temp \
    --region=${REGION} \
    --project=${PROJECT} 

##python3 ./batch_reviews.py \
##    --requirements_file=./requirements.txt \
##    --hour_of_day=19 \
##    --output_table=jkwng-dataflow-dev-a8f6:jkwng_data_a8f6.batch_reviews \
##    --staging_location=gs://dataflow-staging-us-central1-802190842362/staging \
##    --service_account_email=dataflow-sa@jkwng-dataflow-dev-a8f6.iam.gserviceaccount.com \
##    --subnetwork=https://www.googleapis.com/compute/v1/projects/jkwng-nonprod-vpc/regions/us-central1/subnetworks/dataflow-dev \
##    --gcs_temp_location=gs://jkwng-bucket-a8f6/batch_reviews_tmp \
##    --runner=DataflowRunner \
##    --gcs_input_path=gs://jkwng-bucket-a8f6/reviews_raw \
##    --project=jkwng-dataflow-dev-a8f6 \
##    --region=us-central1 \
##    --date=20221106 \
##    --job_name=batchreviews-20221106-196
