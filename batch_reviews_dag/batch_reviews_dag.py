# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START composer_dataflow_dag]


"""Example Airflow DAG that creates a Cloud Dataflow workflow which takes a
text file and adds the rows to a BigQuery table.

This DAG relies on four Airflow variables
https://airflow.apache.org/concepts.html#variables
* project_id - Google Cloud Project ID to use for the Cloud Dataflow cluster.
* gce_zone - Google Compute Engine zone where Cloud Dataflow cluster should be
  created.
* gce_region - Google Compute Engine region where Cloud Dataflow cluster should be
  created.
Learn more about the difference between the two here:
https://cloud.google.com/compute/docs/regions-zones
* bucket_path - Google Cloud Storage bucket where you've stored the User Defined
Function (.js), the input file (.txt), and the JSON schema (.json).
"""

import datetime
import shutil
import logging

from airflow import DAG
from airflow import models
from airflow.operators.dummy import DummyOperator
from airflow.providers.google.cloud.operators.dataflow import (
    DataflowStartFlexTemplateOperator,
)

from airflow.utils.dates import days_ago

project_id = models.Variable.get("project_id")
gce_region = models.Variable.get("gce_region")
bucket_path = models.Variable.get("bucket_path")

dt_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

default_args = {
    # Tell airflow to start one day ago, so that it runs as soon as you upload it
    "start_date": days_ago(1),
    "dataflow_default_options": {
        "project": project_id,
        # Set to your region
        "region": gce_region,
        # This is a subfolder for storing temporary files, like the staged pipeline job.
        "temp_location": f'{bucket_path}/dataflow-temp',
        "staging_location": f'{bucket_path}/dataflow-staging',
    },
    "retries": 2,
}


# Define a DAG (directed acyclic graph) of tasks.
# Any task you create within the context manager is automatically added to the
# DAG object.
with DAG(
    # The id you will see in the DAG airflow page
    "batch_reviews",
    start_date=days_ago(1),
    schedule_interval=datetime.timedelta(hours=1),  # run hourly
    default_args=default_args,
    # The interval with which to schedule the DAG
) as dag:
    start = DummyOperator(
        task_id='start',
        dag=dag,
    )

    start_flex_template = DataflowStartFlexTemplateOperator(
        task_id="start_batch_reviews",
        body={
            "launchParameter": {
                "containerSpecGcsPath": f'{bucket_path}/samples/dataflow/templates/batch-reviews.json',
                "jobName": f'batch-reviews-{dt_now}',
                "parameters": {
                    "gcs_input_path": f'{bucket_path}/reviews_raw',
                    "output_table": f'{project_id}:jkwng_data_a8f6.batch_reviews',
                    "hour_of_day": '{{ (execution_date - macros.timedelta(hours=-1)).strftime("%H") }}',
                    "date": '{{ (execution_date - macros.timedelta(hours=-1)).strftime("%Y%m%d") }}',
                    "gcs_temp_location": f'{bucket_path}/batch_reviews_tmp',
                },
                "launchOptions": {
                    "temp_location": f'{bucket_path}/dataflow-temp',
                    "staging_location": f'{bucket_path}/dataflow-staging',
                }
            }
        },
        do_xcom_push=True,
        location=gce_region,
        dag=dag,
    )

    end = DummyOperator(
        task_id='end',
        dag=dag,
    )

    start >> start_flex_template >> end


# [END composer_dataflow_dag]