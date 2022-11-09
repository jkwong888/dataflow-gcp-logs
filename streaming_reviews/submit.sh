#!/bin/bash

BUCKET=jkwng-bucket-a8f6
VERSION=1.2.5
TEMPLATE_PATH=gs://$BUCKET/samples/dataflow/templates/streaming-reviews.json
TEMPLATE_IMAGE=gcr.io/jkwng-images/dataflow-streaming-reviews:$VERSION
VPC_PROJECT=jkwng-nonprod-vpc
PROJECT=jkwng-dataflow-dev-a8f6
SUBSCRIPTION=jkwng-dataflow-reviews-subscription-a8f6
DATASET=jkwng_data_a8f6
TABLE=streaming_reviews
REGION=us-central1
SUBNETWORK=dataflow-dev
SERVICE_ACCOUNT=dataflow-sa@jkwng-dataflow-dev-a8f6.iam.gserviceaccount.com

gcloud builds submit --tag "$TEMPLATE_IMAGE"

gcloud dataflow flex-template build $TEMPLATE_PATH \
  --image "$TEMPLATE_IMAGE" \
  --sdk-language "PYTHON" \
  --metadata-file "metadata.json" \
  --additional-experiments=enable_prime

gcloud dataflow flex-template run \
	"streaming-beam-`date +%Y%m%d-%H%M%S`" \
	--template-file-gcs-location "$TEMPLATE_PATH" \
   	--parameters input_subscription="projects/$PROJECT/subscriptions/$SUBSCRIPTION" \
   	--parameters gcs_output_path="gs://${BUCKET}/reviews_raw" \
   	--parameters output_table="$PROJECT:$DATASET.$TABLE" \
   	--region "$REGION" \
	--subnetwork=https://www.googleapis.com/compute/v1/projects/${VPC_PROJECT}/regions/${REGION}/subnetworks/${SUBNETWORK} \
	--service-account-email=${SERVICE_ACCOUNT} \
	--additional-experiments=enable_prime 
