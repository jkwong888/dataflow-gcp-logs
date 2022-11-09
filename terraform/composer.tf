resource "google_service_account" "composer_node_sa" {
  provider = google-beta
  project   = module.service_project.project_id
  account_id   = "composer-node-sa"
  display_name = "Review scheduler Service Account"
}

resource "google_project_iam_member" "composer_worker" {
  provider = google-beta
  project   = module.service_project.project_id
  role = "roles/composer.worker"
  member = "serviceAccount:${google_service_account.composer_node_sa.email}"
}

resource "google_project_iam_member" "composer_dataflow_developer" {
  provider = google-beta
  project   = module.service_project.project_id
  role = "roles/dataflow.developer"
  member = "serviceAccount:${google_service_account.composer_node_sa.email}"
}

resource "google_service_account_iam_member" "composer_dataflow_sa_user" {
    service_account_id = google_service_account.dataflow_sa.id
    role = "roles/iam.serviceAccountUser"
    member  = "serviceAccount:${google_service_account.composer_node_sa.email}"
}

resource "google_project_iam_member" "composer_service_agent" {
  provider = google-beta
  project   = module.service_project.project_id
  role = "roles/composer.ServiceAgentV2Ext"
  member = "serviceAccount:service-${module.service_project.number}@cloudcomposer-accounts.iam.gserviceaccount.com"
}

resource "google_compute_subnetwork_iam_member" "composer_network_user" {
  provider = google-beta
  subnetwork = module.service_project.subnets[0].id
  role = "roles/compute.networkUser"
  member = "serviceAccount:service-${module.service_project.number}@cloudcomposer-accounts.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "composer_shared_vpc_agent" {
  project   = data.google_project.host_project.id
  role      = "roles/composer.sharedVpcAgent"
  member = "serviceAccount:service-${module.service_project.number}@cloudcomposer-accounts.iam.gserviceaccount.com"
}

resource "google_compute_subnetwork_iam_member" "gke_network_user" {
  subnetwork = module.service_project.subnets[0].id
  role = "roles/compute.networkUser"
  member = "serviceAccount:service-${module.service_project.number}@container-engine-robot.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "gke_host_service_agent" {
  project   = data.google_project.host_project.id
  role = "roles/container.hostServiceAgentUser"
  member = "serviceAccount:service-${module.service_project.number}@container-engine-robot.iam.gserviceaccount.com"
}

resource "google_composer_environment" "composer" {
  depends_on = [
    google_project_iam_member.composer_service_agent,
    google_project_iam_member.composer_worker,
    google_project_iam_member.gke_host_service_agent,
    google_project_iam_member.composer_shared_vpc_agent,
    google_compute_subnetwork_iam_member.gke_network_user,
    google_compute_subnetwork_iam_member.composer_network_user,
  ]

  provider = google-beta
  project   = module.service_project.project_id
  name   = "composer-env-tf-c2-${random_id.random_suffix.hex}"
  region = var.region
  config {

    software_config {
      image_version = "composer-2-airflow-2"
    }

    workloads_config {
      scheduler {
        cpu        = 0.5
        memory_gb  = 1.875
        storage_gb = 1
        count      = 1
      }
      web_server {
        cpu        = 0.5
        memory_gb  = 1.875
        storage_gb = 1
      }
      worker {
        cpu = 0.5
        memory_gb  = 1.875
        storage_gb = 1
        min_count  = 1
        max_count  = 3
      }


    }
    environment_size = "ENVIRONMENT_SIZE_SMALL"

    node_config {
      network    = data.google_compute_network.shared_vpc.id
      subnetwork = module.service_project.subnets[0].id
      service_account = google_service_account.composer_node_sa.name
    }
  }
}