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

from git import Repo

from google.cloud import storage

from airflow import models
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.operators.subdag import SubDagOperator
from airflow.providers.apache.beam.operators.beam import (
    BeamRunPythonPipelineOperator,
)
from airflow.operators.bash_operator import BashOperator

from airflow.utils.dates import days_ago

project_id = models.Variable.get("project_id")
gce_zone = models.Variable.get("gce_zone")
gce_region = models.Variable.get("gce_region")
bucket_path = models.Variable.get("bucket_path")

default_args = {
    # Tell airflow to start one day ago, so that it runs as soon as you upload it
    "start_date": days_ago(1),
    "dataflow_default_options": {
        "project": project_id,
        # Set to your region
        "region": gce_region,
        # Set to your zone
        "zone": gce_zone,
        # This is a subfolder for storing temporary files, like the staged pipeline job.
        "temp_location": bucket_path + "/tmp/",
    },
}

shutil.rmtree('/tmp/dataflow-gcp-logs', ignore_errors=True)
Repo.clone_from("https://github.com/jkwong888/dataflow-gcp-logs.git", "/tmp/dataflow-gcp-logs")


def merge_cats(**kwargs):
    storage_client = storage.Client()

    blobs = storage_client.list_blobs(kwargs['bucket'], prefix=kwargs['source'], delimiter='/')
    logging.info("{0}".format(blobs))

    blob = '\n'.join(b.download_as_string().decode('utf-8') for b in blobs)
    old_categories = blob.split()
    logging.info("old_categories (gs://{0}/{1})): {2}".format(kwargs['bucket'], kwargs['source'], old_categories))

    new_blobs = storage_client.list_blobs(kwargs['bucket'], prefix=kwargs['input'], delimiter='/')
    logging.info("{0}".format(new_blobs))
    new_blob = '\n'.join(b.download_as_string().decode('utf-8') for b in new_blobs)
    new_categories = new_blob.split()

    logging.info("new_categories: (gs://{0}/{1}): {2}".format(kwargs['bucket'], kwargs['input'], new_categories))

    # write the merged category list back to gs
    updated = list(set(old_categories) | set(new_categories))
    logging.info("writing merged to: (gs://{0}/{1}): {2}".format(kwargs['bucket'], kwargs['source'], updated))

    with open('/tmp/tmpfile', 'wt') as file:
        file.write('\n'.join(updated))

    storage_client.bucket(kwargs['bucket']).blob(kwargs['source']).upload_from_filename('/tmp/tmpfile')

    # delete the input files
    new_blobs = storage_client.list_blobs(kwargs['bucket'], prefix=kwargs['input'], delimiter='/')
    for b in new_blobs:
        try:
            logging.info("deleting gs://{0}/{1})".format(kwargs['bucket'], b.name))
            b.delete()
        except google.cloud.exceptions.NotFound:
            pass





# Define a DAG (directed acyclic graph) of tasks.
# Any task you create within the context manager is automatically added to the
# DAG object.
with models.DAG(
    # The id you will see in the DAG airflow page
    "category_dag",
    default_args=default_args,
    # The interval with which to schedule the DAG
    schedule_interval=datetime.timedelta(hours=1),  # Override to match your needs
) as dag:
    debug1 = BashOperator(
        task_id='print_execution_date',
        bash_command='echo {{ execution_date }}',
        dag=dag
    )

    start = DummyOperator(
        task_id='start',
        dag=dag,
    )

    # t1, t2 and t3 are examples of tasks created by instantiating operators
    # [START howto_operator_start_python_direct_runner_pipeline_local_file]
    categorize_logs_local_direct_runner = BeamRunPythonPipelineOperator(
        task_id="categorize",
        runner="DirectRunner",
        py_file='/tmp/dataflow-gcp-logs/categorize_logs.py',
        py_options=[],
        py_requirements=['apache-beam[gcp]==2.26.0'],
        py_interpreter='python3',
        py_system_site_packages=False,
        pipeline_options={
            'input': 'gs://fruitshop-logs/stdout/{{ (execution_date - macros.timedelta(hours=1)).strftime("%Y/%m/%d/%H") }}*.json',
            'output': 'gs://fruitshop-logs-staging/categories-{{ execution_date.strftime("%Y-%m-%d-%H") }}.txt',
        },
        dag=dag,
    )

    merge_categories = PythonOperator(
        task_id='merge_categories',
        python_callable=merge_cats,
        op_kwargs={
            'bucket': 'fruitshop-logs-staging',
            'source': 'categories-all.txt',
            'input': 'categories-{{ execution_date.strftime("%Y-%m-%d-%H") }}.txt',
        },
        dag=dag,
    )

    end = DummyOperator(
        task_id='end',
        dag=dag,
    )


    start >> debug1 >> categorize_logs_local_direct_runner >> merge_categories >> end


# [END composer_dataflow_dag]