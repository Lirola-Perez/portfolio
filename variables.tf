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

variable "storage_path" {
  description = "Container path to storage"
  type        = string
  default     = "https://kunmisvoxlxoymtxelth.storage.supabase.co/storage/v1/s3"
  #default     = "/app/storage"
}

variable "weather_path" {
  description = "Container path to weather files"
  type        = string
  default     = "weather"
}

variable "output_path" {
  description = "Container path to output files"
  type        = string
  default     = "output"
}

variable "idf_path" {
  description = "Container path to idf files"
  type        = string
  default     = "idf-files"
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


