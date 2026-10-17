# Hostel Room Allocation System

A containerized hostel room allocation system built with **Python 3.12, FastAPI, PostgreSQL, and Redis**, featuring automated testing, CI/CD with CircleCI, Docker Hub image publishing, and Kubernetes deployment using Minikube.

## 📌 Project Overview

The Hostel Room Allocation System automates the allocation of hostel rooms to students based on academic merit, seniority, room preferences, floor preferences, and mutually agreed roommate requests.

The application provides a REST API for managing students, viewing rooms, updating preferences, initiating allocation runs, tracking execution progress, and retrieving allocation results.

PostgreSQL stores persistent application data, while Redis tracks allocation progress and supports temporary run-state storage. Docker packages the application and its dependencies, CircleCI automates the build and validation workflow, and Kubernetes manages the application across separate QA, Stage, and Production environments.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Application runtime |
| FastAPI | REST API development |
| PostgreSQL 16 | Persistent database |
| Redis 7 | Allocation progress and temporary run-state tracking |
| pytest | Automated unit and integration testing |
| Ruff | Python linting and code quality |
| Docker | Application containerization |
| Docker Compose | Local multi-container orchestration |
| CircleCI | Continuous integration and delivery |
| Docker Hub | Container image registry |
| Kubernetes | Deployment and orchestration |
| Minikube | Local Kubernetes cluster |

## ✨ Features

- Retrieve student records and room information.
- Update student room-type and floor preferences.
- Process allocation requests asynchronously.
- Honour mutually agreed roommate requests.
- Apply deterministic allocation rules for consistent results.
- Rank students using merit, year of study, and student ID as tie-breakers.
- Track allocation progress and retrieve completed allocation results.
- Explain allocation disappointments, including when a student is `outranked` by another student.
- Persist application data in PostgreSQL.
- Use Redis for temporary allocation-run state and progress tracking.
- Run health checks for the API, PostgreSQL, and Redis.
- Containerize the application with Docker.
- Automate validation and image publishing through CircleCI.
- Deploy isolated application environments using Kubernetes.

## 🏗️ Application Architecture

The application follows a containerized, service-oriented architecture.

1. **FastAPI application:** Receives HTTP requests, validates inputs, executes allocation workflows, and returns JSON responses.
2. **PostgreSQL:** Stores students, rooms, preferences, and persistent allocation data.
3. **Redis:** Maintains temporary allocation-run state and supports progress tracking with a configurable time-to-live.
4. **Database migrations:** Initialize and seed the database using ordered SQL migration files.
5. **Docker:** Packages the Python application and its runtime dependencies into a reproducible container image.
6. **Docker Compose:** Coordinates the application, database, Redis, and migration process for local execution.
7. **CircleCI:** Automates the configured code-quality checks, tests, and container image publishing workflow.
8. **Docker Hub:** Stores the published application image for use by deployment environments.
9. **Kubernetes and Minikube:** Orchestrate the application, PostgreSQL, and Redis across QA, Stage, and Production namespaces.

### Architecture flow

```text
                  Client / Swagger UI
                          |
                          v
                     FastAPI API
                     /         \
                    v           v
               PostgreSQL     Redis
                    |
                    v
           Persistent allocation data

        Source Code Repository
                  |
                  v
               CircleCI
                  |
          Build and validate
                  |
                  v
              Docker Hub
                  |
                  v
          Kubernetes / Minikube
             /      |      \
            v       v       v
           QA     Stage   Production
```

## 🔗 REST API Endpoints

The application exposes the following endpoints.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks application, PostgreSQL, and Redis health |
| GET | `/students` | Retrieves student information |
| GET | `/rooms` | Retrieves room information |
| PUT | `/students/{sid}/preferences` | Updates an individual student's preferences |
| POST | `/allocate` | Starts a new allocation run |
| GET | `/runs/{run_id}` | Retrieves allocation-run status and results |
| GET | `/allocation?run_id={run_id}` | Retrieves the allocation plan for a run |

### API documentation

When the application is accessible on local port 8080:

- **Swagger UI:** http://localhost:8080/docs
- **OpenAPI specification:** http://localhost:8080/openapi.json
- **Health endpoint:** http://localhost:8080/health

Swagger UI allows API endpoints to be explored and tested interactively.

## 🧠 Allocation Algorithm

The allocation engine is implemented in `app/allocate.py`, separating the core allocation logic from the API and infrastructure layers.

### 1. Student grouping

Students requesting to stay together are grouped only when their roommate requests are mutual. A one-way request is not sufficient to form a roommate group.

The grouping process respects room capacity, including the four-bed room constraint, and avoids placing a student alone in a four-bed room.

### 2. Ranking and deterministic allocation

Students are evaluated using a consistent ranking order:

1. Higher merit ranks first.
2. Year of study is used as the next tie-breaker.
3. Student ID provides a final deterministic tie-breaker.

The allocator applies these rules consistently so that equivalent inputs produce reproducible allocation results.

### 3. Room and floor preferences

The allocator considers students' preferred room types and floors while respecting room capacity and grouping constraints. When all preferences cannot be satisfied, the result records the relevant allocation outcome and disappointment reason.

### 4. Allocation explanations

The system provides information about students whose preferences could not be fulfilled.

For example, a student may be marked as `outranked` when a higher-ranked student receives a limited room or placement opportunity first. The `blocked_by` information helps explain which competing allocation prevented a preferred placement.

### 5. Allocation progress

Allocation requests create a run that can be tracked using its run ID. Redis supports temporary run-state storage and progress reporting, with a configured run TTL of 3600 seconds. Persistent application and allocation data is maintained in PostgreSQL.

## 🐳 Running Locally with Docker Compose

### Prerequisites

Install:

- Git
- Docker Desktop with Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/vedanthn0202-byte/hostel-allocation-python.git
cd hostel-allocation-python
```

### 2. Build and start the services

```bash
docker compose up --build -d
```

Docker Compose starts the application infrastructure, including PostgreSQL and Redis, and runs the database migration process according to the Compose configuration.

### 3. Check the running containers

```bash
docker compose ps
```

### 4. Verify application health

```bash
curl http://localhost:8080/health
```

A healthy response reports `status` as `ok`, with `postgres` and `redis` set to `true`.

### 5. Open Swagger UI

Visit http://localhost:8080/docs to explore and test the REST API.

### 6. Stop the local services

```bash
docker compose down
```

This stops and removes the Compose containers and network. Persistent database storage is managed separately by the Compose configuration.

## 🧪 Automated Testing

The project uses pytest to validate the allocation algorithm, API behaviour, and allocation workflow.

### Run all tests

```bash
python -m pytest -v
```

### Run allocation unit tests

```bash
python -m pytest tests/test_allocate.py -v
```

### Run API tests

```bash
python -m pytest tests/test_api.py -v
```

### Run allocation workflow tests

```bash
python -m pytest tests/test_allocation_flow.py -v
```

The test suite covers allocation constraints, mutual roommate requests, deterministic results, ranking behaviour, allocation explanations, and API workflows.

Ruff is used for Python code-quality checks, and the CI workflow runs automated validation before publishing container images.

## 🔄 CI/CD with CircleCI and Docker Hub

The project integrates CircleCI with the source repository to automate the container build and publishing workflow.

The configured pipeline includes code-quality checks, automated tests, service and migration validation, and Docker image building and publishing.

### CI/CD workflow

1. A code change is pushed to a configured Git branch.
2. CircleCI checks out the repository.
3. Python code-quality checks and automated tests run.
4. Required application services and database migrations are validated by the pipeline.
5. Docker builds the application image.
6. The image is published to Docker Hub when the publishing conditions are met.

### Docker Hub image

**Repository:** `vedanth02/hostel-allocation-python`

Docker Hub repository: https://hub.docker.com/r/vedanth02/hostel-allocation-python

The image is published for use in the Kubernetes deployment workflow. Environment-specific tags include:

- `latest`
- `qa`
- `stage`
- `prod`

The tags identify images intended for the respective deployment environments.

## ☸️ Kubernetes Deployment with Minikube

The project uses Kubernetes to orchestrate the application and its supporting services locally through Minikube.

The deployment is organized into three namespaces:

| Namespace | Purpose |
|---|---|
| `qa` | Quality assurance and functional validation |
| `stage` | Pre-production validation |
| `prod` | Production-style deployment |

Each environment contains the Hostel Allocation application, PostgreSQL, and Redis. PostgreSQL storage is managed through persistent volume claims, and database migrations initialize the application schema.

### 1. Start Minikube

```powershell
minikube start --driver=docker
```

### 2. Verify the cluster

```powershell
kubectl get nodes
```

The Minikube node should report `Ready`.

### 3. Inspect environment deployments

```powershell
kubectl get deployments,pods -n qa
kubectl get deployments,pods -n stage
kubectl get deployments,pods -n prod
```

### 4. Check application services

```powershell
kubectl get services -n qa
kubectl get services -n stage
kubectl get services -n prod
```

The application Service exposes port `8080` internally. PostgreSQL and Redis use ports `5432` and `6379`, respectively.

### 5. Access the QA application

Run the following command in a dedicated terminal:

```powershell
kubectl port-forward service/hostel-allocation 18081:8080 -n qa
```

Keep that terminal open. In another terminal, run:

```powershell
Invoke-RestMethod http://localhost:18081/health
```

Open Swagger UI at http://localhost:18081/docs.

### 6. Access the Stage application

Start the Stage port-forward:

```powershell
kubectl port-forward service/hostel-allocation 18082:8080 -n stage
```

Health check:

```powershell
Invoke-RestMethod http://localhost:18082/health
```

Swagger UI: http://localhost:18082/docs

### 7. Access the Production application

Start the Production port-forward:

```powershell
kubectl port-forward service/hostel-allocation 18083:8080 -n prod
```

Health check:

```powershell
Invoke-RestMethod http://localhost:18083/health
```

Swagger UI: http://localhost:18083/docs

Each port-forward runs in its own terminal and remains active until stopped with `Ctrl+C`.

### 8. Check application rollout status

```powershell
kubectl rollout status deployment/hostel-allocation -n qa
kubectl rollout status deployment/hostel-allocation -n stage
kubectl rollout status deployment/hostel-allocation -n prod
```

These commands verify that the application deployments have completed their rollout.

## 🗄️ Database and Configuration

The application uses environment variables to connect to its supporting services:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection URL |
| `REDIS_URL` | Redis connection URL |

Database schema and seed data are managed through SQL migration files in `migrations/`. The migration process runs before the application starts, according to the deployment configuration.

Kubernetes Secrets provide database configuration where referenced by the manifests, while ConfigMaps can be used to provide non-sensitive configuration and migration files.

## 📁 Repository Structure

```text
hostel-allocation-python/
├── app/
│   ├── main.py                 # FastAPI routes and application setup
│   ├── allocate.py             # Core allocation algorithm
│   ├── db.py                   # PostgreSQL integration
│   └── cache.py                # Redis integration
├── tests/
│   ├── test_allocate.py        # Allocation unit tests
│   ├── test_api.py             # API tests
│   └── test_allocation_flow.py # Allocation workflow tests
├── migrations/                 # SQL schema and seed migrations
├── k8s/                        # Kubernetes deployment manifests
├── .circleci/
│   └── config.yml              # CircleCI pipeline configuration
├── Dockerfile                  # Application container image
├── docker-compose.yml          # Local service orchestration
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

## ✅ Project Status

The Hostel Room Allocation System has been implemented and exercised through its API, containerized runtime, CI/CD pipeline, and Kubernetes deployment.

- The application exposes the documented REST API endpoints.
- PostgreSQL and Redis connectivity is verified through the health endpoint.
- The allocation workflow processes student records and returns allocation results.
- The allocation algorithm applies mutual roommate requests, deterministic ranking, and room constraints.
- Automated tests validate the core allocation logic and API workflows.
- CircleCI has completed successful pipeline runs and published the Docker image.
- QA, Stage, and Production Kubernetes environments have been deployed in Minikube.
- Health checks have returned successful responses from all three environments, with PostgreSQL and Redis connectivity confirmed.

## 🚀 Future Improvements

- Introduce centralized application logging and monitoring dashboards.
- Add authentication and role-based access control.
- Improve allocation-result visualization and reporting.
- Extend automated coverage and performance testing.
- Deploy to a managed cloud Kubernetes platform.
- Add alerts and operational metrics for application and database health.

## 👨‍💻 Author

Developed as a practical project demonstrating backend API development, database integration, containerization, automated testing, CI/CD automation, and Kubernetes deployment.
## Presentation Verification
- Docker Compose: docker compose ps
- Application health: http://localhost:8080/health
- Kubernetes pods: kubectl get pods -A
