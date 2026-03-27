# Parking Management Hiring Assignment

This repository contains a short, intentionally broken full-stack assignment for backend and frontend developers. The domain is parking management. Candidates need to debug and fix realistic issues across Django ORM/schema usage, Go SQL queries, and Next.js API integration.

## Tech Stack

- Backend 1: Django + Django REST Framework
- Backend 2: Go (`database/sql` with PostgreSQL)
- Frontend: Next.js
- Database: PostgreSQL

## Repository Layout

```
/backend-django   (broken ORM + schema issues)
/backend-go       (incorrect SQL queries)
/frontend-nextjs  (UI with bugs / incomplete integration)
README.md
```

## Prerequisites

- Python 3.11+
- Go 1.22+
- Node.js 20+
- Docker + Docker Compose

## Setup Instructions

### 1) Start PostgreSQL

From repository root:

```bash
docker compose up -d
```

Database settings used by all services:

- DB name: `parking_db`
- User: `parking_user`
- Password: `parking_pass`
- Host: `localhost`
- Port: `5432`

### 2) Run Django API (`backend-django`)

```bash
cd backend-django
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata parking/fixtures/sample_data.json
python manage.py runserver 8000
```

### 3) Run Go API (`backend-go`)

In a new terminal:

```bash
cd backend-go
go mod tidy
go run main.go
```

The Go API runs on `http://localhost:8080`.

### 4) Run Next.js app (`frontend-nextjs`)

In a new terminal:

```bash
cd frontend-nextjs
npm install
npm run dev
```

The frontend runs on `http://localhost:3000`.

## Assignment Goal For Candidate

Fix the broken behavior across all three services while keeping the design simple and production-reasonable. Avoid over-engineering.

### What candidate should debug

Do not treat these as trick questions. These are realistic mistakes that happen in day-to-day development:

- Available slots endpoint returns incorrect results
- Booking flow allows inconsistent slot occupancy state
- Booking create/update behavior fails due to serializer configuration
- Go active-bookings report returns wrong or empty data due to SQL issues
- Frontend cannot reliably talk to backend services
- Frontend slot loading/refresh behavior is incomplete after booking

## API Overview

### Django (`http://localhost:8000`)

- `GET /api/lots/`
- `GET /api/lots/<id>/slots/available/`
- `GET /api/bookings/`
- `POST /api/bookings/`
- `PATCH /api/bookings/<id>/checkout/`

### Go (`http://localhost:8080`)

- `GET /active-bookings`
- `GET /occupancy`

## Sample Data Included

Fixture file: `backend-django/parking/fixtures/sample_data.json`

- 3 parking lots (`Downtown Lot`, `Mall Parking`, `Airport Lot`)
- 15 slots total (5 per lot), with mixed occupancy
- 4 vehicles with realistic number plates
- 3 bookings total
  - 2 active bookings (`end_time = null`)
  - 1 completed booking (`end_time` set)

## Suggested Timebox

60-90 minutes.

## Evaluation Criteria

- Correctness of fixes
- Ability to reason about ORM and relational data consistency
- Ability to reason about SQL joins and filter conditions
- Frontend-backend integration quality
- Code clarity and maintainability
- Minimal but useful validation/testing approach

## Optional Nice-to-Have (not required)

- Add a few focused tests for the fixed behaviors
- Add small UX improvements (loading/error states) without changing architecture
