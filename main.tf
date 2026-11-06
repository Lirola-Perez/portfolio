terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Fetch the project number dynamically
data "google_project" "project" {
  project_id = var.gcp_project_id
}

# Grant Cloud Run permission to read images from Artifact Registry
resource "google_project_iam_member" "cloud_run_artifact_registry" {
  project = var.gcp_project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:service-${data.google_project.project.number}@serverless-robot-prod.iam.gserviceaccount.com"
}


# the 5 microservices pointing to GHCR artifacts (GitHub)
locals {
  microservices = {
    "service-ui"          = "ghcr.io/lirola-perez/portfolio/service_ui:master"
    "service-core"        = "ghcr.io/lirola-perez/portfolio/service_core:master"
    "service-runner"      = "ghcr.io/lirola-perez/portfolio/service_runner:master"
    "service-postprocess" = "ghcr.io/lirola-perez/portfolio/service_postprocess:master"
    "neuronal-network"    = "ghcr.io/lirola-perez/portfolio/neuronal_network:master"
  }
}

resource "google_cloud_run_v2_service" "services" {
  for_each = local.microservices

  name     = each.key
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  depends_on = [
    google_artifact_registry_repository.cache
  ]

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 1 # Bot protection cap
    }

    containers {
      image = "europe-west1-docker.pkg.dev/${var.gcp_project_id}/cache/${each.value}"

      env {
        name  = "SUPABASE_URL"
        value = var.supabase_url
      }
      env {
        name  = "SUPABASE_KEY"
        value = var.supabase_service_role_key
      }

      env {
        name  = "DATABASE_URL"
        value = var.database_url
      }

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }
    }
  }
}

# Make services publicly accessible as a portfolio showcase
# resource "google_cloud_run_v2_service_iam_member" "public_access" {
#   for_each = local.microservices
#   location = google_cloud_run_v2_service.services[each.key].location
#   name     = google_cloud_run_v2_service.services[each.key].name
#   role     = "roles/run.invoker"
#   member   = "allUsers"
# }
