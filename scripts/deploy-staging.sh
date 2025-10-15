#!/bin/bash

# Staging deployment script for Trading Bot Swarm
# This script helps deploy the application to a staging environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[→]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_status "Docker found"
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_status "Docker Compose found"
}

# Check if required files exist
check_files() {
    print_step "Checking required files..."
    
    if [ ! -f "docker-compose.staging.yml" ]; then
        print_error "docker-compose.staging.yml not found!"
        exit 1
    fi
    
    if [ ! -f "config/.env.staging" ]; then
        print_error "config/.env.staging not found!"
        exit 1
    fi
    
    print_status "Required files found"
}

# Setup environment
setup_env() {
    print_step "Setting up environment..."
    
    if [ ! -f "config/.env" ]; then
        cp config/.env.staging config/.env
        print_status "Environment file created from staging template"
        print_info "Please edit config/.env with your staging credentials"
        read -p "Press enter when ready to continue..."
    else
        print_info "config/.env already exists"
    fi
}

# Pull latest code
pull_code() {
    print_step "Pulling latest code from git..."
    
    if [ -d ".git" ]; then
        git pull origin develop
        print_status "Code updated"
    else
        print_info "Not a git repository. Skipping pull."
    fi
}

# Build Docker images
build_images() {
    print_step "Building Docker images..."
    
    docker-compose -f docker-compose.staging.yml build --no-cache
    print_status "Images built successfully"
}

# Start services
start_services() {
    print_step "Starting services..."
    
    docker-compose -f docker-compose.staging.yml up -d
    print_status "Services started"
}

# Wait for services to be ready
wait_for_services() {
    print_step "Waiting for services to be ready..."
    
    sleep 10
    
    # Check if services are running
    if docker-compose -f docker-compose.staging.yml ps | grep -q "Up"; then
        print_status "Services are running"
    else
        print_error "Some services failed to start"
        docker-compose -f docker-compose.staging.yml ps
        exit 1
    fi
}

# Run health checks
health_check() {
    print_step "Running health checks..."
    
    # Check application
    if curl -f http://localhost:8080/health &> /dev/null; then
        print_status "Application is healthy"
    else
        print_error "Application health check failed"
    fi
    
    # Check database
    if docker-compose -f docker-compose.staging.yml exec -T postgres-staging pg_isready &> /dev/null; then
        print_status "Database is healthy"
    else
        print_error "Database health check failed"
    fi
    
    # Check Redis
    if docker-compose -f docker-compose.staging.yml exec -T redis-staging redis-cli ping &> /dev/null; then
        print_status "Redis is healthy"
    else
        print_error "Redis health check failed"
    fi
}

# Show service status
show_status() {
    echo ""
    echo "================================================"
    echo "  Service Status"
    echo "================================================"
    docker-compose -f docker-compose.staging.yml ps
    echo ""
}

# Show access information
show_access_info() {
    echo ""
    echo "================================================"
    echo "  Access Information"
    echo "================================================"
    echo ""
    echo "Application:     http://localhost:8080"
    echo "Prometheus:      http://localhost:9090"
    echo "Grafana:         http://localhost:3000 (admin/admin)"
    echo "Nginx:           http://localhost:80"
    echo ""
    echo "Logs:            docker-compose -f docker-compose.staging.yml logs -f"
    echo "Stop:            docker-compose -f docker-compose.staging.yml down"
    echo "Restart:         docker-compose -f docker-compose.staging.yml restart"
    echo ""
}

# Rollback function
rollback() {
    print_error "Deployment failed. Rolling back..."
    
    docker-compose -f docker-compose.staging.yml down
    print_status "Services stopped"
    
    exit 1
}

# Main deployment flow
main() {
    echo "================================================"
    echo "  Trading Bot Swarm - Staging Deployment"
    echo "================================================"
    echo ""
    
    # Trap errors and rollback
    trap rollback ERR
    
    check_docker
    check_files
    
    # Confirm deployment
    read -p "Deploy to staging environment? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi
    
    setup_env
    pull_code
    build_images
    start_services
    wait_for_services
    health_check
    show_status
    show_access_info
    
    print_status "Staging deployment completed successfully!"
}

# Run main function
main
