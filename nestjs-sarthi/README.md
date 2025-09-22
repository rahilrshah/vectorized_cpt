# Sarthi CPT Vector Service

A HIPAA-compliant microservice for CPT code search and medical note processing, designed for integration with the Sarthi Healthcare Platform.

## 🏥 Overview

This NestJS-based microservice transforms medical notes into relevant CPT codes using advanced AI and vector similarity search. It provides enterprise-grade features including multi-tenancy, audit logging, encryption, and comprehensive monitoring.

## ✨ Key Features

### 🔒 Security & Compliance
- **HIPAA Compliant**: Full audit trails, PHI protection, encryption at rest and in transit
- **Multi-Tenant Architecture**: Complete tenant isolation with row-level security
- **End-to-End Encryption**: Google Cloud KMS integration for sensitive data
- **JWT Authentication**: Secure API access with role-based permissions

### 🚀 Performance & Scalability
- **Vector Search Engine**: High-performance similarity matching using Vertex AI
- **Redis Caching**: Optimized response times for common queries
- **PostgreSQL + Firestore**: Hybrid database architecture for optimal performance
- **Rate Limiting**: Configurable per-tenant request throttling

### 📊 Monitoring & Observability
- **Comprehensive Logging**: Structured logs with Cloud Logging integration
- **Prometheus Metrics**: Real-time performance monitoring
- **Distributed Tracing**: Full request lifecycle tracking
- **Health Checks**: Kubernetes-ready health endpoints

### 🏗️ Enterprise Integration
- **API Gateway Ready**: Seamless integration with Sarthi platform
- **OpenAPI Documentation**: Auto-generated API docs with Swagger
- **Containerized Deployment**: Docker and Kubernetes support
- **CI/CD Pipeline**: Automated testing and deployment

## 🛠️ Technology Stack

- **Runtime**: Node.js 18+ with TypeScript
- **Framework**: NestJS with Express
- **Database**: PostgreSQL + Google Firestore
- **Cache**: Redis
- **AI/ML**: Google Vertex AI (Embeddings + Gemini)
- **Security**: Google Cloud KMS, JWT, bcrypt
- **Monitoring**: Prometheus, OpenTelemetry, Winston
- **Container**: Docker with multi-stage builds

## 📋 Prerequisites

- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Google Cloud Platform account
- Docker (for containerized deployment)

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd nestjs-sarthi

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Configure your environment variables
nano .env.local
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb sarthi_cpt

# Run migrations
npm run migration:run

# (Optional) Seed with sample data
npm run seed
```

### 3. Development Mode

```bash
# Start development server
npm run start:dev

# View API documentation
open http://localhost:8080/api/docs
```

### 4. Production Deployment

```bash
# Build the application
npm run build

# Start production server
npm run start:prod

# Or use Docker
docker build -t cpt-vector-service .
docker run -p 8080:8080 --env-file .env cpt-vector-service
```

## 📚 API Documentation

### Medical Note Processing

```bash
POST /api/v1/cpt-search/medical-note
Content-Type: application/json
Authorization: Bearer <jwt-token>
X-Tenant-Id: <tenant-id>

{
  "text": "Patient underwent arthroscopic knee surgery to repair torn meniscus in right knee",
  "maxResults": 20,
  "similarityThreshold": 0.7
}
```

### Direct CPT Search

```bash
POST /api/v1/cpt-search/direct
Content-Type: application/json
Authorization: Bearer <jwt-token>
X-Tenant-Id: <tenant-id>

{
  "query": "arthroscopic meniscus repair",
  "maxResults": 10,
  "categories": ["Surgery"]
}
```

### Health Monitoring

```bash
# Health check
GET /health

# Ready check
GET /ready

# Metrics (Prometheus format)
GET /metrics
```

## 🔧 Configuration

### Environment Variables

Key configuration options:

```env
# Core Settings
NODE_ENV=production
PORT=8080
GCP_PROJECT_ID=sarthi-healthcare-prod

# Database
DB_HOST=your-postgres-host
DB_NAME=sarthi_cpt
DB_USERNAME=cpt_service
DB_PASSWORD=secure_password

# Security
JWT_SECRET=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key
HIPAA_COMPLIANCE_ENABLED=true

# Multi-Tenancy
MULTI_TENANT_ENABLED=true
TENANT_HEADER=X-Tenant-Id
```

See `.env.example` for complete configuration options.

### Multi-Tenant Setup

1. **Create Tenant Configuration**:
```sql
INSERT INTO tenant_configs (
  tenant_id, tenant_name, admin_email, created_by
) VALUES (
  'your-clinic', 'Your Clinic Name', 'admin@yourclinic.com', 'system'
);
```

2. **Configure API Client**:
```typescript
const headers = {
  'Authorization': 'Bearer ' + jwt_token,
  'X-Tenant-Id': 'your-clinic',
  'Content-Type': 'application/json'
};
```

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Gateway   │───▶│  CPT Vector API  │───▶│   Vertex AI     │
│   (Sarthi)      │    │   (NestJS)       │    │   (Embeddings)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   PostgreSQL     │    │   Firestore     │
                       │   (Primary)      │    │   (Real-time)   │
                       └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │      Redis       │
                       │     (Cache)      │
                       └──────────────────┘
```

### Key Components

- **Controllers**: Handle HTTP requests and responses
- **Services**: Business logic and data processing
- **Middleware**: Security, logging, tenant isolation
- **Guards**: Authentication and authorization
- **Interceptors**: Audit logging and error handling

## 🧪 Testing

```bash
# Unit tests
npm run test

# Integration tests
npm run test:e2e

# Test coverage
npm run test:cov

# Load testing
npm run test:load
```

## 📊 Monitoring

### Metrics Available

- **Request Metrics**: Count, duration, status codes
- **CPT Search Metrics**: Search performance, accuracy
- **Database Metrics**: Connection pool, query performance
- **Cache Metrics**: Hit rates, memory usage
- **Tenant Metrics**: Per-tenant usage and performance

### Log Levels

- **ERROR**: System errors, failed requests
- **WARN**: Performance issues, security events
- **INFO**: Normal operations, audit events
- **DEBUG**: Detailed debugging information

## 🔐 Security Features

### HIPAA Compliance

- **Audit Logging**: Every action logged with 7-year retention
- **PHI Protection**: Automatic detection and redaction
- **Encryption**: All sensitive data encrypted at rest
- **Access Control**: Role-based permissions with tenant isolation

### Security Headers

- Content Security Policy (CSP)
- X-Frame-Options (Clickjacking protection)
- X-Content-Type-Options (MIME sniffing protection)
- Strict Transport Security (HTTPS enforcement)

## 🐳 Docker Deployment

### Building the Image

```bash
# Build production image
docker build -t cpt-vector-service:latest .

# Build with specific tag
docker build -t gcr.io/sarthi-healthcare-prod/cpt-vector-service:v1.0.0 .
```

### Running with Docker Compose

```yaml
version: '3.8'
services:
  cpt-service:
    image: cpt-vector-service:latest
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
      - DB_HOST=postgres
    depends_on:
      - postgres
      - redis
```

## ☸️ Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cpt-vector-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cpt-vector-service
  template:
    metadata:
      labels:
        app: cpt-vector-service
    spec:
      containers:
      - name: cpt-service
        image: gcr.io/sarthi-healthcare-prod/cpt-vector-service:v1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: NODE_ENV
          value: "production"
        - name: PORT
          value: "8080"
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check database credentials and connectivity
   - Verify PostgreSQL is running and accessible
   - Check firewall settings

2. **Vector Search Not Working**
   - Verify Vertex AI credentials and permissions
   - Check if vector embeddings are populated
   - Validate embedding dimensions (should be 768)

3. **High Memory Usage**
   - Check Redis memory usage and eviction policies
   - Monitor vector embedding cache size
   - Review application memory leaks

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=debug npm run start:dev

# Enable SQL query logging
DB_LOGGING=true npm run start:dev
```

## 📈 Performance Optimization

### Recommended Settings

- **Production**: 3+ replicas with horizontal pod autoscaling
- **Database**: Connection pooling with 20 max connections
- **Cache**: Redis with 2GB memory and LRU eviction
- **Rate Limiting**: 100 requests/minute per tenant

### Monitoring Alerts

Set up alerts for:
- Response time > 500ms (95th percentile)
- Error rate > 1%
- Memory usage > 80%
- Database connection pool > 80%

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software owned by Sarthi Healthcare Platform.

## 📞 Support

For technical support and questions:
- **Documentation**: [Sarthi Developer Portal](https://docs.sarthi.healthcare)
- **Support Email**: support@sarthi.healthcare
- **Emergency Hotline**: Available 24/7 for production issues

---

**Built with ❤️ for Healthcare Excellence**