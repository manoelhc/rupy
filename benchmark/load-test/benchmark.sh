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
Rupy vs FastAPI Benchmark Helper Script

Usage: $0 [COMMAND]

Commands:
    start           Start all services (PostgreSQL, Rupy, FastAPI)
    stop            Stop all services
    restart         Restart all services
    logs            Show logs for all services
    test            Run API compatibility tests
    bench-rupy      Run load test against Rupy (requires locust)
    bench-fastapi   Run load test against FastAPI (requires locust)
    bench-both      Run load tests against both APIs sequentially
    clean           Stop services and remove volumes
    help            Show this help message

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
    
    # Install requests if needed
    pip install requests 2>/dev/null || true
    
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

function bench_both() {
    bench_api "rupy" "localhost" "8001"
    echo ""
    bench_api "fastapi" "localhost" "8002"
    
    print_header "Benchmark Comparison Complete"
    echo "Compare the HTML reports to see performance differences."
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
    bench-both)
        bench_both
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
