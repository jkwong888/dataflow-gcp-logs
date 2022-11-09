resource "google_service_account" "review_scheduler_sa" {
  project   = module.service_project.project_id
  account_id   = "reviews-scheduler"
  display_name = "Review scheduler Service Account"
}

resource "google_cloud_scheduler_job" "review_scheduler" {
  project   = module.service_project.project_id

  name        = "review-emitter-job"
  region      = var.region
  schedule    = "* * * * *"

  http_target {
    http_method = "POST"
    uri = google_cloudfunctions_function.reviewsgen.https_trigger_url
    body = base64encode("{}")

    oidc_token {
      service_account_email = google_service_account.review_scheduler_sa.email
    }
  }
}

