resource "google_storage_bucket" "bucket" {
    project = module.service_project.project_id
    name = "jkwng-bucket-${random_id.random_suffix.hex}"
    location = var.region

    uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "dataflow_bucket" {
    bucket  = google_storage_bucket.bucket.name
    role    = "roles/storage.objectAdmin"
    member  = format("serviceAccount:%s", google_service_account.dataflow_sa.email)
}

resource "google_storage_bucket_iam_member" "compute_bucket" {
    bucket  = google_storage_bucket.bucket.name
    role    = "roles/storage.objectAdmin"
    member  = "serviceAccount:${module.service_project.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "dataflow_storage_admin" {
    project = module.service_project.project_id
    role    = "roles/storage.admin"
    member  = format("serviceAccount:%s", google_service_account.dataflow_sa.email)
}