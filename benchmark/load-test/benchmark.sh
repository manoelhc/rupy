#!/bin/bash
# Helper script for running benchmark tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}============================================${NC}"
}

function print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

function print_info() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

function show_help() {
    cat << EOF
Benchmark Helper Script for Python Web Frameworks

Usage: $0 [COMMAND]

Commands:
    start              Start all services (PostgreSQL + all framework APIs)
    stop               Stop all services
    restart            Restart all services
    logs               Show logs for all services
    test               Run API compatibility tests for all frameworks
    bench-rupy         Run load test against Rupy (requires locust)
    bench-fastapi      Run load test against FastAPI (requires locust)
    bench-django       Run load test against Django REST (requires locust)
    bench-flask        Run load test against Flask-RESTful (requires locust)
    bench-robyn        Run load test against Robyn (requires locust)
    bench-mrhttp       Run load test against mrhttp (requires locust)
    bench-all          Run load tests against all frameworks sequentially
    clean              Stop services and remove volumes
    help               Show this help message

Frameworks included:
    - Rupy (port 8001)
    - FastAPI (port 8002)
    - Django REST Framework (port 8003)
    - Flask-RESTful (port 8004)
    - Robyn (port 8005)
    - mrhttp (port 8006)

Examples:
    $0 start
    $0 test
    $0 bench-rupy
    $0 bench-both

EOF
}

function start_services() {
    print_header "Starting Services"
    docker-compose up -d --build
    
    print_info "Waiting for services to be ready..."
    sleep 10
    
    echo ""
    echo "Services started:"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Rupy API: http://localhost:8001"
    echo "  - FastAPI: http://localhost:8002"
    echo "  - Django REST: http://localhost:8003"
    echo "  - Flask-RESTful: http://localhost:8004"
    echo "  - Robyn: http://localhost:8005"
    echo "  - mrhttp: http://localhost:8006"
    echo "  - Locust: http://localhost:8089"
}

function stop_services() {
    print_header "Stopping Services"
    docker-compose down
}

function restart_services() {
    stop_services
    start_services
}

function show_logs() {
    print_header "Service Logs"
    docker-compose logs -f
}

function run_tests() {
    print_header "Running API Compatibility Tests"
    
    if ! command -v python3 &> /dev/null; then
        print_error "python3 is required but not installed"
        exit 1
    fi
    
    # Check if requests is installed, install if needed
    if ! python3 -c "import requests" 2>/dev/null; then
        print_info "Installing requests package..."
        pip install --quiet requests || {
            print_error "Failed to install requests package"
            exit 1
        }
    fi
    
    python3 test_apis.py
}

function bench_api() {
    local api_name=$1
    local host=$2
    local port=$3
    
    print_header "Running Load Test: $api_name"
    
    if ! command -v locust &> /dev/null; then
        print_error "locust is not installed"
        echo "Install it with: pip install locust"
        exit 1
    fi
    
    local output_file="${api_name}-benchmark-$(date +%Y%m%d-%H%M%S)"
    
    print_info "Running 60-second test with 100 users..."
    print_info "Results will be saved to: ${output_file}.html"
    
    locust -f locustfile.py --headless \
        --users 100 \
        --spawn-rate 10 \
        --run-time 60s \
        --host "http://${host}:${port}" \
        --html "${output_file}.html" \
        --csv "${output_file}"
    
    echo ""
    print_info "Test complete! Results saved to ${output_file}.html"
    echo "Open the report with: open ${output_file}.html"
}

function bench_all() {
    bench_api "rupy" "localhost" "8001"
    echo ""
    bench_api "fastapi" "localhost" "8002"
    echo ""
    bench_api "django" "localhost" "8003"
    echo ""
    bench_api "flask" "localhost" "8004"
    echo ""
    bench_api "robyn" "localhost" "8005"
    echo ""
    bench_api "mrhttp" "localhost" "8006"
    
    print_header "Benchmark Comparison Complete"
    echo "Compare the HTML reports to see performance differences across all frameworks."
}

function clean_all() {
    print_header "Cleaning Up"
    docker-compose down -v
    print_info "All containers and volumes removed"
}

# Main command handler
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs
        ;;
    test)
        run_tests
        ;;
    bench-rupy)
        bench_api "rupy" "localhost" "8001"
        ;;
    bench-fastapi)
        bench_api "fastapi" "localhost" "8002"
        ;;
    bench-django)
        bench_api "django" "localhost" "8003"
        ;;
    bench-flask)
        bench_api "flask" "localhost" "8004"
        ;;
    bench-robyn)
        bench_api "robyn" "localhost" "8005"
        ;;
    bench-mrhttp)
        bench_api "mrhttp" "localhost" "8006"
        ;;
    bench-all)
        bench_all
        ;;
    clean)
        clean_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
