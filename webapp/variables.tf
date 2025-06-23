variable "artifact_repo_name" {
  type = string
  default = "devops-agent-artifact"
  description = "Name of the Artifact Registry repository"
}

variable "cloud_run_name" {
  type = string
  default = "devops-agent-app"
  description = "Name of the Cloud Run service"
}

variable "secret_name" {
  type = string
  default = "devops-agent-secret"
  description = "Name of the Secret Manager secret"
}
