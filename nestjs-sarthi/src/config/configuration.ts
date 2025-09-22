import { registerAs } from '@nestjs/config';

export default registerAs('config', () => ({
  // Environment
  nodeEnv: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT, 10) || 8080,
  apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8080',
  
  // Google Cloud Platform
  gcp: {
    projectId: process.env.GCP_PROJECT_ID || 'sarthi-healthcare-prod',
    location: process.env.GCP_LOCATION || 'us-central1',
    serviceAccountKey: process.env.GCP_SERVICE_ACCOUNT_KEY,
  },
  
  // Database configuration
  database: {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT, 10) || 5432,
    username: process.env.DB_USERNAME || 'cpt_service',
    password: process.env.DB_PASSWORD,
    name: process.env.DB_NAME || 'sarthi_cpt',
    logging: process.env.DB_LOGGING === 'true',
    sslCert: process.env.DB_SSL_CERT,
  },
  
  // Redis configuration
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT, 10) || 6379,
    password: process.env.REDIS_PASSWORD,
    database: parseInt(process.env.REDIS_DATABASE, 10) || 0,
    ttl: parseInt(process.env.REDIS_TTL, 10) || 3600, // 1 hour
    maxItems: parseInt(process.env.REDIS_MAX_ITEMS, 10) || 1000,
  },
  
  // Firestore configuration
  firestore: {
    projectId: process.env.FIRESTORE_PROJECT_ID || process.env.GCP_PROJECT_ID,
    collection: process.env.FIRESTORE_COLLECTION || 'Vectorized_CPT_Test',
    vectorField: process.env.FIRESTORE_VECTOR_FIELD || 'vector',
    credentialsPath: process.env.FIRESTORE_CREDENTIALS_PATH,
  },
  
  // Vertex AI configuration
  vertexAi: {
    projectId: process.env.VERTEX_PROJECT_ID || process.env.GCP_PROJECT_ID,
    location: process.env.VERTEX_LOCATION || process.env.GCP_LOCATION,
    endpointId: process.env.VERTEX_ENDPOINT_ID,
    indexId: process.env.VERTEX_INDEX_ID,
    embeddingModel: process.env.EMBEDDING_MODEL || 'text-embedding-004',
    generativeModel: process.env.GENERATIVE_MODEL || 'gemini-2.0-flash-exp',
    dimensions: parseInt(process.env.EMBEDDING_DIMENSIONS, 10) || 768,
  },
  
  // Security configuration
  security: {
    jwtSecret: process.env.JWT_SECRET,
    jwtExpiresIn: process.env.JWT_EXPIRES_IN || '24h',
    encryptionKey: process.env.ENCRYPTION_KEY,
    kmsKeyRing: process.env.KMS_KEY_RING || 'sarthi-phi',
    kmsKey: process.env.KMS_KEY || 'cpt-service-key',
    bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS, 10) || 12,
  },
  
  // HIPAA compliance
  hipaa: {
    enabled: process.env.HIPAA_COMPLIANCE_ENABLED !== 'false',
    auditRetentionDays: parseInt(process.env.AUDIT_RETENTION_DAYS, 10) || 2555, // 7 years
    phiRedactionEnabled: process.env.PHI_REDACTION_ENABLED !== 'false',
    encryptionAtRest: process.env.ENCRYPTION_AT_REST_ENABLED !== 'false',
    dataResidency: process.env.DATA_RESIDENCY || 'us-central1',
  },
  
  // Rate limiting
  rateLimit: {
    ttl: parseInt(process.env.RATE_LIMIT_TTL, 10) || 60000, // 1 minute
    limit: parseInt(process.env.RATE_LIMIT_REQUESTS, 10) || 100, // 100 requests per minute
    skipSuccessfulRequests: process.env.RATE_LIMIT_SKIP_SUCCESS === 'true',
    skipFailedRequests: process.env.RATE_LIMIT_SKIP_FAILED === 'true',
  },
  
  // Monitoring and observability
  monitoring: {
    enableMetrics: process.env.ENABLE_METRICS !== 'false',
    metricsPort: parseInt(process.env.METRICS_PORT, 10) || 9090,
    enableTracing: process.env.ENABLE_TRACING !== 'false',
    tracingSampleRate: parseFloat(process.env.TRACING_SAMPLE_RATE) || 0.1,
    logLevel: process.env.LOG_LEVEL || 'info',
    cloudLoggingEnabled: process.env.CLOUD_LOGGING_ENABLED !== 'false',
  },
  
  // Sarthi API Gateway integration
  apiGateway: {
    baseUrl: process.env.SARTHI_API_GATEWAY_URL || process.env.API_GATEWAY_URL,
    authServiceUrl: process.env.SARTHI_AUTH_SERVICE_URL || process.env.AUTH_SERVICE_URL,
    allowedOrigins: process.env.ALLOWED_ORIGINS,
    serviceRegistrationEnabled: process.env.SERVICE_REGISTRATION_ENABLED !== 'false',
    sarthiNamespace: process.env.SARTHI_NAMESPACE || 'sarthi-system',
    sarthiServiceMesh: process.env.SARTHI_SERVICE_MESH_ENABLED !== 'false',
  },

  // Sarthi platform configuration
  sarthi: {
    platformVersion: process.env.SARTHI_PLATFORM_VERSION || '2.0',
    servicePrefix: process.env.SARTHI_SERVICE_PREFIX || 'sarthi',
    businessDomain: process.env.SARTHI_BUSINESS_DOMAIN || 'healthcare-coding',
    complianceLevel: process.env.SARTHI_COMPLIANCE_LEVEL || 'hipaa-high',
    dataClassification: process.env.SARTHI_DATA_CLASSIFICATION || 'phi-sensitive',
    crossBorderEnabled: process.env.SARTHI_CROSS_BORDER_ENABLED === 'true',
    biasDetectionEnabled: process.env.SARTHI_BIAS_DETECTION_ENABLED !== 'false',
  },
  
  // Tenant configuration
  multiTenant: {
    enabled: process.env.MULTI_TENANT_ENABLED !== 'false',
    defaultTenant: process.env.DEFAULT_TENANT_ID || 'default',
    tenantHeader: process.env.TENANT_HEADER || 'X-Tenant-Id',
    tenantValidationEnabled: process.env.TENANT_VALIDATION_ENABLED !== 'false',
  },
  
  // Vector search configuration
  vectorSearch: {
    similarityThreshold: parseFloat(process.env.SIMILARITY_THRESHOLD) || 0.70,
    maxResults: parseInt(process.env.MAX_SEARCH_RESULTS, 10) || 20,
    cacheEnabled: process.env.VECTOR_CACHE_ENABLED !== 'false',
    cacheTtl: parseInt(process.env.VECTOR_CACHE_TTL, 10) || 1800, // 30 minutes
    batchSize: parseInt(process.env.VECTOR_BATCH_SIZE, 10) || 32,
  },
  
  // Performance tuning
  performance: {
    requestTimeout: parseInt(process.env.REQUEST_TIMEOUT, 10) || 30000, // 30 seconds
    keepAliveTimeout: parseInt(process.env.KEEP_ALIVE_TIMEOUT, 10) || 5000,
    bodyLimit: process.env.BODY_LIMIT || '10mb',
    compressionEnabled: process.env.COMPRESSION_ENABLED !== 'false',
  },
  
  // Health check configuration
  health: {
    checkInterval: parseInt(process.env.HEALTH_CHECK_INTERVAL, 10) || 30000, // 30 seconds
    timeout: parseInt(process.env.HEALTH_CHECK_TIMEOUT, 10) || 5000, // 5 seconds
    retries: parseInt(process.env.HEALTH_CHECK_RETRIES, 10) || 3,
  },
}));