#!/bin/bash


# gcloud dataflow flex-template build \
#   gs://jkwng-dataflow-metadata/categorize-logs \
#   --image gcr.io/jkwng-cicd-274417/df-categorize-logs:latest \
#   --sdk-language "PYTHON" \
#   --metadata-file "metadata.json"

  gcloud dataflow flex-template run "categorize-logs-`date +%Y%m%d-%H%M%S`" \
    --template-file-gcs-location "gs://jkwng-dataflow-metadata/categorize-logs" \
    --parameters input="gs://fruitshop-logs/stdout/2021/04/09/*.json" \
    --parameters output="gs://fruitshop-logs-staging/categories-2021-04-09.txt" \
    --parameters prebuild_sdk_container_engine=cloud_build \
    --region "us-central1" \
    --project jkwng-fruitshop-logs \
    --network=shared-network \
    --subnetwork=https://www.googleapis.com/compute/v1/projects/shared-vpc-host-project-55427/regions/us-central1/subnetworks/dataflow-central1 \
    --additional-experiments=use_runner_v2
