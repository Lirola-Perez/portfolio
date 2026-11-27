# SECRET ADMINISTRATION: Database url ---------------------------------------
resource "google_secret_manager_secret" "url_database_secret" {
  secret_id = "url-database-secret"
  project   = var.gcp_project_id
  replication {
    auto {}
  }
}

# Store the token version securely from the sensitive variable
resource "google_secret_manager_secret_version" "url_database_secret_version" {
  secret      = google_secret_manager_secret.url_database_secret.id
  secret_data = var.database_url
}

# Grant Artifact Registry permission to read the secret
resource "google_secret_manager_secret_iam_member" "cloud_run_database_secret_access" {
  secret_id = google_secret_manager_secret.url_database_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# SECRET ADMINISTRATION: Supabase url ---------------------------------------
resource "google_secret_manager_secret" "url_supabase_secret" {
  secret_id = "url-supabase-secret"
  project   = var.gcp_project_id
  replication {
    auto {}
  }
}

# Store the token version securely from the sensitive variable
resource "google_secret_manager_secret_version" "url_supabase_secret_version" {
  secret      = google_secret_manager_secret.url_supabase_secret.id
  secret_data = var.supabase_url
}

# Grant Artifact Registry permission to read the secret
resource "google_secret_manager_secret_iam_member" "cloud_run_supabase_secret_access" {
  secret_id = google_secret_manager_secret.url_supabase_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# SECRET ADMINISTRATION: Supabase pass ---------------------------------------
resource "google_secret_manager_secret" "pass_supabase_secret" {
  secret_id = "pass-supabase-secret"
  project   = var.gcp_project_id
  replication {
    auto {}
  }
}

# Store the token version securely from the sensitive variable
resource "google_secret_manager_secret_version" "pass_supabase_secret_version" {
  secret      = google_secret_manager_secret.pass_supabase_secret.id
  secret_data = var.supabase_service_role_key
}

# Grant Artifact Registry permission to read the secret
resource "google_secret_manager_secret_iam_member" "cloud_run_pass_supabase_secret_access" {
  secret_id = google_secret_manager_secret.pass_supabase_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# SECRET ADMINISTRATION: GitHub credentials -------------------------------
# Create the Secret Manager secret container
resource "google_secret_manager_secret" "ghcr_secret" {
  secret_id = "ghcr-secret"
  project   = var.gcp_project_id
  replication {
    auto {}
  }
}

# Store the token version securely from the sensitive variable
resource "google_secret_manager_secret_version" "ghcr_secret_version" {
  secret      = google_secret_manager_secret.ghcr_secret.id
  secret_data = var.github_pat
}

# Grant Artifact Registry permission to read the secret
resource "google_secret_manager_secret_iam_member" "artifact_registry_secret_access" {
  secret_id = google_secret_manager_secret.ghcr_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-artifactregistry.iam.gserviceaccount.com"
}


# GITHUB ACCESS --------------------------------------------------------------
# Configure your Artifact Registry cache repository with upstream credentials
resource "google_artifact_registry_repository" "cache" {
  location      = "europe-west1"
  repository_id = "cache"
  format        = "DOCKER"
  mode          = "REMOTE_REPOSITORY"
  project       = var.gcp_project_id

  remote_repository_config {
    docker_repository {
      custom_repository {
        uri = "https://ghcr.io"
      }
    }
    upstream_credentials {
      username_password_credentials {
        username                = "lirola-perez"
        password_secret_version = google_secret_manager_secret_version.ghcr_secret_version.name
      }
    }
  }

  depends_on = [google_secret_manager_secret_iam_member.artifact_registry_secret_access]
}
