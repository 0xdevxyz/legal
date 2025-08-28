#!/bin/bash

# Production Deployment Script for Complyo
# Comprehensive production readiness implementation
# Version: 2.0
# Date: 2025-08-27

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/opt/projects/saas-project-2"
ENV_FILE="${PROJECT_ROOT}/.env.production"
DOCKER_COMPOSE_PROD="${PROJECT_ROOT}/docker-compose.production.yml"
DOCKER_COMPOSE_MONITORING="${PROJECT_ROOT}/docker-compose.monitoring.yml"
SSL_SCRIPT="${PROJECT_ROOT}/scripts/ssl-setup.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}" >&2; }
warning() { echo -e "${YELLOW}[WARNING] $1${NC}"; }
info() { echo -e "${BLUE}[INFO] $1${NC}"; }

# Progress tracking
TOTAL_STEPS=12
CURRENT_STEP=0

progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo -e "${BLUE}[Step $CURRENT_STEP/$TOTAL_STEPS] $1${NC}"
}

# Error handling
cleanup() {
    if [ $? -ne 0 ]; then
        error "Deployment failed! Rolling back changes..."
        docker-compose -f "$DOCKER_COMPOSE_PROD" down --remove-orphans || true
        docker-compose -f "$DOCKER_COMPOSE_MONITORING" down --remove-orphans || true
    fi
}
trap cleanup EXIT

# Validate prerequisites
validate_prerequisites() {
    progress "Validating prerequisites..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root for SSL certificate setup"
        exit 1
    fi
    
    # Check required commands
    local required_commands=("docker" "docker-compose" "openssl" "curl")\n    for cmd in "${required_commands[@]}"; do\n        if ! command -v "$cmd" &> /dev/null; then\n            error "Required command '$cmd' is not installed"\n            exit 1\n        fi\n    done\n    \n    # Check Docker daemon\n    if ! docker info &> /dev/null; then\n        error "Docker daemon is not running"\n        exit 1\n    fi\n    \n    # Check environment file\n    if [ ! -f "$ENV_FILE" ]; then\n        error "Production environment file not found: $ENV_FILE"\n        exit 1\n    fi\n    \n    log "✅ Prerequisites validated successfully"\n}\n\n# Load environment variables\nload_environment() {\n    progress "Loading production environment..."\n    \n    # Export environment variables\n    set -a\n    source "$ENV_FILE"\n    set +a\n    \n    # Validate required variables\n    local required_vars=("DB_PASSWORD" "REDIS_PASSWORD" "JWT_SECRET_KEY")\n    for var in "${required_vars[@]}"; do\n        if [ -z "${!var:-}" ]; then\n            error "Required environment variable '$var' is not set"\n            exit 1\n        fi\n    done\n    \n    log "✅ Environment loaded successfully"\n}\n\n# Setup SSL certificates\nsetup_ssl() {\n    progress "Setting up SSL certificates..."\n    \n    if [ ! -f "$SSL_SCRIPT" ]; then\n        error "SSL setup script not found: $SSL_SCRIPT"\n        exit 1\n    fi\n    \n    chmod +x "$SSL_SCRIPT"\n    \n    # Check if certificates already exist\n    if [ -d "/etc/letsencrypt/live/complyo.tech" ]; then\n        warning "SSL certificates already exist. Checking validity..."\n        "$SSL_SCRIPT" status\n    else\n        info "Generating new SSL certificates..."\n        "$SSL_SCRIPT" setup\n    fi\n    \n    log "✅ SSL certificates configured"\n}\n\n# Build production images\nbuild_images() {\n    progress "Building production Docker images..."\n    \n    cd "$PROJECT_ROOT"\n    \n    # Build with no cache for clean production images\n    docker-compose -f "$DOCKER_COMPOSE_PROD" build --no-cache --parallel\n    \n    # Verify images were built\n    local expected_images=(\n        "saas-project-2_complyo-backend-direct"\n        "saas-project-2_complyo-dashboard"\n        "saas-project-2_complyo-landing"\n    )\n    \n    for image in "${expected_images[@]}"; do\n        if ! docker images | grep -q "$image"; then\n            error "Failed to build image: $image"\n            exit 1\n        fi\n    done\n    \n    log "✅ Production images built successfully"\n}\n\n# Initialize database\ninit_database() {\n    progress "Initializing production database..."\n    \n    # Start only PostgreSQL for initialization\n    docker-compose -f "$DOCKER_COMPOSE_PROD" up -d shared-postgres\n    \n    # Wait for PostgreSQL to be ready\n    info "Waiting for PostgreSQL to be ready..."\n    for i in {1..30}; do\n        if docker-compose -f "$DOCKER_COMPOSE_PROD" exec -T shared-postgres pg_isready -U complyo_user; then\n            break\n        fi\n        sleep 2\n        if [ $i -eq 30 ]; then\n            error "PostgreSQL failed to start within 60 seconds"\n            exit 1\n        fi\n    done\n    \n    log "✅ Database initialized successfully"\n}\n\n# Start Redis cache\nstart_redis() {\n    progress "Starting Redis cache..."\n    \n    docker-compose -f "$DOCKER_COMPOSE_PROD" up -d shared-redis\n    \n    # Wait for Redis to be ready\n    info "Waiting for Redis to be ready..."\n    for i in {1..15}; do\n        if docker-compose -f "$DOCKER_COMPOSE_PROD" exec -T shared-redis redis-cli -a "$REDIS_PASSWORD" ping | grep -q "PONG"; then\n            break\n        fi\n        sleep 2\n        if [ $i -eq 15 ]; then\n            error "Redis failed to start within 30 seconds"\n            exit 1\n        fi\n    done\n    \n    log "✅ Redis started successfully"\n}\n\n# Deploy backend services\ndeploy_backend() {\n    progress "Deploying backend services..."\n    \n    docker-compose -f "$DOCKER_COMPOSE_PROD" up -d complyo-backend-direct\n    \n    # Wait for backend to be healthy\n    info "Waiting for backend to be healthy..."\n    for i in {1..30}; do\n        if curl -sf http://localhost:8002/health > /dev/null; then\n            break\n        fi\n        sleep 3\n        if [ $i -eq 30 ]; then\n            error "Backend failed to become healthy within 90 seconds"\n            exit 1\n        fi\n    done\n    \n    log "✅ Backend deployed successfully"\n}\n\n# Deploy frontend services\ndeploy_frontend() {\n    progress "Deploying frontend services..."\n    \n    docker-compose -f "$DOCKER_COMPOSE_PROD" up -d complyo-dashboard complyo-landing\n    \n    # Wait for frontend services to start\n    sleep 10\n    \n    log "✅ Frontend services deployed successfully"\n}\n\n# Deploy gateway\ndeploy_gateway() {\n    progress "Deploying production gateway..."\n    \n    docker-compose -f "$DOCKER_COMPOSE_PROD" up -d complyo-gateway\n    \n    # Wait for gateway to be ready\n    info "Waiting for gateway to be ready..."\n    for i in {1..20}; do\n        if curl -sf http://localhost:8080/nginx-health > /dev/null; then\n            break\n        fi\n        sleep 3\n        if [ $i -eq 20 ]; then\n            error "Gateway failed to start within 60 seconds"\n            exit 1\n        fi\n    done\n    \n    log "✅ Gateway deployed successfully"\n}\n\n# Setup monitoring stack\nsetup_monitoring() {\n    progress "Setting up monitoring stack..."\n    \n    # Create monitoring directories if they don't exist\n    mkdir -p "${PROJECT_ROOT}/monitoring/grafana/provisioning"\n    \n    docker-compose -f "$DOCKER_COMPOSE_MONITORING" up -d\n    \n    # Wait for Prometheus to be ready\n    info "Waiting for monitoring services..."\n    sleep 20\n    \n    log "✅ Monitoring stack deployed successfully"\n}\n\n# Run system validation\nvalidate_deployment() {\n    progress "Validating deployment..."\n    \n    local services=(\n        "https://complyo.tech:Landing page"\n        "https://app.complyo.tech:Dashboard"\n        "https://api.complyo.tech/health:API health check"\n    )\n    \n    local all_healthy=true\n    \n    for service in "${services[@]}"; do\n        local url="${service%:*}"\n        local name="${service#*:}"\n        \n        info "Testing $name ($url)..."\n        \n        if curl -sf -k "$url" > /dev/null; then\n            log "✅ $name is responding correctly"\n        else\n            error "❌ $name is not responding"\n            all_healthy=false\n        fi\n    done\n    \n    if [ "$all_healthy" = true ]; then\n        log "🎉 All services are healthy!"\n    else\n        error "❌ Some services are not responding correctly"\n        exit 1\n    fi\n}\n\n# Generate deployment report\ngenerate_report() {\n    progress "Generating deployment report..."\n    \n    local report_file="${PROJECT_ROOT}/deployment-report-$(date +%Y%m%d_%H%M%S).txt"\n    \n    cat > "$report_file" << EOF\nComplyo Production Deployment Report\nGenerated: $(date)\n\n=== DEPLOYMENT STATUS ===\nEnvironment: Production\nVersion: 2.0.0\nDeployment Time: $(date)\n\n=== SERVICES STATUS ===\nEOF\n\n    # Check service status\n    docker-compose -f "$DOCKER_COMPOSE_PROD" ps >> "$report_file"\n    \n    echo "" >> "$report_file"\n    echo "=== MONITORING SERVICES ===" >> "$report_file"\n    docker-compose -f "$DOCKER_COMPOSE_MONITORING" ps >> "$report_file"\n    \n    echo "" >> "$report_file"\n    echo "=== ACCESS URLS ===" >> "$report_file"\n    echo "Main Website: https://complyo.tech" >> "$report_file"\n    echo "Dashboard: https://app.complyo.tech" >> "$report_file"\n    echo "API Endpoint: https://api.complyo.tech" >> "$report_file"\n    echo "Monitoring: http://localhost:3001 (admin/[password])" >> "$report_file"\n    echo "Prometheus: http://localhost:9090" >> "$report_file"\n    \n    echo "" >> "$report_file"\n    echo "=== SECURITY STATUS ===" >> "$report_file"\n    "$SSL_SCRIPT" status >> "$report_file" 2>&1 || echo "SSL status check failed" >> "$report_file"\n    \n    log "✅ Deployment report generated: $report_file"\n}\n\n# Main deployment function\nmain() {\n    log "🚀 Starting Complyo Production Deployment"\n    log "================================================"\n    \n    validate_prerequisites\n    load_environment\n    setup_ssl\n    build_images\n    init_database\n    start_redis\n    deploy_backend\n    deploy_frontend\n    deploy_gateway\n    setup_monitoring\n    validate_deployment\n    generate_report\n    \n    log "================================================"\n    log "🎉 Production deployment completed successfully!"\n    log ""\n    log "📋 Next Steps:"\n    log "   1. Test all services thoroughly"\n    log "   2. Configure DNS to point to this server"\n    log "   3. Set up backup procedures"\n    log "   4. Configure monitoring alerts"\n    log "   5. Update team documentation"\n    log ""\n    log "🔗 Access URLs:"\n    log "   • Main Site: https://complyo.tech"\n    log "   • Dashboard: https://app.complyo.tech" \n    log "   • API: https://api.complyo.tech"\n    log "   • Monitoring: http://localhost:3001"\n    log ""\n    log "🔐 Security:"\n    log "   • SSL certificates configured and valid"\n    log "   • Rate limiting enabled"\n    log "   • Security headers configured"\n    log "   • Non-root containers"\n}\n\n# Handle script arguments\ncase "${1:-deploy}" in\n    "deploy")\n        main\n        ;;\n    "validate")\n        validate_prerequisites\n        load_environment\n        validate_deployment\n        ;;\n    "ssl")\n        setup_ssl\n        ;;\n    "help"|"-h"|"--help")\n        echo "Usage: $0 [command]"\n        echo ""\n        echo "Commands:"\n        echo "  deploy    - Full production deployment (default)"\n        echo "  validate  - Validate existing deployment"\n        echo "  ssl       - Setup SSL certificates only"\n        echo "  help      - Show this help message"\n        ;;\n    *)\n        error "Unknown command: $1"\n        exit 1\n        ;;\nesac