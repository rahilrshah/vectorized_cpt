#!/bin/bash

# Sarthi CPT Vector Service Deployment Script
# Usage: ./scripts/deploy.sh [environment] [version]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Environment configuration
case $ENVIRONMENT in
    "staging")
        NAMESPACE="sarthi-backend-staging"
        CLUSTER="sarthi-staging-cluster"
        PROJECT_ID="sarthi-healthcare-staging"
        DOMAIN="api-staging.sarthi.healthcare"
        ;;
    "production")
        NAMESPACE="sarthi-backend"
        CLUSTER="sarthi-prod-cluster"
        PROJECT_ID="sarthi-healthcare-prod"
        DOMAIN="api.sarthi.healthcare"
        ;;
    *)
        log_error "Invalid environment: $ENVIRONMENT. Use 'staging' or 'production'"
        exit 1
        ;;
esac

IMAGE="gcr.io/${PROJECT_ID}/cpt-vector-service:${VERSION}"

log_info "Starting deployment to $ENVIRONMENT environment"
log_info "Image: $IMAGE"
log_info "Namespace: $NAMESPACE"

# Pre-deployment checks
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required tools
    for tool in kubectl docker gcloud; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check Docker registry access
    if ! gcloud auth configure-docker --quiet; then
        log_error "Cannot configure Docker registry access"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build and push Docker image
build_and_push() {
    log_info "Building and pushing Docker image..."
    
    cd "$PROJECT_ROOT"
    
    # Build image
    docker build -t "$IMAGE" .
    
    # Push to registry
    docker push "$IMAGE"
    
    log_success "Docker image built and pushed: $IMAGE"
}

# Deploy to Kubernetes
deploy_to_k8s() {
    log_info "Deploying to Kubernetes..."
    
    cd "$PROJECT_ROOT/k8s"
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Update image tag in deployment
    sed -i.bak "s|gcr.io/sarthi-healthcare-prod/cpt-vector-service:.*|$IMAGE|g" deployment.yaml
    
    # Apply configurations in order
    kubectl apply -f namespace.yaml -n "$NAMESPACE"
    kubectl apply -f configmap.yaml -n "$NAMESPACE"
    kubectl apply -f secret.yaml -n "$NAMESPACE"
    kubectl apply -f rbac.yaml -n "$NAMESPACE"
    kubectl apply -f deployment.yaml -n "$NAMESPACE"
    kubectl apply -f service.yaml -n "$NAMESPACE"
    kubectl apply -f hpa.yaml -n "$NAMESPACE"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        kubectl apply -f ingress.yaml -n "$NAMESPACE"
    fi
    
    kubectl apply -f network-policy.yaml -n "$NAMESPACE"
    
    # Restore original deployment file
    mv deployment.yaml.bak deployment.yaml
    
    log_success "Kubernetes manifests applied"
}

# Wait for deployment to complete
wait_for_deployment() {
    log_info "Waiting for deployment to complete..."
    
    # Wait for rollout to complete
    if kubectl rollout status deployment/cpt-vector-service -n "$NAMESPACE" --timeout=600s; then
        log_success "Deployment rollout completed"
    else
        log_error "Deployment rollout failed"
        return 1
    fi
    
    # Wait for pods to be ready
    if kubectl wait --for=condition=ready pod -l app=cpt-vector-service -n "$NAMESPACE" --timeout=300s; then
        log_success "All pods are ready"
    else
        log_error "Pods failed to become ready"
        return 1
    fi
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Get service endpoint
    if [[ "$ENVIRONMENT" == "production" ]]; then
        ENDPOINT="https://$DOMAIN"
    else
        # For staging, use port-forward
        kubectl port-forward service/cpt-vector-service 8080:80 -n "$NAMESPACE" &
        PORT_FORWARD_PID=$!
        sleep 10
        ENDPOINT="http://localhost:8080"
    fi
    
    # Test health endpoints
    if curl -f "$ENDPOINT/health" > /dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        [[ -n "${PORT_FORWARD_PID:-}" ]] && kill $PORT_FORWARD_PID
        return 1
    fi
    
    if curl -f "$ENDPOINT/ready" > /dev/null 2>&1; then
        log_success "Readiness check passed"
    else
        log_error "Readiness check failed"
        [[ -n "${PORT_FORWARD_PID:-}" ]] && kill $PORT_FORWARD_PID
        return 1
    fi
    
    # Test API endpoints with authentication (if available)
    if [[ -n "${TEST_API_KEY:-}" ]]; then
        if curl -f -H "Authorization: Bearer $TEST_API_KEY" -H "X-Tenant-Id: test-tenant" "$ENDPOINT/api/docs" > /dev/null 2>&1; then
            log_success "API endpoint check passed"
        else
            log_warning "API endpoint check failed (may need authentication)"
        fi
    fi
    
    # Clean up port-forward
    [[ -n "${PORT_FORWARD_PID:-}" ]] && kill $PORT_FORWARD_PID
}

# Get deployment status
get_deployment_status() {
    log_info "Deployment status:"
    
    kubectl get deployment cpt-vector-service -n "$NAMESPACE" -o wide
    kubectl get pods -l app=cpt-vector-service -n "$NAMESPACE"
    kubectl get services -l app=cpt-vector-service -n "$NAMESPACE"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        kubectl get ingress -l app=cpt-vector-service -n "$NAMESPACE"
    fi
}

# Rollback deployment
rollback_deployment() {
    log_warning "Rolling back deployment..."
    
    kubectl rollout undo deployment/cpt-vector-service -n "$NAMESPACE"
    kubectl rollout status deployment/cpt-vector-service -n "$NAMESPACE" --timeout=300s
    
    log_success "Rollback completed"
}

# Main deployment function
main() {
    local start_time=$(date +%s)
    
    # Set up error handling
    trap 'log_error "Deployment failed!"; rollback_deployment; exit 1' ERR
    
    check_prerequisites
    
    if [[ "${BUILD_IMAGE:-true}" == "true" ]]; then
        build_and_push
    fi
    
    deploy_to_k8s
    wait_for_deployment
    run_health_checks
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "Deployment completed successfully in ${duration}s"
    
    get_deployment_status
    
    log_info "Service endpoints:"
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo "  API: https://$DOMAIN/api/v1/cpt-search"
        echo "  Health: https://$DOMAIN/health"
        echo "  Docs: https://$DOMAIN/api/docs"
    else
        echo "  Use kubectl port-forward to access staging endpoints"
        echo "  kubectl port-forward service/cpt-vector-service 8080:80 -n $NAMESPACE"
    fi
}

# Script usage
usage() {
    cat << EOF
Usage: $0 [environment] [version] [options]

Arguments:
  environment  Target environment (staging|production) [default: staging]
  version     Docker image version tag [default: latest]

Environment Variables:
  BUILD_IMAGE     Whether to build and push image [default: true]
  TEST_API_KEY    API key for endpoint testing [optional]

Examples:
  $0 staging v1.2.3
  $0 production latest
  BUILD_IMAGE=false $0 staging v1.2.3

EOF
}

# Handle script arguments
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

# Run main function
main "$@"