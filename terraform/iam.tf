
resource "google_service_account" "dataflow_sa" {
    project = module.service_project.project_id
    account_id = "dataflow-sa"
}

resource "google_storage_bucket" "job_output" {
    project = module.service_project.project_id
    name = format("jkwng-wordcount-output-%s", random_id.random_suffix.hex)
    location = "us-central1"
    uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "dataflow_job_bucket" {
    bucket  = google_storage_bucket.job_output.name
    role    = "roles/storage.admin"
    member  = format("serviceAccount:%s", google_service_account.dataflow_sa.email)
}

resource "google_project_iam_member" "compute_dataflow_worker" {
    project = module.service_project.project_id
    role = "roles/dataflow.worker"
    member  = "serviceAccount:${module.service_project.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "dataflow_sa_dataflow_worker" {
    project = module.service_project.project_id
    role = "roles/dataflow.worker"
    member  = format("serviceAccount:%s", google_service_account.dataflow_sa.email)
}

resource "google_project_iam_member" "dataflow_sa_dataflow_admin" {
    project = module.service_project.project_id
    role = "roles/dataflow.admin"
    member  = format("serviceAccount:%s", google_service_account.dataflow_sa.email)
}

resource "google_compute_subnetwork_iam_member" "dataflow_network_user" {
  project = data.google_project.host_project.project_id
  subnetwork = module.service_project.subnets.0.self_link
  role = "roles/compute.networkUser"
  member  = format("serviceAccount:service-%d@dataflow-service-producer-prod.iam.gserviceaccount.com", module.service_project.number)
}