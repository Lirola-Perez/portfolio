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

  web_services = {
    "service-ui" = "ghcr.io/lirola-perez/portfolio/service_ui:${var.image_tag}"
  }

  batch_jobs = {
    "service-core"        = "ghcr.io/lirola-perez/portfolio/service_core:${var.image_tag}"
    "service-runner"      = "ghcr.io/lirola-perez/portfolio/service_runner:${var.image_tag}"
    "service-postprocess" = "ghcr.io/lirola-perez/portfolio/service_postprocess:${var.image_tag}"
    "neuronal-network"    = "ghcr.io/lirola-perez/portfolio/neuronal_network:${var.image_tag}"
  }
}

# Frontend microservice
resource "google_cloud_run_v2_service" "web_service" {
  for_each = local.web_services

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
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/cache/${each.value}"

      env {
        name = "SUPABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.url_supabase_secret.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "SUPABASE_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.pass_supabase_secret.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.url_database_secret.secret_id
            version = "latest"
          }
        }
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

# Backend worker jobs (no ports requirements)
resource "google_cloud_run_v2_job" "batch_job" {
  for_each = local.batch_jobs

  name     = each.key
  location = var.gcp_region

  depends_on = [google_artifact_registry_repository.cache]

  # template for job
  template {
    # template for tasks
    # jobs does not need scaling. One time job.
    template {
      containers {
        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/cache/${each.value}"

        env {
          name = "SUPABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.url_supabase_secret.secret_id
              version = "latest"
            }
          }
        }
        env {
          name = "SUPABASE_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.pass_supabase_secret.secret_id
              version = "latest"
            }
          }
        }

        env {
          name = "DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.url_database_secret.secret_id
              version = "latest"
            }
          }
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

}

# Make service publicly accessible as a portfolio showcase
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  for_each = local.web_services

  project  = google_cloud_run_v2_service.web_service[each.key].project
  location = google_cloud_run_v2_service.web_service[each.key].location
  name     = google_cloud_run_v2_service.web_service[each.key].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
