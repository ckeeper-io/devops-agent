resource "google_artifact_registry_repository" "default" {
  location = "us-central1"
  repository_id = var.artifact_repo_name
  description = "Docker repository"
  format = "DOCKER"
}

resource "google_cloud_run_v2_service" "default" {
  name = var.cloud_run_name
  location = "us-central1"

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
    }
  }

  traffic {
    type = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_secret_manager_secret" "default" {
  secret_id  = var.secret_name
  replication {
    automatic {}
  }
}

resource "google_secret_manager_secret_version" "default" {
  secret = google_secret_manager_secret.default.id
  secret_data = "secret-data"
}
