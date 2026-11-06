variable "gcp_project_id" {
  description = "Assignated name of the project in the Google Cloud Provider"
  type        = string
  default     = "project-344bc86d-021e-42d7-a72"
}

variable "gcp_region" {
  description = "Selected region for the Cloud Google Provider"
  type        = string
  default     = "europe-west1"
}

variable "supabase_url" {
  description = "General URL value for the SUPABASE - backend service"
  type        = string
  sensitive   = true
}

variable "supabase_service_role_key" {
  description = "Key value for connecting with the database SUPABASE"
  type        = string
  sensitive   = true
}

variable "github_pat" {
  description = "Personal Token for connecting with the GitHub repository"
  type        = string
  sensitive   = true
}

variable "database_url" {
  description = "Connection to the database SUPABASE - backend service"
  type        = string
  sensitive   = true
}
