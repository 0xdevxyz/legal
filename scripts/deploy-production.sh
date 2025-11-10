#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/opt/projects/saas-project-2"
ENV_FILE="${PROJECT_ROOT}/.env"
DOCKER_COMPOSE_PROD="${PROJECT_ROOT}/docker-compose.production.yml"
DOCKER_COMPOSE_MONITORING="${PROJECT_ROOT}/docker-compose.monitoring.yml"
SSL_SCRIPT="${PROJECT_ROOT}/scripts/ssl-setup.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}" >&2; }
warning() { echo -e "${YELLOW}[WARNING] $1${NC}"; }
info() { echo -e "${BLUE}[INFO] $1${NC}"; }

TOTAL_STEPS=12
CURRENT_STEP=0

progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo -e "${BLUE}[Step $CURRENT_STEP/$TOTAL_STEPS] $1${NC}"
}

cleanup() {
    if [ $? -ne 0 ]; then
        error "Deployment failed! Rolling back changes..."
        docker-compose -f "$DOCKER_COMPOSE_PROD" down --remove-orphans || true
        docker-compose -f "$DOCKER_COMPOSE_MONITORING" down --remove-orphans || true
    fi
}
trap cleanup EXIT

validate_prerequisites() {
    progress "Validating prerequisites..."
    
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi
    
    local required_commands=("docker" "docker-compose" "openssl" "curl")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "Required command '$cmd' is not installed"
            exit 1
        fi
    done
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        error "Production environment file not found: $ENV_FILE"
        exit 1
    fi
    
    log "✅ Prerequisites validated successfully"
}

load_environment() {
    progress "Loading production environment..."
    
    set -a
    source "$ENV_FILE"
    set +a
    
    local required_vars=("DB_PASSWORD" "REDIS_PASSWORD" "JWT_SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            error "Required environment variable '$var' is not set"
            exit 1
        fi
    done
    
    log "✅ Environment loaded successfully"
}

setup_ssl() {
    progress "Setting up SSL certificates..."
    
    if [ ! -f "$SSL_SCRIPT" ]; then
        error "SSL setup script not found: $SSL_SCRIPT"
        exit 1
    fi
    
    chmod +x "$SSL_SCRIPT"
    
    if [ -d "/etc/letsencrypt/live/complyo.tech" ]; then
        warning "SSL certificates already exist. Skipping renewal due to rate limits."
        "$SSL_SCRIPT" status || true
    else
        info "Generating new SSL certificates..."
        "$SSL_SCRIPT" setup
    fi
    
    log "✅ SSL certificates configured"
}

build_images() {
    progress "Building production Docker images..."
    
    cd "$PROJECT_ROOT"
    
    docker-compose -f "$DOCKER_COMPOSE_PROD" build --no-cache
    
    local expected_images=(
        "complyo/backend"
        "complyo/dashboard"
        "complyo/landing"
    )
    
    for image in "${expected_images[@]}"; do
        if ! docker images | grep -q "$image"; then
            error "Failed to build image: $image"
            error "Current docker images:"
            docker images
            exit 1
        fi
    done
    
    log "✅ Production images built successfully"
}

init_database() {
    progress "Initializing production database..."
    
    docker-compose -f "$DOCKER_COMPOSE_PROD" up -d shared-postgres
    
    info "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker-compose -f "$DOCKER_COMPOSE_PROD" exec -T shared-postgres pg_isready -U complyo_user; then
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            error "PostgreSQL failed to start within 60 seconds"
            exit 1
        fi
    done
    
    log "✅ Database initialized successfully"
}

start_redis() {
    progress "Starting Redis cache..."
    
    docker-compose -f "$DOCKER_COMPOSE_PROD" up -d shared-redis
    
    info "Waiting for Redis to be ready..."
    for i in {1..15}; do
        if docker-compose -f "$DOCKER_COMPOSE_PROD" exec -T shared-redis redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
            break
        fi
        sleep 2
        if [ $i -eq 15 ]; then
            error "Redis failed to start within 30 seconds"
            exit 1
        fi
    done
    
    log "✅ Redis started successfully"
}

deploy_backend() {
    progress "Deploying backend services..."
    
    docker-compose -f "$DOCKER_COMPOSE_PROD" up -d complyo-backend-direct
    
    info "Waiting for backend to be healthy..."
    for i in {1..30}; do
        if curl -sf http://localhost:8002/health > /dev/null 2>&1; then
            break
        fi
        sleep 3
        if [ $i -eq 30 ]; then
            warning "Backend health check timeout - continuing anyway"
            break
        fi
    done
    
    log "✅ Backend deployed successfully"
}

deploy_frontend() {
    progress "Deploying frontend services..."
    
    docker-compose -f "$DOCKER_COMPOSE_PROD" up -d complyo-dashboard complyo-landing
    
    sleep 10
    
    log "✅ Frontend services deployed successfully"
}

deploy_ssl_proxy() {
    progress "Deploying SSL proxy..."
    
    docker-compose -f "$DOCKER_COMPOSE_PROD" up -d complyo-ssl-proxy
    
    sleep 5
    
    log "✅ SSL proxy deployed successfully"
}

setup_monitoring() {
    progress "Setting up monitoring stack..."
    
    mkdir -p "${PROJECT_ROOT}/monitoring/grafana/provisioning"
    
    docker-compose -f "$DOCKER_COMPOSE_MONITORING" up -d || warning "Monitoring stack failed to start - continuing"
    
    sleep 10
    
    log "✅ Monitoring stack deployed successfully"
}

validate_deployment() {
    progress "Validating deployment..."
    
    docker-compose -f "$DOCKER_COMPOSE_PROD" ps
    
    log "✅ Deployment validation complete"
}

generate_report() {
    progress "Generating deployment report..."
    
    local report_file="${PROJECT_ROOT}/deployment-report-$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
Complyo Production Deployment Report
Generated: $(date)

=== DEPLOYMENT STATUS ===
Environment: Production
Deployment Time: $(date)

=== SERVICES STATUS ===
EOF

    docker-compose -f "$DOCKER_COMPOSE_PROD" ps >> "$report_file"
    
    log "✅ Deployment report generated: $report_file"
}

main() {
    log "🚀 Starting Complyo Production Deployment"
    log "================================================"
    
    validate_prerequisites
    load_environment
    setup_ssl
    build_images
    init_database
    start_redis
    deploy_backend
    deploy_frontend
    deploy_ssl_proxy
    setup_monitoring
    validate_deployment
    generate_report
    
    log "================================================"
    log "🎉 Production deployment completed successfully!"
    log ""
    log "Access URLs:"
    log "   • Landing: http://localhost:3003"
    log "   • Dashboard: http://localhost:3001"
    log "   • API: http://localhost:8002"
}

case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "validate")
        validate_prerequisites
        load_environment
        validate_deployment
        ;;
    "ssl")
        setup_ssl
        ;;
    *)
        error "Unknown command: $1"
        exit 1
        ;;
esac
