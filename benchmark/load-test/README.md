# Benchmark Load Tests: Python Web Frameworks Comparison

This directory contains load testing benchmarks comparing multiple Python web frameworks with PostgreSQL operations.

## Overview

All implementations provide identical REST APIs with the following endpoints:
- `GET /` - Health check
- `GET /items` - List all items (with pagination)
- `GET /items/{id}` - Get a specific item
- `POST /items` - Create a new item
- `PUT /items/{id}` - Update an existing item
- `POST /upsert` - Insert or update based on item name

## Frameworks Tested

- **Rupy** - High-performance framework powered by Rust (port 8001)
- **FastAPI** - Modern async Python framework (port 8002)
- **Django REST Framework** - Full-featured framework (port 8003)
- **Flask-RESTful** - Lightweight RESTful extension for Flask (port 8004)
- **Robyn** - Fast async framework built with Rust (port 8005)
- **mrhttp** - High-performance C extension framework (port 8006)

## Directory Structure

```
benchmark/load-test/
├── rupy-pg-upsert-select/
│   ├── app.py              # Rupy API implementation
│   ├── Dockerfile          # Docker image for Rupy
│   └── requirements.txt    # Python dependencies
├── fastapi-pg-upsert-select/
│   ├── app.py              # FastAPI implementation
│   ├── Dockerfile          # Docker image for FastAPI
│   └── requirements.txt    # Python dependencies
├── django-pg-upsert-select/
│   ├── app.py              # Django REST implementation
│   ├── Dockerfile          # Docker image for Django
│   └── requirements.txt    # Python dependencies
├── flask-pg-upsert-select/
│   ├── app.py              # Flask-RESTful implementation
│   ├── Dockerfile          # Docker image for Flask
│   └── requirements.txt    # Python dependencies
├── robyn-pg-upsert-select/
│   ├── app.py              # Robyn implementation
│   ├── Dockerfile          # Docker image for Robyn
│   └── requirements.txt    # Python dependencies
├── mrhttp-pg-upsert-select/
│   ├── app.py              # mrhttp implementation
│   ├── Dockerfile          # Docker image for mrhttp
│   └── requirements.txt    # Python dependencies
├── docker-compose.yml      # Orchestrates all services
├── locustfile.py          # Locust load testing script
├── test_apis.py           # API compatibility test script
├── benchmark.sh           # Helper script for running benchmarks
└── README.md              # This file
```

## Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local testing)
- Locust (for load testing)

## Quick Start

### Using the Helper Script (Recommended)

The easiest way to run the benchmarks is using the provided helper script:

```bash
cd benchmark/load-test

# Start all services
./benchmark.sh start

# Test all APIs
./benchmark.sh test

# Run load tests on all frameworks
./benchmark.sh bench-all

# Run load test on specific framework
./benchmark.sh bench-rupy
./benchmark.sh bench-fastapi
./benchmark.sh bench-django
./benchmark.sh bench-flask
./benchmark.sh bench-robyn
./benchmark.sh bench-mrhttp

# View logs
./benchmark.sh logs

# Stop services
./benchmark.sh stop

# See all options
./benchmark.sh help
```

### Manual Setup

### 1. Build and Start Services

```bash
cd benchmark/load-test
docker-compose up --build
```

This will start:
- PostgreSQL database (port 5432)
- Rupy API (port 8001)
- FastAPI (port 8002)
- Django REST Framework (port 8003)
- Flask-RESTful (port 8004)
- Robyn (port 8005)
- mrhttp (port 8006)
- Locust master (port 8089)

### 2. Verify APIs are Running

Test any framework:
```bash
curl http://localhost:8001/  # Rupy
curl http://localhost:8002/  # FastAPI
curl http://localhost:8003/  # Django
curl http://localhost:8004/  # Flask
curl http://localhost:8005/  # Robyn
curl http://localhost:8006/  # mrhttp
```

### 3. Run Load Tests with Locust

#### Option A: Using the Web UI

1. Open your browser to http://localhost:8089
2. Enter the number of users and spawn rate
3. Enter the host URL (http://rupy-api:8000 or http://fastapi-api:8000)
4. Click "Start swarming"

#### Option B: Using the Command Line

Test Rupy API:
```bash
locust -f locustfile.py --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 60s \
  --host http://localhost:8001 \
  --html rupy-report.html
```

Test FastAPI:
```bash
locust -f locustfile.py --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 60s \
  --host http://localhost:8002 \
  --html fastapi-report.html
```

### 4. Test Individual Endpoints

Create an item:
```bash
curl -X POST http://localhost:8001/items \
  -H "Content-Type: application/json" \
  -d '{"name": "test-item", "value": "test-value"}'
```

Get an item:
```bash
curl http://localhost:8001/items/1
```

Update an item:
```bash
curl -X PUT http://localhost:8001/items/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "updated-item", "value": "updated-value"}'
```

Upsert an item:
```bash
curl -X POST http://localhost:8001/upsert \
  -H "Content-Type: application/json" \
  -d '{"name": "upsert-item", "value": "upsert-value"}'
```

List items:
```bash
curl http://localhost:8001/items
```

## Load Test Configuration

The Locust script simulates realistic user behavior with the following distribution:
- 50% - Read operations (GET /items/{id})
- 30% - Create operations (POST /items)
- 20% - Update operations (PUT /items/{id})
- 20% - Upsert operations (POST /upsert)
- 10% - List operations (GET /items)
- 10% - Health checks (GET /)

You can modify these distributions in `locustfile.py` by adjusting the `@task` weights.

## Benchmarking Guidelines

### Recommended Test Scenarios

1. **Low Load Test**
   - Users: 10
   - Spawn rate: 1/sec
   - Duration: 60 seconds

2. **Medium Load Test**
   - Users: 100
   - Spawn rate: 10/sec
   - Duration: 120 seconds

3. **High Load Test**
   - Users: 500
   - Spawn rate: 50/sec
   - Duration: 300 seconds

4. **Stress Test**
   - Users: 1000+
   - Spawn rate: 100/sec
   - Duration: 600 seconds

### Metrics to Compare

- **Requests per second (RPS)**: Total throughput
- **Response time**: 50th, 95th, and 99th percentiles
- **Error rate**: Percentage of failed requests
- **Resource usage**: CPU and memory consumption (use `docker stats`)

### Running Performance Comparison

```bash
# Test all frameworks with 500 users for 5 minutes
./benchmark.sh bench-all

# Or test individually
locust -f locustfile.py --headless \
  --users 500 --spawn-rate 50 --run-time 300s \
  --host http://localhost:8001 \
  --html rupy-500users.html \
  --csv rupy-500users

locust -f locustfile.py --headless \
  --users 500 --spawn-rate 50 --run-time 300s \
  --host http://localhost:8002 \
  --html fastapi-500users.html \
  --csv fastapi-500users

# Repeat for other frameworks on ports 8003-8006
```

## Monitoring

### View Container Stats

```bash
docker stats
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific services
docker-compose logs -f rupy-api
docker-compose logs -f fastapi-api
docker-compose logs -f django-api
docker-compose logs -f flask-api
docker-compose logs -f robyn-api
docker-compose logs -f mrhttp-api
docker-compose logs -f postgres
```

### Database Monitoring

Connect to PostgreSQL:
```bash
docker-compose exec postgres psql -U postgres -d benchmark
```

Check table stats:
```sql
SELECT COUNT(*) FROM items;
SELECT * FROM items LIMIT 10;
```

## Cleanup

Stop and remove all containers:
```bash
docker-compose down
```

Remove volumes (including database data):
```bash
docker-compose down -v
```

## Troubleshooting

### Database Connection Issues

If you see database connection errors, ensure PostgreSQL is ready:
```bash
docker-compose logs postgres
```

Wait for the message: `database system is ready to accept connections`

### Build Issues

If the Rupy build fails, ensure you have enough disk space and memory:
```bash
docker system df
docker system prune
```

### Port Conflicts

If ports 8001, 8002, or 5432 are already in use, modify the port mappings in `docker-compose.yml`.

## Development

### Local Testing Without Docker

Install dependencies:
```bash
# For Rupy
cd rupy-pg-upsert-select
pip install -r requirements.txt
pip install maturin
cd ../../..
maturin develop
cd benchmark/load-test/rupy-pg-upsert-select
python app.py

# For FastAPI
cd fastapi-pg-upsert-select
pip install -r requirements.txt
python app.py
```

Ensure PostgreSQL is running locally or update the environment variables.

## Contributing

When adding new endpoints or modifying the APIs:
1. Update both Rupy and FastAPI implementations to maintain compatibility
2. Update the Locust script to include new endpoints
3. Update this README with new instructions
4. Test both implementations to ensure they behave identically

## License

This benchmark suite follows the same license as the parent Rupy project (MIT).
