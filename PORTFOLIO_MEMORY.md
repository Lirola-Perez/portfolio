# Portfolio Project Memory: 

## E2E Building Energy-Performance Machine Learning Project (PoC)

> Summary of the portfolio, from the beginning to the final first version. Its intention is to gather the process in detail describing the measures taken.

## First version memory: v1.0.0 - dated on `2026-11-25`

Initial public release of the Building Energy Simulation & Neural Network Surrogate Platform.

#### 1. Environment & Parametric Simulation Engine:

For this project, I used NixOS as my operating system. Declarative system configuration and atomic rollbacks make NixOS a natural local counterpart to Infrastructure as Code (IaC)—allowing dependencies, toolchains, and services to be modified cleanly without risking environment drift.

The first step in the repository was defining an isolated, reproducible development environment in `flake.nix`:

- **Pinned & Isolated Dependencies**: Instead of relying on host-level global packages, the flake pulls a pinned revision of nixpkgs (`nixos-unstable` locked via `flake.lock`) with `allowUnfree = true` for local tooling (such as VS Code).

- **Scientific, Web & ML Python Environment**: Python is not a program to be downloaded and ready to use (in NixOS reference system), such as others like `git` or `terraform`. For that reason, a dedicated Python 3.13 environment (`myPython`) bundles the data science and machine learning libraries (`tensorflow`, `pandas`, `numpy`, `scikit-learn`), backend stack (`sqlalchemy`, `supabase`), linting and testing (`ruff`, `pytest`) and web design support (`fastapi`,) overriding `mlxtend (doCheck = false)` to bypass upstream numerical test sensitivity during builds - raising numerical misreadings avoiding to build properly the environment -

- **Custom `eppy` Packaging & EnergyPlus Integration inside Python Environment**: Because `eppy` *(the Python scripting interface for EnergyPlus `.idf` models)* was unavailable in `nixpkgs`, the flake uses `buildPythonPackage` and hatchling to build `eppy 0.5.68` from source fetched via `fetchPypi` *(verified with its SHA-256 source hash)*, bridging the Python environment with the EnergyPlus simulation setup. Its runtime dependencies are declared in `propagatedBuildInputs` so they are available whenever `eppy` is used.

- **Unified DevOps Shell and Python environment load**: Entering the shell (with `nix develop` in `devShells.x86_64-linux.default`) provides `terraform`, `google-cloud-sdk`, `kubernetes`, `pandoc`, and `texliveMedium` alongside a `shellHook` that bootstraps a local `.venv` with `--system-site-packages` — giving both, the shell session (via `source .venv/bin/activate`) and the IDE (Integrated Development Environment, such as VS Code) access to the `myPython` environment.

Those above points are the reason why the two steps for setting the work environment are:

- Running flake environment: `nix develop` command
- Entering the Python environment: `source .venv/bin/activate`

#### 2. Microservices Architecture & Orchestration

This project has evolved naturally from a more or less initial monolithic structure to a native micro-service one. 

Microservice structure is the better fit for a scalable orchestrated cloud app. Ogirinally all parts of this project were designed as permanent running microservices, however as the `service_core`, `service_runner`, `service_postprocess` and training `neuronal_network` were called exclusively on the generation of the machine learning final model, there were no need to make them services and they changed as jobs (that means, they are called when new model is improved). That leaves only the web service as the only permanent running service in the project.

- **Containerized Services (`docker-compose.yaml`):** Decoupled the monolithic simulation script into dedicated, containerized microservices separated conveniently (SoC):
  - **CREATION-PARAMETRIZATION**: **`service_core`**: Manages IDF configurations with built object-oriented `.idf` parsing, parametric variations (`idf_class.py`, `idf_parametric.py`), and REST/manager workflows.
  - **SIMULATION RUNS**:**`service_runner`**: Executes EnergyPlus batch simulations on demand.
  - **DATA PREPARATION**:**`service_postprocess`**: Extracts, cleans, and aggregates raw simulation outputs into structured datasets (`grabber.py`).
  - **MACHINE LEARNING TRAINING**: **`neuronal_network`**: Prepares features, scales inputs/outputs, trains Keras/Ridge surrogate models, and runs evaluation benchmarks.
  - **PUBLIC WEB SERVICE**:**`service_ui`**: Serves a FastAPI web interface and HTML templates for interacting with models and predictions.

- **Migration from local to cloud**

  In the `docker_compose.yaml` it is possible to see the postgres service. That was used initially as a backend service before migration of the backend to a web-based backend (`supabase`). Additionally, in that file it is possible to see the mounted volume (`common_storage`) that services initially locally as data storage (for written or created data).The data required included multi-story and orientation-varied building models (`MultiStory.idf`, `LBuilding-G000` through `G270`) alongside weather datasets (`Madrid.epw`, `Potsdam.epw`).

- **Orchestration**
  The orchestration was managed by docker containerization. Each service is defined by its corresponding `Dockerfile` with its own particularities. The main considerations are:
  - Related to **SIMULATION ENGINE: `EnergyPlus`**:
    - **in `service_core`**: for using the python package `eppy` (related to EnergyPlus), the identification of the extension idfs and subsequent objects needs the file `Energy+.idd`. For this reason, that file should be downloaded from the repo.
    - **in `service_runner`**: as the principal task of this service is running simulations, the packed binaries of the program are downloaded and unpacked.
  - Related to **CONNECTIONS**:
    - There are two major needs for different services:
      - **Storage**: The definition of the environmental variable `BACKEND_STORAGE_CLOUD` in the Dockerfiles was defined as the migration from the local folder storage to cloud storage. This variable is the one used in code for switching between the `storage_client` types (local folder vs. `supabase` cloud service). The `storage_client` needs the url of the database and the password.
      >- *#Note: Google Cloud provides services for data administration (tables and storage capacity), however for this project `supabase` is used because it is free. The downside of this is the limited storage capacity of the free service*.
      - **database tables**: The client driver is set by `psycopg2` and `.connect(...)` with the postgres server locally or cloud (supabase). 
        - If it is **locally**, it connects (through `<LOCALHOST>:<PORT>` with credentials `<USER>` and `<PASSWORD>` to the running container (image built), 
        - if it is **cloud-based**, it connects with `supabase` already incorporated postgress service (using the credentials injected in the url: `<PASSWORD>@<POOLER_HOST>` and using TSL connection `sslmode=require`)
       Again the definition of `BACKEND_STORAGE_CLOUD` in the Dockerfiles plays a role in the creation, read, write and update of the project tables. Locally, the tables are recorded in a postgresql service. That services is built as image by the `docker_compose.yml` file and is called in the file `postgres_connection.py`. In the cloud version, the client providing the data administration is the `supabase` service, as well as the storage capacity in this case.

      | Variable | Example Value / Structure | Purpose & Role | 
      | ----- | ----- | ----- | 
      | `DATABASE_URL` | `postgresql://postgres.<project_ref>:<PASSWORD>@<POOLER_HOST>:5432/postgres?sslmode=require` | Primary DSN used by `psycopg2.connect()`. Overrides fallback logic to direct queries to Supabase. | 
      | `DATABASE_PASSWORD` | `YourSupabaseDbPassword` | Dedicated database password configured in Supabase (distinct from login/dashboard password). | 
      | `SUPABASE_URL` | `https://<project_ref>.supabase.co` | REST/Storage base API URL for bucket interactions. | 
      | `SUPABASE_KEY` | `eyJhbGciOi...` | Anon/Service key for object storage and API authentication. |

      - **Containers <IP-Adresses:Ports>**: Docker containerization, by default, sets the containers as private (127.0.0.1 or localhost), unless they are set explicitly public. So, there is no need to specify the IP-addresses and Ports in the services `service_core`, `service_runner` and `service_postprocess` (`Expose` in Dockerfile is just informative). Additionally, these services in this project, actually, do not need connection because they are totally independent. The link between them is the database and storage. These services connect to the client (whether `postgresql` or `supabase`) and retrieve the current state of the data triggering their processes if needed. The only services that need to define the ports are the `postgressql` (port 5432 only private IP address) when it was used locally and the `ui_service` because it needs to redirect the HTTP protocols public (locally and later public) to the right container appy. The `Dockerfile` from the `ui_service` opens publicly the container (IP address `0.0.0.0` and in the port `8080` that later will be use by `supabase`)
  - Related to **SECURITY**:
    This is a very important part of every project. Measures have been taken for avoiding any leakage of information. Concretely they are:
    - **Code**:
      - **Data preparation and analysis**: Although it sounds trivial, first security measures start by preserving the integrity of the original data
        - In pure python:
          - Treating tuples as security measure to preserve data that should not change.
          - That can be achieved making `.copy()` of data before starting to manipulate it. (`.deepcopy()` method ensures pure isolation)
        - With packages: `numpy`, `pandas`:
          - Normally, they "duplicate" the data when doing operations with it by default (unless in-place methods are used, such as `.add_()`, that are not used in this project)
        - With package: `tensorflow`:
          - This package treats the tensors as inmutable natively, so there is no risk of accidental edition (unless it is defined explicitly as `tf.variable` in customized neuronal networks)
    - **Containerization**:
      - **creation of `.env` file**: Within other variables, `.env` file contains information about the `postgresql` and `supabase` clients, passwords and URLs.
      - **Environmental variables references**: Once the sensible variables are set in the `.env` file, if some other file needs them they are referenced to them, never hardcoded. This is case, for example, in the file `docker_compose.yaml` loading the `.env` file and then using references.
      - **Dockerfile user**: All containers are initialized with user `app` instead of `root`. This measures limits the capacity of making any modification beyond the requires.
      - **Containers ports and addresses**: All containers are private (`127.0.0.1`) excpect the one needed to be exposed to public: `ui_service`.
    - **CI/CD process**:
      - **`.gitignore`**: the project was tracked by Git on GitHub in my private profile. `.gitignore` was set, first thing, to avoid pushing any sensible data (or unnecessary files). The file with the variables `.env` is included in the list.
      - **Pipeline**: as security measure a pipeline was set for checking the containers and building their images:
        - **GitHub secrets**: to avoid sensible information in the configuration of the building process, I have used the `secrets` feature in GitHub when triggering the `Actions`. So, I passed part of the environmental variables written in `.env` (URL for postgres database and `supabase` and corresponding passwords)
        >#Note: **`secrets.GITHUB_TOKEN`** is created automaticly at each workflow run, for that reason, it does not appear in the secrets vault in actions.
        >#Note: GitHub offers an extense feature measure to detect dependencies and sensible information exposure. That could, eventually, be added and completement the security good practices.
        - **Jobs: testing and pushing**: (`.github/workflows/ci.yaml`): 
          - Configured automated `pytest` test suites
          - `ruff` linting/formatting enforcement
          - multi-architecture container builds tagged by branch, commit SHA
          - SemVer releases pushed to GitHub Container Registry (`ghcr.io`).
    - **Cloud deployment: `terraform`**:
      - Considering the orchestration as the whole process till public production, final step in `terraform` contemplates also security measures. In this object I have opted to manage the secrets through variables (no vaults or third party admon). Three files are essential:
        - **`variables.tf` file**: This is the file for defining the variables used for terraforming. The sensitive ones are declair as a reference name, type of variable,and most importantly, setting `sensitive = true` and without default value. These declared sensitive variables will be called in `secrets.tf` file.
        - **`terraform.tfvars` file**: In this file all sensible environmental variables (related to infrastructure, clients, passwords ...) are explicitly written. THIS file must be excluded from CI/CD, so it should be **included in `.gitignore` (`*.tfvars`)**
        - **`secrets.tf` file**: Every sensible variable that should be kept private to public, should be managed by a `resource "google_secret_manager_secret"`. Then, assigning the variable (in `variable.tf`) to the secret and finally, granting the artifact access to the secret with `resource "google_secret_manager_secret_iam_member"`. this file set also the resource `ghcr_secret` that will grant access to the github password `PAT` (Personal Access Token) thought `ghcr_secret_version`. That is used for load the credentials to grant access to the artifacts atomatic created in repository `ghcr.io` (created by the github pipeline). 
        - **`main.tf` file**: those sensible environmental variables will be loaded as `value_source {secret_key_ref {...}}`.
      - **Containers in cloud**: Google Cloud injects explicitly bound environment variables and Secret Manager secrets (should be seen in `Secret Manager` in Google Cloud), that should be declared properly as secrets (`terraform`), into each Cloud Run container at startup (runtime). It is very similar to GitHub Action procedure, with the difference that these secrets declared in GitHub are injected in building,testing or deploying.
       
    | Scope | Location | Primary Purpose |
    | :--- | :--- | :--- |
    | **Local Container Runtime** | `.env` file | Read directly by `docker-compose.yml` during local runs. |
    | **Cloud Service Runtime** | Cloud Dashboard / Secret Manager | Injected directly into production containers/serverless functions. |
    | **CI/CD Pipeline** | GitHub Repository / Actions Secrets | Used by automated test runners, linter checks, and image build tasks. |

    ## Working in Progress ...