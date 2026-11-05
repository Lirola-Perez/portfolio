variable "gcp_project_id" {
  type    = string
  default = "project-344bc86d-021e-42d7-a72"
}

variable "gcp_region" {
  type    = string
  default = "europe-west1"
}

variable "supabase_url" {
  type      = string
  sensitive = true
}

variable "supabase_service_role_key" {
  type      = string
  sensitive = true
}

variable "github_pat" {
  type      = string
  sensitive = true
}
