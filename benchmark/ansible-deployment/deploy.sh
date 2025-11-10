#!/bin/bash
# Quick deployment script for benchmark infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function check_ansible() {
    if ! command -v ansible &> /dev/null; then
        print_error "Ansible is not installed"
        echo "Install with: pip install ansible"
        exit 1
    fi
    print_success "Ansible is installed"
}

function check_inventory() {
    if [ ! -f "inventory.yml" ]; then
        print_error "inventory.yml not found"
        exit 1
    fi
    
    # Check if inventory has been customized
    if grep -q "192.168.1.10" inventory.yml; then
        print_error "Please update inventory.yml with your actual server IPs"
        echo "Edit inventory.yml and replace 192.168.1.* with your server addresses"
        exit 1
    fi
    print_success "Inventory file configured"
}

function test_connectivity() {
    print_header "Testing Connectivity"
    ansible all -m ping || {
        print_error "Cannot connect to servers. Check:"
        echo "  1. SSH keys are configured"
        echo "  2. IPs in inventory.yml are correct"
        echo "  3. Servers are accessible"
        exit 1
    }
    print_success "All servers are reachable"
}

function deploy_all() {
    print_header "Deploying Benchmark Infrastructure"
    
    print_info "Step 1/4: Common setup..."
    ansible-playbook playbooks/common.yml || exit 1
    
    print_info "Step 2/4: Database setup..."
    ansible-playbook playbooks/database.yml || exit 1
    
    print_info "Step 3/4: Application servers setup..."
    ansible-playbook playbooks/apps.yml || exit 1
    
    print_info "Step 4/4: Locust setup..."
    ansible-playbook playbooks/locust.yml || exit 1
    
    print_success "Deployment complete!"
}

function show_status() {
    print_header "Service Status"
    ansible-playbook playbooks/manage.yml -e "action=status"
}

function start_services() {
    print_header "Starting Services"
    ansible-playbook playbooks/manage.yml -e "action=start"
    print_success "All services started"
}

function stop_services() {
    print_header "Stopping Services"
    ansible-playbook playbooks/manage.yml -e "action=stop"
    print_success "All services stopped"
}

function restart_services() {
    print_header "Restarting Services"
    ansible-playbook playbooks/manage.yml -e "action=restart"
    print_success "All services restarted"
}

function show_info() {
    print_header "Deployment Information"
    
    # Get IPs from inventory
    LOCUST_IP=$(grep -A1 "locust-server:" inventory.yml | grep ansible_host | awk '{print $2}')
    APP_IP=$(grep -A1 "app-server:" inventory.yml | grep ansible_host | awk '{print $2}')
    DB_IP=$(grep -A1 "db-server:" inventory.yml | grep ansible_host | awk '{print $2}')
    
    echo ""
    echo "Locust Web UI:    http://${LOCUST_IP}:8089"
    echo ""
    echo "Application Servers:"
    echo "  Rupy:      http://${APP_IP}:8001"
    echo "  FastAPI:   http://${APP_IP}:8002"
    echo "  Django:    http://${APP_IP}:8003"
    echo "  Flask:     http://${APP_IP}:8004"
    echo "  Robyn:     http://${APP_IP}:8005"
    echo "  mrhttp:    http://${APP_IP}:8006"
    echo ""
    echo "Database:         ${DB_IP}:5432"
    echo ""
    echo "To run a load test:"
    echo "  ssh ubuntu@${LOCUST_IP}"
    echo "  /opt/benchmark/locust/run_test.sh rupy 100 10 60s"
    echo ""
}

function show_help() {
    cat << EOF
Benchmark Infrastructure Deployment Script

Usage: $0 [COMMAND]

Commands:
    check       Check prerequisites
    deploy      Deploy all components
    status      Show service status
    start       Start all services
    stop        Stop all services
    restart     Restart all services
    info        Show deployment information
    help        Show this help message

Examples:
    $0 check          # Check prerequisites
    $0 deploy         # Full deployment
    $0 status         # Check service status
    $0 info           # Show URLs and IPs

EOF
}

# Main
case "${1:-help}" in
    check)
        print_header "Checking Prerequisites"
        check_ansible
        check_inventory
        test_connectivity
        print_success "All checks passed!"
        ;;
    deploy)
        check_ansible
        check_inventory
        test_connectivity
        deploy_all
        show_info
        ;;
    status)
        show_status
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    info)
        show_info
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
