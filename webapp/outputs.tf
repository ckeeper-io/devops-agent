output "artifact_repo_id" {
  value = google_artifact_registry_repository.default.id
  description = "Artifact Registry repository ID"
}

output "cloud_run_url" {
  value = google_cloud_run_v2_service.default.uri
  description = "Cloud Run service URL"
}

output "secret_id" {
  value = google_secret_manager_secret.default.id
  description = "Secret Manager secret ID"
}
