# E2E Building Energy-Performance Machine Learning Project (PoC)

## Production MLOps Simulation & Database Pipeline

[![CI Pipeline](https://github.com/Lirola-Perez/portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/Lirola-Perez/portfolio/actions/workflows/ci.yaml)

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)

[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust, production-ready MLOps monorepo designed to orchestrate automated simulation runs, manage stateful PostgreSQL transactions, and execute rigorous background tracking—all backed by a fully automated GitHub Actions CI pipeline.

## Tech Stack

- **Locally Developed**: Nixos with `flake.nix` environment (`Linux` and `Nix`)

- **Language:** `Python 3.13`

- **Database:** `PostgreSQL` (psycopg2 driver with explicit transactional safety)

- **Machine Learning** / Simulation: `TensorFlow` / `Keras` model loading & structured file parsing
- **Simulation Engine**: `EnergyPlus`

- **Code Quality & Linter:** Ruff (enforcing modern standards like SIM117 multi-context rules and strict exception patterns)

- **CI/CD:** `GitHub Actions` (automated pip caching, test execution, and static checks)

---

## Architecture & System Design

This project follows a clean **separation of concerns** pattern, isolating infrastructure plumbing from business logic:

1. **Transactional Database Management (`get_db_connection`)**: A custom context manager handles PostgreSQL connections, automatic transaction commits, rollbacks on error, and guaranteed resource cleanup.
2. **Resilient Background Runner (`runner.py`)**: Executes model and simulation workloads (e.g., EnergyPlus/TensorFlow pipelines) with explicit, self-documenting exception handling (`psycopg2.OperationalError`, `psycopg2.ProgrammingError`, `zipfile.BadZipFile`) to ensure worker states transition cleanly to `"Failed"` rather than hanging indefinitely.
3. **Automated CI/CD (`ci.yml`)**: Continuous integration workflow running on **Python 3.13**, enforcing strict static code analysis via **Ruff**, and executing test suites with `pytest` and `httpx`.

---

## Repository Structure

```text
Porfolio/
├── .github/
│   └── workflows/
│       └── ci.yml              # Automated CI pipeline & testing
├── project/
│   ├── service_ui/             # FastAPI user interface & frontend rendering
|   ├── service_postprocess/    # Read and preparation of the data from the runner
|   ├── service_runner/         # Runner engine EPlus
|   ├── neuronal_network/       # Machine learning inference & modeling service
│   ├── db_init/                # Postgres database initialization
│   ├── common_storage/         # Shared volume data root (/common_storage)
│   ├── tests/                  # Integration and unit test suite
│   ├── docker-compose.yaml     # Local multi-container orchestration
│   └── .env                    # (HIDDEN) Environment variable configurations
├── .gitignore
├── flake.nix
└── README.md
```

### 1. Overview & Definition

An end-to-end (E2E) MLOps Proof of Concept (PoC) designed for predicting building energy-performance parameters. While lightweight by design, this project is architected with production-grade separation of concerns (SoC), ensuring seamless scalability, reproducibility, and robust infrastructure management.

### 2. Repository Structure & Microservices

The project follows a clean monorepo layout, segregating application logic, user interfaces, testing, and infrastructure configuration:


### 3. Inter-Service Communication & Storage

- **Private Container Network:** All microservices run on an isolated internal Docker network. Services communicate strictly via internal DNS names.

- **Shared Storage Volume (`/common_storage`)**: Rather than traditional database heavy-coupling for inter-service file sharing, a dedicated shared storage volume acts as a linked stateful exchange point (e.g., passing generated artifacts like column_list.json from upstream data preparation pipelines to inference services).

- **Database & Health Monitoring**: Includes a secured PostgreSQL instance (`postgres_db`) with active health checks to ensure dependent services only boot up when the data layer is fully responsive.

### 4. Security & Network Isolation

- **Local Binding:** All database and internal microservice ports are strictly bound to loopback `127.0.0.1` or kept entirely unexposed on external host interfaces.

- **Controlled Access:** The UI Service is the sole entry point explicitly configured for external access, serving as the secure gateway to the underlying application stack.

### 5. Testing & Continuous Integration (CI)

To guarantee application reliability and code health, the repository features an automated GitHub Actions CI pipeline (`.github/workflows/ci.yml`).

**Key Pipeline Features:**

- **Absolute Path Resolution:** Configures dynamic `PYTHONPATH` to handle deep monorepo directory structures.

- **Environment Parity**: Enforces strict package installations using `python -m pip`.

- **Upstream Artifact Mocking:** Dynamically generates mock data structures (such as column_list.json) during CI runs to allow clean import-time evaluation of FastAPI endpoints.

- **Automated Linting & Pytest:** Executes code style checks (`Ruff`) and runs comprehensive test suites (`pytest + httpx`) on every push and pull request.

### 6. Scalability & Cloud-Native Readiness

- **Containerization:** Fully containerized using Docker Compose for local parity with production.

- **Infrastructure as Code (IaC)**: Prepared for cloud provisioning using `Terraform`.

- **Orchestration**: Container definitions and deployment patterns are structured for seamless migration to Kubernetes clusters.