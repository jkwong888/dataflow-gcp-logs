data "google_project" "registry_project" {
    project_id = var.registry_project_id
}

# take the df SA and allow storage object browser on the image registry bucket
resource "google_storage_bucket_iam_member" "registry_bucket" {
    bucket  = format("artifacts.%s.appspot.com", data.google_project.registry_project.project_id)
    role    = "roles/storage.objectViewer"
    member  = format("serviceAccount:%s", google_service_account.dataflow_sa.email)
}

resource "google_storage_bucket_iam_member" "composer_bucket" {
    bucket  = format("artifacts.%s.appspot.com", data.google_project.registry_project.project_id)
    role    = "roles/storage.objectViewer"
    member  = format("serviceAccount:%s", google_service_account.composer_node_sa.email)
}


resource "google_storage_bucket_iam_member" "cloudbuild_registry_objectAdmin" {
    bucket  = format("artifacts.%s.appspot.com", data.google_project.registry_project.project_id)
    role    = "roles/storage.objectAdmin"
    member  = format("serviceAccount:%d@cloudbuild.gserviceaccount.com", module.service_project.number)
}

resource "google_storage_bucket_iam_member" "cloudbuild_registry_bucket_getter" {
    bucket  = format("artifacts.%s.appspot.com", data.google_project.registry_project.project_id)
    role    = "roles/storage.legacyBucketReader"
    member  = format("serviceAccount:%d@cloudbuild.gserviceaccount.com", module.service_project.number)
}