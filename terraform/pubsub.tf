resource "google_pubsub_topic" "reviews_topic" {
  project   = module.service_project.project_id
  name = "jkwng-reviews-topic-${random_id.random_suffix.hex}"

  message_retention_duration = "86400s"
}

resource "google_pubsub_subscription" "reviews_subscription" {
  project   = module.service_project.project_id
  name = "jkwng-dataflow-reviews-subscription-${random_id.random_suffix.hex}"

  topic = google_pubsub_topic.reviews_topic.id
}

resource "google_pubsub_subscription_iam_member" "reviews_dataflow_pull" {
  project   = module.service_project.project_id
  subscription = google_pubsub_subscription.reviews_subscription.id
  role = "roles/pubsub.subscriber"
  member = format("serviceAccount:%s",google_service_account.dataflow_sa.email)
}

resource "google_pubsub_topic_iam_member" "function_reviews_publish" {
  project   = module.service_project.project_id
  topic = google_pubsub_topic.reviews_topic.id
  role = "roles/pubsub.publisher"
  member = format("serviceAccount:%s",google_service_account.functions_sa.email)
}

/*
resource "google_pubsub_topic_iam_member" "workflows_reviews_publish" {
  project   = module.service_project.project_id
  topic     = google_pubsub_topic.reviews_topic.id
  role      = "roles/pubsub.publisher"
  member    = format("serviceAccount:%s",google_service_account.workflows_sa.email)
}


resource "google_pubsub_topic" "weather_topic" {
  project   = module.service_project.project_id
  name = "jkwng-weather-${random_id.random_suffix.hex}"

  message_retention_duration = "86400s"

}

resource "google_pubsub_subscription" "weather_subscription" {
  project   = module.service_project.project_id
  name = "jkwng-weather-sub-${random_id.random_suffix.hex}"

  topic = google_pubsub_topic.weather_topic.id

}

resource "google_pubsub_topic_iam_member" "workflows_publish" {
  project   = module.service_project.project_id
  topic = google_pubsub_topic.weather_topic.id
  role = "roles/pubsub.publisher"
  member = format("serviceAccount:%s",google_service_account.workflows_sa.email)

}

resource "google_pubsub_subscription_iam_member" "dataflow_pull_weather" {
  project   = module.service_project.project_id
  subscription = google_pubsub_subscription.weather_subscription.id
  role = "roles/pubsub.subscriber"
  member = format("serviceAccount:%s",google_service_account.dataflow_sa.email)

}
*/