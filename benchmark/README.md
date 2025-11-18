# Rupy Benchmark Suite

This directory contains benchmarking tools and load tests for comparing Rupy's performance against other Python web frameworks.

## Available Benchmarks

### Load Test: Python Web Frameworks with PostgreSQL

**Location:** `benchmark/load-test/`

This benchmark compares multiple Python web frameworks for typical database operations:
- INSERT operations
- UPDATE operations  
- SELECT operations
- UPSERT operations

**Frameworks included:**
- **Rupy** - High-performance framework powered by Rust
- **FastAPI** - Modern async Python framework
- **Django REST Framework** - Full-featured Django extension
- **Flask-RESTful** - Lightweight RESTful extension for Flask
- **Robyn** - Fast async framework built with Rust
- **mrhttp** - High-performance C extension framework

All implementations use:
- PostgreSQL database with the official `psycopg2` driver
- Identical API endpoints and behavior
- Docker containers for consistent testing environment
- Locust for load testing and performance measurement

**Quick Start:**
```bash
cd load-test
./benchmark.sh start      # Start all services
./benchmark.sh test       # Run compatibility tests
./benchmark.sh bench-all  # Run load tests on all frameworks
```

See [load-test/README.md](load-test/README.md) for detailed documentation.

## Contributing New Benchmarks

When adding new benchmarks:

1. Create a new subdirectory under `benchmark/`
2. Include implementations for Rupy and comparison frameworks
3. Provide Docker setup for consistent testing
4. Add comprehensive documentation
5. Include scripts for easy execution

## Benchmark Goals

These benchmarks aim to:

- **Measure** real-world performance with common operations
- **Compare** Rupy against established Python frameworks
- **Validate** that Rupy's performance claims are reproducible
- **Identify** performance characteristics and bottlenecks
- **Guide** optimization efforts

## Interpreting Results

When reviewing benchmark results, consider:

- **Throughput** (requests per second)
- **Latency** (response time percentiles: p50, p95, p99)
- **Resource usage** (CPU and memory consumption)
- **Error rates** under load
- **Consistency** across multiple runs

Remember that benchmarks reflect specific workloads and configurations. Real-world performance may vary based on your application's requirements.

## License

Same as the parent Rupy project (MIT).
