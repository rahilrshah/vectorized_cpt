# Vectorized CPT Microservices Architecture

This document describes the new microservices architecture for the Vectorized CPT project, which provides API-key based access to medical coding and CPT search functionality.

## Architecture Overview

The system is now organized into 4 main microservices:

```
┌─────────────────┐    ┌──────────────────────┐
│   API Gateway   │    │   Medical Processor  │
│   Port: 8000    │◄──►│     Port: 8001       │
│   Auth & Route  │    │   AI Text Processing │
└─────────────────┘    └──────────────────────┘
         │
         ▼              ┌──────────────────────┐
┌─────────────────┐    │    CPT Search        │
│   Client Apps   │    │     Port: 8002       │
│   Web/Mobile    │    │  Vector Similarity   │
└─────────────────┘    └──────────────────────┘
                                │
                       ┌──────────────────────┐
                       │  Medical Coding      │
                       │     Port: 8003       │
                       │ Anesthesia/Modifiers │
                       └──────────────────────┘
```

## Services

### 1. API Gateway (Port 8000)
- **Purpose**: Unified entry point with API key authentication
- **Features**: 
  - API key management and validation
  - Rate limiting and usage tracking
  - Request routing to microservices
  - Complete workflow orchestration
- **Main Endpoint**: `/api/v1/process` - Complete medical note processing

### 2. Medical Processor API (Port 8001)
- **Purpose**: AI-powered medical text processing
- **Features**:
  - Extract procedures from medical notes using Gemini AI
  - PDF text extraction
  - Structured data extraction
- **Main Endpoint**: `/api/v1/medical/extract`

### 3. CPT Search API (Port 8002)
- **Purpose**: Vector-based CPT code search
- **Features**:
  - Semantic similarity search using embeddings
  - Enhanced medical relevance scoring
  - Keyword-based fallback search
- **Main Endpoint**: `/api/v1/cpt/search`

### 4. Medical Coding API (Port 8003)
- **Purpose**: Comprehensive medical coding analysis
- **Features**:
  - Anesthesia code detection
  - Modifier recommendations
  - Related diagnostic codes
  - Billing summary generation
- **Main Endpoint**: `/api/v1/medical/code-complete`

## Quick Start

### 1. Start All Services

```bash
# Install dependencies
pip install -r requirements.txt

# Start all microservices
python start_services.py start
```

This will start:
- Medical Processor API on http://localhost:8001
- CPT Search API on http://localhost:8002
- Medical Coding API on http://localhost:8003
- API Gateway on http://localhost:8000

### 2. Create an API Key

```bash
# Create an example API key
python start_services.py create-key
```

This will output an API key that you can use for testing.

### 3. Test the Complete Workflow

```bash
# Set your API key
export VECTORIZED_CPT_API_KEY=your_api_key_here

# Test with curl
curl -X POST "http://localhost:8000/api/v1/process" \
     -H "Authorization: Bearer $VECTORIZED_CPT_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Patient underwent arthroscopic knee surgery with meniscus repair.",
       "max_results": 10,
       "include_comprehensive": true
     }'
```

## Using Docker

### Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## API Usage

### Authentication
All API requests require an API key in the Authorization header:

```
Authorization: Bearer vcp_your_api_key_here
```

### Main Workflow Endpoint

**POST** `/api/v1/process`

Complete medical note processing that preserves exact functionality of the original `Billing.process_medical_note()` method.

```json
{
  "text": "Patient underwent arthroscopic knee surgery...",
  "max_results": 20,
  "include_comprehensive": true,
  "pdf_base64": null  // Optional: PDF content as base64
}
```

Response:
```json
{
  "step1_extracted_text": "Patient underwent...",
  "step2_extracted_procedures": "Arthroscopic knee surgery, meniscus repair",
  "step3_cpt_results": [...],
  "step4_comprehensive_codes": {...},
  "total_processing_time_ms": 2500,
  "services_used": ["medical_processor", "cpt_search", "medical_coding"],
  "success": true
}
```

### Individual Service Endpoints

#### Medical Text Processing
**POST** `/api/v1/medical/extract`
```json
{
  "text": "Medical note text...",
  "extract_structured": false
}
```

#### CPT Code Search
**POST** `/api/v1/cpt/search`
```json
{
  "procedures": "Arthroscopic knee surgery",
  "max_results": 20,
  "similarity_threshold": 0.6
}
```

#### Comprehensive Medical Coding
**POST** `/api/v1/medical/code-complete`
```json
{
  "primary_codes": [...],
  "medical_text": "Extracted procedures...",
  "original_note": "Full medical note...",
  "include_diagnostics": true,
  "include_anesthesia": true,
  "include_modifiers": true
}
```

### Health Check and Usage

```bash
# Check system health
GET /health

# Get API key usage statistics
GET /api/v1/usage
```

## Backward Compatibility

The new architecture maintains 100% backward compatibility with existing code through the `HybridBilling` class:

### Python Integration

```python
from app.billing_hybrid import HybridBilling

# Use API mode
billing = HybridBilling(use_api_mode=True, api_key="your_key")
result = await billing.process_medical_note("Medical note text...")

# Use direct mode (original architecture)
billing = HybridBilling(use_api_mode=False)
result = await billing.process_medical_note("Medical note text...")
```

### Environment-Based Configuration

```python
from app.billing_hybrid import create_auto_billing_system

# Configure via environment variables
os.environ['VECTORIZED_CPT_MODE'] = 'api'  # or 'direct'
os.environ['VECTORIZED_CPT_API_KEY'] = 'your_key'
os.environ['VECTORIZED_CPT_GATEWAY_URL'] = 'http://localhost:8000'

billing = create_auto_billing_system()
```

### Firebase Functions Compatibility

The existing Firebase Functions continue to work unchanged. The `Billing` class in `functions/src/billing/index.ts` remains fully functional.

## API Key Management

### Creating API Keys

```python
from api_gateway.auth import api_key_manager

# Create API key
api_key, key_id = api_key_manager.generate_api_key(
    user_id="customer_123",
    rate_limit_per_hour=1000,
    expires_days=365
)
```

### Rate Limiting

- Default: 1000 requests per hour per API key
- Configurable per key
- HTTP 429 response when exceeded
- Usage tracking in SQLite database

### Usage Analytics

Each API call is logged with:
- Endpoint accessed
- Response time
- Success/failure status
- Service used
- Timestamp

## Development

### Project Structure

```
├── api_gateway/           # API Gateway with authentication
│   ├── main.py           # FastAPI application
│   ├── auth.py           # API key management
│   ├── routing.py        # Service routing
│   └── models.py         # Pydantic models
├── api_services/         # Individual microservices
│   ├── medical_processor/
│   ├── cpt_search/
│   └── medical_coding/
├── app/                  # Original application (backward compatibility)
│   ├── billing_hybrid.py # Hybrid billing system
│   ├── api_client.py     # API client for microservices
│   └── services/         # Original services
└── functions/            # Firebase Functions (unchanged)
```

### Adding New Endpoints

1. Add endpoint to appropriate microservice
2. Update the API Gateway routing if needed
3. Add tests and documentation
4. Update the unified response models if required

### Service Communication

Services communicate via HTTP calls through the API Gateway. Each service is independently deployable and scalable.

## Deployment

### Production Deployment

1. **Docker Deployment**: Use `docker-compose.yml` for container orchestration
2. **Kubernetes**: Convert Docker Compose to Kubernetes manifests
3. **Cloud Run**: Deploy each service as a separate Cloud Run service
4. **Load Balancing**: Use a load balancer for the API Gateway

### Environment Variables

```bash
# API Gateway
VECTORIZED_CPT_MODE=api
VECTORIZED_CPT_API_KEY=your_api_key
VECTORIZED_CPT_GATEWAY_URL=http://localhost:8000

# Google Cloud (for microservices)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id
```

### Database

- **API Keys**: SQLite database (`api_keys.db`)
- **CPT Data**: Firestore (unchanged)
- **Vector Search**: Vertex AI Vector Search (unchanged)

## Monitoring and Logging

### Health Checks

Each service provides a `/health` endpoint:
- Individual service health
- Dependency health (databases, external services)
- Resource utilization

### Logging

Structured logging across all services:
- Request/response logging
- Error tracking
- Performance metrics
- Usage analytics

## Security

### API Key Security

- SHA-256 hashed keys in database
- Bearer token authentication
- Rate limiting per key
- Configurable expiration
- Usage tracking and anomaly detection

### Network Security

- Service-to-service communication via private networks
- HTTPS termination at load balancer
- No direct external access to individual microservices

## Migration Guide

### From Direct Firebase Functions

1. **Set up API Gateway**: Deploy the microservices
2. **Generate API Keys**: Create keys for your applications
3. **Update Client Code**: Switch to API-based calls
4. **Gradual Migration**: Use hybrid mode during transition
5. **Decommission**: Remove Firebase Functions after complete migration

### Testing Migration

```python
# Test both architectures side by side
direct_billing = HybridBilling(use_api_mode=False)
api_billing = HybridBilling(use_api_mode=True, api_key="your_key")

text = "Your medical note..."

# Compare results
direct_result = await direct_billing.process_medical_note(text)
api_result = await api_billing.process_medical_note(text)

# Results should be identical
assert direct_result["step3_cpt_results"] == api_result["step3_cpt_results"]
```

## Support

For questions or issues:
1. Check service logs: `docker-compose logs service_name`
2. Verify health checks: `curl http://localhost:8000/health`
3. Review API documentation: `http://localhost:8000/docs`
4. Check rate limits and usage: `GET /api/v1/usage`

## Performance

### Benchmarks

- **Complete Workflow**: ~2-5 seconds per request
- **CPT Search Only**: ~500ms per request  
- **Text Processing**: ~1-3 seconds per request
- **Medical Coding**: ~1-2 seconds per request

### Scaling

- Each microservice can be scaled independently
- API Gateway handles load balancing
- Database connections are pooled
- Stateless design enables horizontal scaling