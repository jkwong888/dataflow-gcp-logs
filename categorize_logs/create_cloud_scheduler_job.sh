#!/bin/bash



URI=https://dataflow.googleapis.com/v1b3/projects/jkwng-fruitshop-logs/locations/us-central1/flexTemplates:launch
CLIENT_SERVICE_ACCOUNT_EMAIL=jkwng-cloud-scheduler@jkwng-fruitshop-logs.iam.gserviceaccount.com
BODY=`echo "
{
    "launch_parameter": {
        "jobName": "categorize-logs-asdfasdf",
        "containerSpecGcsPath": "gs://jkwng-dataflow-metadata/categorize-logs",
        "parameters": {
            "input": "gs://fruitshop-logs/stdout/2021/04/09/",
            "output": "gs://fruitshop-logs-staging/categories-2021-04-09.txt",
            "worker_region": "us-central1",
            "network": "shared-network",
            "subnetwork": "https://www.googleapis.com/compute/v1/projects/shared-vpc-host-project-55427/regions/us-central1/subnetworks/dataflow-central1",
            "no_use_public_ips": "true"
        }
    }
}
" | base64`
SCOPE=https://www.googleapis.com/auth/cloud-platform


#gcloud scheduler jobs create http ${JOB_ID} \
#    --schedule="every 1 hour" \
#    --uri=${URI} \
#    --oidc-service-account-email=${CLIENT_SERVICE_ACCOUNT_EMAIL}

echo $BODY