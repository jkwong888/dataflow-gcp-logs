resource "google_storage_bucket_object" "archive" {
  name   = "samples/functions/random_reviews.zip"
  bucket = google_storage_bucket.bucket.name
  source = data.archive_file.functions_zip.output_path
}

data "archive_file" "functions_zip" {
    output_path = "/tmp/random_reviews.zip"
    type = "zip"
    source_dir = "${path.module}/random_function"
}

resource "google_service_account" "functions_sa" {
  project   = module.service_project.project_id
  account_id   = "reviews-sa"
  display_name = "Review function Service Account"
}

resource "google_cloudfunctions_function_iam_member" "scheduler_invoker" {
  project   = module.service_project.project_id
  region = var.region
  cloud_function = google_cloudfunctions_function.reviewsgen.name
  role = "roles/cloudfunctions.invoker"
  member = format("serviceAccount:%s", google_service_account.review_scheduler_sa.email)
}

resource "google_cloudfunctions_function" "reviewsgen" {
  project = module.service_project.project_id
  name          = "random_reviews_generator"
  description   = "random reviews generator"
  runtime       = "python39"
  region        = var.region

  service_account_email = google_service_account.functions_sa.email

  available_memory_mb          = 128
  source_archive_bucket        = google_storage_bucket.bucket.name
  source_archive_object        = google_storage_bucket_object.archive.name
  trigger_http                 = true
  https_trigger_security_level = "SECURE_ALWAYS"
  timeout                      = 60
  entry_point                  = "randomgen"
  environment_variables = {
    TOPIC_ID = google_pubsub_topic.reviews_topic.name
    PROJECT_ID = module.service_project.project_id
  }

  ingress_settings             = "ALLOW_ALL"
}