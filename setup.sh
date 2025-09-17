#!/bin/bash

# Voice-Enabled Browser Agent Setup Script
# This script sets up the complete development environment

set -e

echo "🚀 Setting up Voice-Enabled Browser Agent..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ and try again."
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm and try again."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.9+ and try again."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker is not installed. You'll need Docker for the monitoring stack."
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose is not installed. You'll need it for the monitoring stack."
    fi
    
    print_success "Requirements check completed"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Install root dependencies
    npm install
    
    # Install frontend dependencies
    print_status "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    
    # Install executor dependencies
    print_status "Installing executor dependencies..."
    cd executor
    npm install
    cd ..
    
    # Install backend dependencies
    print_status "Installing backend dependencies..."
    cd backend
    pip install -r requirements.txt
    cd ..
    
    print_success "All dependencies installed"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    if [ ! -f .env ]; then
        cp env.example .env
        print_success "Environment file created from template"
        print_warning "Please edit .env file with your API keys and configuration"
    else
        print_warning ".env file already exists, skipping creation"
    fi
}

# Setup monitoring stack
setup_monitoring() {
    print_status "Setting up monitoring stack..."
    
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        cd monitoring
        docker-compose up -d
        cd ..
        print_success "Monitoring stack started"
        print_status "Grafana: http://localhost:3001 (admin/admin)"
        print_status "Kibana: http://localhost:5601"
        print_status "Prometheus: http://localhost:9090"
    else
        print_warning "Docker not available, skipping monitoring stack setup"
        print_warning "You can start it later with: cd monitoring && docker-compose up -d"
    fi
}

# Build applications
build_applications() {
    print_status "Building applications..."
    
    # Build frontend
    print_status "Building frontend..."
    cd frontend
    npm run build
    cd ..
    
    # Build executor
    print_status "Building executor..."
    cd executor
    npm run build
    cd ..
    
    print_success "Applications built successfully"
}

# Main setup function
main() {
    echo "🎯 Voice-Enabled Browser Agent Setup"
    echo "====================================="
    echo ""
    
    check_requirements
    install_dependencies
    setup_environment
    setup_monitoring
    build_applications
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Edit .env file with your API keys"
    echo "2. Start the development servers:"
    echo "   npm run dev"
    echo ""
    echo "🌐 Access points:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend: http://localhost:8000"
    echo "   Executor: http://localhost:3001"
    echo "   Grafana: http://localhost:3001"
    echo "   Kibana: http://localhost:5601"
    echo ""
    echo "📚 Documentation: README.md"
    echo "🐛 Issues: Create GitHub issues for bugs or feature requests"
}

# Run main function
main "$@"
