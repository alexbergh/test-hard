# Test-Hard Dashboard

Web-based dashboard for managing security scans and monitoring.

## Features

- **Host Management** — Add, edit, and monitor scan targets
- **Scan Execution** — Start and monitor security scans (Lynis, OpenSCAP)
- **Scheduled Scanning** — Configure automated scan schedules with cron expressions
- **Real-time Status** — Live updates on scan progress and host status
- **Authentication** — JWT-based authentication with role-based access control
- **Distributed Tracing** — OpenTelemetry integration with Grafana Tempo

## Quick Start

### Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Docker

```bash
# Start dashboard
docker compose up -d

# With tracing
docker compose -f docker-compose.yml -f ../docker-compose.tracing.yml up -d
```

## Architecture

```
dashboard/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # REST API endpoints
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── main.py    # Application entry
│   └── Dockerfile
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── store/     # Zustand state
│   │   └── lib/       # API client
│   └── Dockerfile
└── docker-compose.yml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Authenticate user |
| POST | `/api/v1/auth/register` | Register new user |
| GET | `/api/v1/hosts` | List all hosts |
| POST | `/api/v1/hosts` | Create host |
| POST | `/api/v1/hosts/sync-docker` | Sync from Docker |
| GET | `/api/v1/scans` | List scans |
| POST | `/api/v1/scans` | Start new scan |
| GET | `/api/v1/schedules` | List schedules |
| POST | `/api/v1/schedules` | Create schedule |

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | - | JWT secret key |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/dashboard.db` | Database URL |
| `PROMETHEUS_URL` | `http://localhost:9090` | Prometheus URL |
| `GRAFANA_URL` | `http://localhost:3000` | Grafana URL |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `TRACING_ENABLED` | `true` | Enable distributed tracing |

## Roles

- **viewer** — Read-only access
- **operator** — Can start scans and manage hosts
- **admin** — Full access including user management

## Ports

- **8000** — Backend API
- **3001** — Frontend (production)
- **5173** — Frontend (development)
