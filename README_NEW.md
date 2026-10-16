# Hostel Room Allocation System

A containerized hostel room allocation application built with **Python 3.12, FastAPI, PostgreSQL, and Redis**, with automated testing and image publishing through CircleCI and deployment on Kubernetes using Minikube.

## 📌 Project Overview

The Hostel Room Allocation System assigns students to hostel rooms according to merit, seniority, room preferences, floor preferences, and mutually agreed roommate requests.

The application processes allocation requests in the background, tracks progress using Redis, stores persistent data in PostgreSQL, and provides REST API endpoints for accessing students, rooms, allocation runs, and results.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Application runtime |
| FastAPI | REST API framework |
| PostgreSQL | Persistent data storage |
| Redis | Allocation progress tracking |
| pytest | Automated testing |
| Docker | Application containerization |
| Docker Compose | Local multi-container setup |
| CircleCI | Continuous integration and delivery |
| Docker Hub | Container image registry |
| Kubernetes | Container orchestration |
| Minikube | Local Kubernetes environment |

## ✨ Features

- View student records and room availability.
- Update student room type and floor preferences.
- Process allocation requests asynchronously.
- Honour mutually agreed roommate requests.
- Allocate students according to merit and seniority.
- Track allocation progress and retrieve completed results.
- Report students who could not receive their preferred arrangements.
- Check application, PostgreSQL, and Redis health.
- Run the application in Docker and Kubernetes.

## 🏗️ Application Architecture

1. **FastAPI** receives requests and exposes the REST API.
2. **PostgreSQL** stores persistent application and allocation data.
3. **Redis** supports allocation progress tracking.
4. **Docker** packages the application and its runtime dependencies.
5. **CircleCI** automates the configured checks, tests, and image publishing workflow.
6. **Docker Hub** stores the published application image.
7. **Kubernetes on Minikube** runs the application alongside PostgreSQL and Redis.

## 🔗 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check application and service health |
| GET | `/students` | Retrieve student information |
| GET | `/rooms` | Retrieve room information |
| PUT | `/students/{sid}/preferences` | Update student preferences |
| POST | `/allocate` | Start an allocation run |
| GET | `/runs/{run_id}` | Check allocation progress and results |
| GET | `/allocation?run_id={run_id}` | Retrieve the saved allocation plan |

### API Documentation

When the application is running locally, access:

- **Swagger UI:** http://localhost:8080/docs
- **OpenAPI specification:** http://localhost:8080/openapi.json
- **Health check:** http://localhost:8080/health

## ⚙️ Prerequisites

For the Docker-based workflow, install:

- Git
- Docker Desktop with Docker Compose
- A Docker Hub account for publishing images

For Kubernetes deployment, also install:

- `kubectl`
- Minikube

Python 3.12 is required if you want to run the application directly outside its container.

## 🐳 Running Locally with Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/vedanthn0202-byte/hostel-allocation-python.git
cd hostel-allocation-python
```

### 2. Build and start the application

```bash
docker compose up --build
```

### 3. Check application health

Open another terminal and run:

```bash
curl http://localhost:8080/health
```

A healthy response should report `status` as `ok`, with both `postgres` and `redis` set to `true`.

### 4. Open the API documentation

Visit http://localhost:8080/docs in your browser.

Follow the repository's Docker Compose configuration for service startup, environment variables, and database migrations.

## 🧪 Testing

The project uses pytest for automated testing.

Run the complete test suite:

```bash
python -m pytest -v
```

Run allocation unit tests separately:

```bash
python -m pytest tests/test_allocate.py -v
```

Run API tests:

```bash
python -m pytest tests/test_api.py -v
```

The API tests require the dependencies and environment configured for the project's test setup.

## 🔄 CI/CD with CircleCI and Docker Hub

The project uses CircleCI to automate the configured build and validation workflow.

The pipeline covers the configured linting, unit testing, integration testing, secret scanning, Docker image building, and image publishing steps.

**Docker Hub image:** `vedanth02/hostel-allocation-python`

Example image tags include:

- `1.0`
- `latest`
- Commit-specific tags, when configured by the pipeline

**Docker Hub repository:** https://hub.docker.com/r/vedanth02/hostel-allocation-python

## ☸️ Kubernetes Deployment with Minikube

The project includes Kubernetes manifests in the `k8s/` directory.

The Kubernetes configuration runs the application with PostgreSQL and Redis. The application uses port `8080`, with startup, readiness, and liveness probes configured for the API.

### 1. Start Minikube

```bash
minikube start --driver=docker
```

### 2. Apply the Kubernetes manifests

```bash
kubectl apply -f ./k8s/
```

### 3. Check deployment status

```bash
kubectl get deployments
kubectl get services
kubectl get pods
```

### 4. Wait for the application deployment

```bash
kubectl rollout status deployment/hostel-allocation
```

### 5. Forward the application port

```bash
kubectl port-forward service/hostel-allocation 8080:8080
```

Keep the port-forward command running. Then open http://localhost:8080/docs or check application health:

```bash
curl http://localhost:8080/health
```

The Kubernetes application Service uses port `8080`; PostgreSQL uses port `5432`, and Redis uses port `6379` internally.

## 🧠 Allocation Rules

The allocator considers student merit, seniority, room preferences, floor preferences, and mutual roommate requests.

A one-way roommate request is not treated as mutual agreement. When preferences cannot all be satisfied, the allocation result reports relevant disappointments and reasons.

The allocation process also applies constraints to avoid leaving a student alone in a four-bed room.

## 📁 Repository Structure

```text
hostel-allocation-python/
├── app/                  # FastAPI application and allocation logic
├── tests/                # Unit and API tests
├── migrations/           # SQL database migrations
├── k8s/                  # Kubernetes manifests
├── .circleci/            # CircleCI pipeline configuration
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## ✅ Project Status

The application has been tested through its REST API, and the health endpoint has confirmed PostgreSQL and Redis connectivity.

The allocation workflow successfully placed all 20 students in a test run.

The CircleCI pipeline has passed, the Docker image has been published, and the Kubernetes application, database, and Redis deployments have been verified as ready in Minikube.

## 🚀 Future Improvements

- Add monitoring and centralized logging.
- Improve allocation reporting and visualization.
- Add authentication and role-based access control.
- Deploy to a managed Kubernetes cluster.
- Extend automated testing and coverage reporting.

## 👨‍💻 Author

Developed as a practical project to learn backend development, containerization, CI/CD automation, and Kubernetes deployment.
