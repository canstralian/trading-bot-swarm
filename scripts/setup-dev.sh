#!/bin/bash

# Development environment setup script for Trading Bot Swarm
# This script automates the setup of the local development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.10 or higher."
        exit 1
    fi
    
    python_version=$(python3 --version | awk '{print $2}')
    print_status "Python $python_version found"
}

# Create virtual environment
setup_venv() {
    print_info "Setting up virtual environment..."
    
    if [ -d ".venv" ]; then
        print_info "Virtual environment already exists. Skipping creation."
    else
        python3 -m venv .venv
        print_status "Virtual environment created"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    print_status "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_info "Installing dependencies..."
    
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    
    print_status "Dependencies installed"
}

# Setup configuration
setup_config() {
    print_info "Setting up configuration files..."
    
    if [ ! -f "config/.env" ]; then
        cp config/.env.development config/.env
        print_status "Development environment file created at config/.env"
        print_info "Edit config/.env to add your API keys if needed"
    else
        print_info "config/.env already exists. Skipping."
    fi
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    
    mkdir -p data
    mkdir -p logs
    
    print_status "Directories created"
}

# Run tests
run_tests() {
    print_info "Running tests to verify setup..."
    
    if pytest tests/ -v; then
        print_status "All tests passed!"
    else
        print_error "Some tests failed. Please check the output above."
    fi
}

# Main setup flow
main() {
    echo "================================================"
    echo "  Trading Bot Swarm - Development Setup"
    echo "================================================"
    echo ""
    
    check_python
    setup_venv
    install_dependencies
    setup_config
    create_directories
    
    echo ""
    print_status "Development environment setup complete!"
    echo ""
    print_info "To activate the virtual environment in the future, run:"
    echo "  source .venv/bin/activate"
    echo ""
    print_info "To run the application in development mode:"
    echo "  python main.py --env development"
    echo ""
    print_info "To run tests:"
    echo "  pytest tests/"
    echo ""
    
    # Ask if user wants to run tests
    read -p "Would you like to run tests now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_tests
    fi
    
    echo ""
    print_status "Happy coding!"
}

# Run main function
main
