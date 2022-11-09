resource "google_bigquery_dataset" "default" {
  project = module.service_project.project_id
  dataset_id                  = "jkwng_data_${random_id.random_suffix.hex}"
  location                    = var.region
}

resource "google_bigquery_dataset_iam_member" "dataflow_write" {
  project   = module.service_project.project_id
  dataset_id = google_bigquery_dataset.default.dataset_id
  role = "roles/bigquery.dataEditor"
  member = format("serviceAccount:%s",google_service_account.dataflow_sa.email)

}

resource "google_project_iam_member" "dataflow_job_user" {
  project   = module.service_project.project_id
  role = "roles/bigquery.jobUser"
  member = format("serviceAccount:%s",google_service_account.dataflow_sa.email)

}