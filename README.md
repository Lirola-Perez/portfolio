## E2E Building Energy-Performance Machine Learning Project (PoC)

### 1. Overview & Definition

An end-to-end (E2E) MLOps Proof of Concept (PoC) designed for predicting building energy-performance parameters. While lightweight by design, this project is architected with production-grade separation of concerns (SoC), ensuring seamless scalability, reproducibility, and robust infrastructure management.

### 2. Repository Structure & Microservices

The project follows a clean monorepo layout, segregating application logic, user interfaces, testing, and infrastructure configuration:

```Plaintext
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
└── flake.nix
```

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