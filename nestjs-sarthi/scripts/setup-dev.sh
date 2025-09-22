#!/bin/bash

# Development Environment Setup Script for CPT Vector Service
# This script sets up a complete development environment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js 18 or higher."
        exit 1
    fi
    
    local node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [[ $node_version -lt 18 ]]; then
        log_error "Node.js version 18 or higher is required. Current version: $(node --version)"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not installed. You'll need it for local database setup."
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose is not installed. You'll need it for local services."
    fi
    
    log_success "Prerequisites check completed"
}

# Install npm dependencies
install_dependencies() {
    log_info "Installing npm dependencies..."
    
    cd "$PROJECT_ROOT"
    npm ci
    
    log_success "Dependencies installed"
}

# Setup environment files
setup_environment() {
    log_info "Setting up environment configuration..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -f .env.local ]]; then
        cp .env.example .env.local
        log_success "Created .env.local from example"
        log_warning "Please update .env.local with your actual configuration values"
    else
        log_info ".env.local already exists"
    fi
    
    # Create .env.test if it doesn't exist
    if [[ ! -f .env.test ]]; then
        cat > .env.test << EOF
NODE_ENV=test
PORT=8080
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=test_user
DB_PASSWORD=test_password
DB_NAME=test_db
REDIS_HOST=localhost
REDIS_PORT=6379
JWT_SECRET=test_jwt_secret
ENCRYPTION_KEY=test_encryption_key
HIPAA_COMPLIANCE_ENABLED=false
AUTH_DISABLED=true
MULTI_TENANT_ENABLED=false
LOG_LEVEL=error
EOF
        log_success "Created .env.test for testing"
    fi
}

# Setup local databases with Docker
setup_local_services() {
    log_info "Setting up local services with Docker..."
    
    cd "$PROJECT_ROOT"
    
    # Create docker-compose.dev.yml if it doesn't exist
    if [[ ! -f docker-compose.dev.yml ]]; then
        cat > docker-compose.dev.yml << 'EOF'
version: '3.8'
services:
  postgres:
    image: postgres:14
    container_name: cpt-postgres-dev
    environment:
      POSTGRES_DB: sarthi_cpt_dev
      POSTGRES_USER: cpt_service
      POSTGRES_PASSWORD: dev_password
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cpt_service -d sarthi_cpt_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: cpt-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  postgres-test:
    image: postgres:14
    container_name: cpt-postgres-test
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d test_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis-test:
    image: redis:7-alpine
    container_name: cpt-redis-test
    ports:
      - "6380:6379"
    tmpfs:
      - /data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
EOF
        log_success "Created docker-compose.dev.yml"
    fi
    
    # Start services
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.dev.yml up -d
        
        # Wait for services to be healthy
        log_info "Waiting for services to be ready..."
        sleep 10
        
        if docker-compose -f docker-compose.dev.yml ps | grep -q "Up (healthy)"; then
            log_success "Local services are running"
        else
            log_warning "Some services may not be fully ready yet"
        fi
    else
        log_warning "Docker Compose not available. Please start PostgreSQL and Redis manually."
    fi
}

# Run database migrations
setup_database() {
    log_info "Setting up database schema..."
    
    cd "$PROJECT_ROOT"
    
    # Check if PostgreSQL is available
    if nc -z localhost 5432 2>/dev/null; then
        log_info "PostgreSQL is available, running migrations..."
        
        # Create database if it doesn't exist
        PGPASSWORD=dev_password createdb -h localhost -U cpt_service sarthi_cpt_dev 2>/dev/null || true
        
        # Run migration
        PGPASSWORD=dev_password psql -h localhost -U cpt_service -d sarthi_cpt_dev -f database/migrations/001-initial-schema.sql
        
        log_success "Database schema created"
    else
        log_warning "PostgreSQL not available. Please start PostgreSQL and run migrations manually."
    fi
}

# Setup Git hooks
setup_git_hooks() {
    log_info "Setting up Git hooks..."
    
    cd "$PROJECT_ROOT"
    
    # Create pre-commit hook
    mkdir -p .git/hooks
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for CPT Vector Service

set -e

echo "Running pre-commit checks..."

# Check if we're in the right directory
if [[ ! -f package.json ]]; then
    echo "Error: package.json not found. Please run from project root."
    exit 1
fi

# Run linting
echo "Running ESLint..."
npm run lint

# Run type checking
echo "Running TypeScript compiler..."
npm run typecheck

# Run tests
echo "Running tests..."
npm run test

echo "All pre-commit checks passed!"
EOF
    
    chmod +x .git/hooks/pre-commit
    log_success "Git pre-commit hook installed"
}

# Generate development SSL certificates
setup_ssl_certs() {
    log_info "Setting up development SSL certificates..."
    
    cd "$PROJECT_ROOT"
    mkdir -p certs
    
    if [[ ! -f certs/dev-cert.pem ]]; then
        # Generate self-signed certificate for development
        openssl req -x509 -newkey rsa:4096 -keyout certs/dev-key.pem -out certs/dev-cert.pem -days 365 -nodes \
            -subj "/C=US/ST=California/L=San Francisco/O=Sarthi Healthcare/CN=localhost" 2>/dev/null || {
            log_warning "OpenSSL not available. Skipping SSL certificate generation."
            return
        }
        
        log_success "Development SSL certificates generated"
    else
        log_info "Development SSL certificates already exist"
    fi
}

# Create useful development scripts
create_dev_scripts() {
    log_info "Creating development scripts..."
    
    mkdir -p scripts
    
    # Create database reset script
    cat > scripts/reset-db.sh << 'EOF'
#!/bin/bash
# Reset development database

set -e

echo "Resetting development database..."

# Drop and recreate database
PGPASSWORD=dev_password dropdb -h localhost -U cpt_service sarthi_cpt_dev --if-exists
PGPASSWORD=dev_password createdb -h localhost -U cpt_service sarthi_cpt_dev

# Run migrations
PGPASSWORD=dev_password psql -h localhost -U cpt_service -d sarthi_cpt_dev -f database/migrations/001-initial-schema.sql

echo "Database reset completed"
EOF
    chmod +x scripts/reset-db.sh
    
    # Create service start script
    cat > scripts/start-dev.sh << 'EOF'
#!/bin/bash
# Start development services

set -e

echo "Starting development environment..."

# Start Docker services
docker-compose -f docker-compose.dev.yml up -d

# Wait for services
echo "Waiting for services to be ready..."
sleep 10

# Start the application
npm run start:dev
EOF
    chmod +x scripts/start-dev.sh
    
    log_success "Development scripts created"
}

# Display setup summary
show_summary() {
    log_success "Development environment setup completed!"
    
    echo ""
    echo "📋 Setup Summary:"
    echo "  ✅ Dependencies installed"
    echo "  ✅ Environment files created"
    echo "  ✅ Local services configured"
    echo "  ✅ Database schema created"
    echo "  ✅ Git hooks installed"
    echo "  ✅ Development scripts created"
    echo ""
    echo "🚀 Next Steps:"
    echo "  1. Update .env.local with your configuration"
    echo "  2. Start development services:"
    echo "     docker-compose -f docker-compose.dev.yml up -d"
    echo "  3. Start the application:"
    echo "     npm run start:dev"
    echo "  4. Visit http://localhost:8080/api/docs for API documentation"
    echo ""
    echo "📚 Useful Commands:"
    echo "  npm run start:dev      - Start development server"
    echo "  npm run test:watch     - Run tests in watch mode"
    echo "  npm run lint           - Run ESLint"
    echo "  npm run typecheck      - Run TypeScript compiler"
    echo "  ./scripts/reset-db.sh  - Reset development database"
    echo "  ./scripts/start-dev.sh - Start full development environment"
    echo ""
    echo "🔗 Development URLs:"
    echo "  API: http://localhost:8080"
    echo "  Health: http://localhost:8080/health"
    echo "  Docs: http://localhost:8080/api/docs"
    echo "  Metrics: http://localhost:9090/metrics"
}

# Main function
main() {
    echo "🏥 Sarthi CPT Vector Service - Development Setup"
    echo "=============================================="
    echo ""
    
    check_prerequisites
    install_dependencies
    setup_environment
    setup_local_services
    setup_database
    setup_git_hooks
    setup_ssl_certs
    create_dev_scripts
    show_summary
}

# Run main function
main "$@"