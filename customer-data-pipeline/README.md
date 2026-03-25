# Customer Data Pipeline

Containerized data pipeline using Flask, FastAPI, and PostgreSQL.

## Overview

This project runs 3 services with Docker Compose:

1. Mock Server (Flask, port 5000): serves customer JSON data with pagination.
2. Pipeline Service (FastAPI, port 8000): ingests customer data and exposes query APIs.
3. PostgreSQL (port 5432): stores ingested customer records.

Data flow:

```text
mock-server (JSON API) -> pipeline-service (ingestion + API) -> postgres (persistent storage)
```

## Project Structure

```text
customer-data-pipeline/
|- docker-compose.yml
|- README.md
|- mock-server/
|  |- app.py
|  |- Dockerfile
|  |- requirements.txt
|  `- data/customers.json
`- pipeline-service/
   |- app.py
   |- Dockerfile
   `- requirements.txt
```

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- curl or Postman for API testing

## Quick Start

From the customer-data-pipeline directory:

```bash
docker-compose up -d --build
docker-compose ps
```

Check health endpoints:

```bash
curl http://localhost:5000/api/health
curl http://localhost:8000/api/health
```

Stop services:

```bash
docker-compose down
```

Stop services and remove database volume:

```bash
docker-compose down -v
```

## End-to-End Test Flow

```bash
# 1) Verify mock data API
curl "http://localhost:5000/api/customers?page=1&limit=5"

# 2) Trigger ingestion into PostgreSQL
curl -X POST http://localhost:8000/api/ingest

# 3) Wait a few seconds, then validate stored records from pipeline API
curl "http://localhost:8000/api/customers?page=1&limit=5"

# 4) Fetch one customer
curl http://localhost:8000/api/customers/CUST001
```

## API Reference

### Mock Server (Flask)

Base URL: http://localhost:5000

- GET /api/health
- GET /api/customers?page=1&limit=10
- GET /api/customers/{customer_id}

Example:

```bash
curl "http://localhost:5000/api/customers?page=2&limit=10"
```

### Pipeline Service (FastAPI)

Base URL: http://localhost:8000

- GET /api/health
- POST /api/ingest
- GET /api/customers?page=1&limit=10
- GET /api/customers/{customer_id}

Examples:

```bash
curl -X POST http://localhost:8000/api/ingest
curl "http://localhost:8000/api/customers?page=1&limit=10"
```

## Environment Variables

Configured in docker-compose.yml.

PostgreSQL:

- POSTGRES_USER=postgres
- POSTGRES_PASSWORD=password
- POSTGRES_DB=customer_db

Pipeline service:

- DATABASE_URL=postgresql://postgres:password@postgres:5432/customer_db
- FLASK_URL=http://mock-server:5000

Mock server:

- FLASK_ENV=production

## Database Schema

The pipeline service creates the customers table automatically on startup.

```sql
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    date_of_birth VARCHAR(20),
    account_balance NUMERIC(15, 2),
    created_at TIMESTAMP
);
```

## Troubleshooting

View all logs:

```bash
docker-compose logs -f
```

View one service log:

```bash
docker-compose logs mock-server
docker-compose logs pipeline-service
docker-compose logs postgres
```

Check data in PostgreSQL:

```bash
docker-compose exec postgres psql -U postgres -d customer_db -c "SELECT COUNT(*) FROM customers;"
```

If ingestion returns success but data is not visible immediately, wait a few seconds and call:

```bash
curl "http://localhost:8000/api/customers?page=1&limit=10"
```

## Notes

- This repository includes sample customer data under mock-server/data/customers.json.
- The ingestion endpoint runs in the background and returns immediately.

## License

Educational project.
