import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { register, Counter, Histogram, Gauge, collectDefaultMetrics } from 'prom-client';

@Injectable()
export class MetricsService {
  private readonly logger = new Logger(MetricsService.name);
  
  // HTTP Request Metrics
  private readonly httpRequestsTotal: Counter<string>;
  private readonly httpRequestDuration: Histogram<string>;
  
  // CPT Search Metrics
  private readonly cptSearchTotal: Counter<string>;
  private readonly cptSearchDuration: Histogram<string>;
  private readonly cptSearchResults: Histogram<string>;
  private readonly cptSearchAccuracy: Histogram<string>;
  
  // Database Metrics
  private readonly dbConnectionsActive: Gauge<string>;
  private readonly dbQueryDuration: Histogram<string>;
  private readonly dbQueryErrors: Counter<string>;
  
  // Cache Metrics
  private readonly cacheHitsTotal: Counter<string>;
  private readonly cacheMissesTotal: Counter<string>;
  private readonly cacheSize: Gauge<string>;
  
  // Vector Engine Metrics
  private readonly vectorEmbeddingDuration: Histogram<string>;
  private readonly vectorSimilarityDuration: Histogram<string>;
  private readonly vectorCacheHits: Counter<string>;
  
  // Tenant Metrics
  private readonly tenantRequestsTotal: Counter<string>;
  private readonly tenantActiveUsers: Gauge<string>;
  
  // Security Metrics
  private readonly authFailures: Counter<string>;
  private readonly securityViolations: Counter<string>;
  private readonly phiAccessEvents: Counter<string>;
  
  // System Metrics
  private readonly memoryUsage: Gauge<string>;
  private readonly cpuUsage: Gauge<string>;

  constructor(private readonly configService: ConfigService) {
    // Enable default metrics collection
    collectDefaultMetrics({ 
      prefix: 'cpt_vector_',
      gcDurationBuckets: [0.001, 0.01, 0.1, 1, 2, 5]
    });

    // HTTP Request Metrics
    this.httpRequestsTotal = new Counter({
      name: 'cpt_vector_http_requests_total',
      help: 'Total number of HTTP requests',
      labelNames: ['method', 'route', 'status_code', 'tenant_id'],
      registers: [register],
    });

    this.httpRequestDuration = new Histogram({
      name: 'cpt_vector_http_request_duration_seconds',
      help: 'Duration of HTTP requests in seconds',
      labelNames: ['method', 'route', 'status_code', 'tenant_id'],
      buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10],
      registers: [register],
    });

    // CPT Search Metrics
    this.cptSearchTotal = new Counter({
      name: 'cpt_vector_search_total',
      help: 'Total number of CPT searches performed',
      labelNames: ['tenant_id', 'search_type', 'success'],
      registers: [register],
    });

    this.cptSearchDuration = new Histogram({
      name: 'cpt_vector_search_duration_seconds',
      help: 'Duration of CPT searches in seconds',
      labelNames: ['tenant_id', 'search_type'],
      buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10, 30],
      registers: [register],
    });

    this.cptSearchResults = new Histogram({
      name: 'cpt_vector_search_results_count',
      help: 'Number of results returned by CPT searches',
      labelNames: ['tenant_id', 'search_type'],
      buckets: [0, 1, 5, 10, 20, 50, 100],
      registers: [register],
    });

    this.cptSearchAccuracy = new Histogram({
      name: 'cpt_vector_search_accuracy_score',
      help: 'Average similarity score of top CPT search results',
      labelNames: ['tenant_id'],
      buckets: [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0],
      registers: [register],
    });

    // Database Metrics
    this.dbConnectionsActive = new Gauge({
      name: 'cpt_vector_db_connections_active',
      help: 'Number of active database connections',
      registers: [register],
    });

    this.dbQueryDuration = new Histogram({
      name: 'cpt_vector_db_query_duration_seconds',
      help: 'Duration of database queries in seconds',
      labelNames: ['query_type', 'tenant_id'],
      buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 2],
      registers: [register],
    });

    this.dbQueryErrors = new Counter({
      name: 'cpt_vector_db_query_errors_total',
      help: 'Total number of database query errors',
      labelNames: ['error_type', 'tenant_id'],
      registers: [register],
    });

    // Cache Metrics
    this.cacheHitsTotal = new Counter({
      name: 'cpt_vector_cache_hits_total',
      help: 'Total number of cache hits',
      labelNames: ['cache_type', 'tenant_id'],
      registers: [register],
    });

    this.cacheMissesTotal = new Counter({
      name: 'cpt_vector_cache_misses_total',
      help: 'Total number of cache misses',
      labelNames: ['cache_type', 'tenant_id'],
      registers: [register],
    });

    this.cacheSize = new Gauge({
      name: 'cpt_vector_cache_size_bytes',
      help: 'Current cache size in bytes',
      labelNames: ['cache_type'],
      registers: [register],
    });

    // Vector Engine Metrics
    this.vectorEmbeddingDuration = new Histogram({
      name: 'cpt_vector_embedding_duration_seconds',
      help: 'Duration of vector embedding generation in seconds',
      labelNames: ['model_type', 'tenant_id'],
      buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10],
      registers: [register],
    });

    this.vectorSimilarityDuration = new Histogram({
      name: 'cpt_vector_similarity_duration_seconds',
      help: 'Duration of vector similarity calculations in seconds',
      labelNames: ['tenant_id'],
      buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1],
      registers: [register],
    });

    this.vectorCacheHits = new Counter({
      name: 'cpt_vector_embedding_cache_hits_total',
      help: 'Total number of vector embedding cache hits',
      labelNames: ['tenant_id'],
      registers: [register],
    });

    // Tenant Metrics
    this.tenantRequestsTotal = new Counter({
      name: 'cpt_vector_tenant_requests_total',
      help: 'Total requests per tenant',
      labelNames: ['tenant_id', 'endpoint'],
      registers: [register],
    });

    this.tenantActiveUsers = new Gauge({
      name: 'cpt_vector_tenant_active_users',
      help: 'Number of active users per tenant',
      labelNames: ['tenant_id'],
      registers: [register],
    });

    // Security Metrics
    this.authFailures = new Counter({
      name: 'cpt_vector_auth_failures_total',
      help: 'Total number of authentication failures',
      labelNames: ['failure_reason', 'tenant_id'],
      registers: [register],
    });

    this.securityViolations = new Counter({
      name: 'cpt_vector_security_violations_total',
      help: 'Total number of security violations detected',
      labelNames: ['violation_type', 'severity', 'tenant_id'],
      registers: [register],
    });

    this.phiAccessEvents = new Counter({
      name: 'cpt_vector_phi_access_total',
      help: 'Total number of PHI access events',
      labelNames: ['tenant_id', 'access_type'],
      registers: [register],
    });

    // System Metrics
    this.memoryUsage = new Gauge({
      name: 'cpt_vector_memory_usage_bytes',
      help: 'Current memory usage in bytes',
      registers: [register],
    });

    this.cpuUsage = new Gauge({
      name: 'cpt_vector_cpu_usage_percent',
      help: 'Current CPU usage percentage',
      registers: [register],
    });

    this.logger.log('Metrics service initialized with Prometheus collectors');
  }

  // HTTP Request Metrics
  recordHttpRequest(method: string, route: string, statusCode: number, duration: number, tenantId?: string) {
    const labels = {
      method,
      route: this.sanitizeRoute(route),
      status_code: statusCode.toString(),
      tenant_id: tenantId || 'unknown',
    };

    this.httpRequestsTotal.inc(labels);
    this.httpRequestDuration.observe(labels, duration / 1000); // Convert to seconds
  }

  // CPT Search Metrics
  recordCptSearch(tenantId: string, searchType: string, duration: number, resultCount: number, success: boolean, avgSimilarity?: number) {
    const searchLabels = {
      tenant_id: tenantId,
      search_type: searchType,
    };

    const successLabels = {
      ...searchLabels,
      success: success.toString(),
    };

    this.cptSearchTotal.inc(successLabels);
    this.cptSearchDuration.observe(searchLabels, duration / 1000);
    this.cptSearchResults.observe(searchLabels, resultCount);

    if (avgSimilarity !== undefined) {
      this.cptSearchAccuracy.observe({ tenant_id: tenantId }, avgSimilarity);
    }

    // Record tenant-specific request
    this.tenantRequestsTotal.inc({
      tenant_id: tenantId,
      endpoint: 'cpt_search',
    });
  }

  // Database Metrics
  recordDbQuery(queryType: string, duration: number, tenantId?: string) {
    this.dbQueryDuration.observe({
      query_type: queryType,
      tenant_id: tenantId || 'system',
    }, duration / 1000);
  }

  recordDbError(errorType: string, tenantId?: string) {
    this.dbQueryErrors.inc({
      error_type: errorType,
      tenant_id: tenantId || 'system',
    });
  }

  updateDbConnections(activeConnections: number) {
    this.dbConnectionsActive.set(activeConnections);
  }

  // Cache Metrics
  recordCacheHit(cacheType: string, tenantId?: string) {
    this.cacheHitsTotal.inc({
      cache_type: cacheType,
      tenant_id: tenantId || 'system',
    });
  }

  recordCacheMiss(cacheType: string, tenantId?: string) {
    this.cacheMissesTotal.inc({
      cache_type: cacheType,
      tenant_id: tenantId || 'system',
    });
  }

  updateCacheSize(cacheType: string, sizeBytes: number) {
    this.cacheSize.set({ cache_type: cacheType }, sizeBytes);
  }

  // Vector Engine Metrics
  recordVectorEmbedding(modelType: string, duration: number, tenantId?: string) {
    this.vectorEmbeddingDuration.observe({
      model_type: modelType,
      tenant_id: tenantId || 'system',
    }, duration / 1000);
  }

  recordVectorSimilarity(duration: number, tenantId?: string) {
    this.vectorSimilarityDuration.observe({
      tenant_id: tenantId || 'system',
    }, duration / 1000);
  }

  recordVectorCacheHit(tenantId?: string) {
    this.vectorCacheHits.inc({
      tenant_id: tenantId || 'system',
    });
  }

  // Security Metrics
  recordAuthFailure(reason: string, tenantId?: string) {
    this.authFailures.inc({
      failure_reason: reason,
      tenant_id: tenantId || 'unknown',
    });
  }

  recordSecurityViolation(violationType: string, severity: string, tenantId?: string) {
    this.securityViolations.inc({
      violation_type: violationType,
      severity,
      tenant_id: tenantId || 'unknown',
    });
  }

  recordPhiAccess(tenantId: string, accessType: string) {
    this.phiAccessEvents.inc({
      tenant_id: tenantId,
      access_type: accessType,
    });
  }

  // System Metrics
  updateSystemMetrics() {
    const memUsage = process.memoryUsage();
    this.memoryUsage.set(memUsage.heapUsed);

    // CPU usage calculation (simplified)
    const cpuUsage = process.cpuUsage();
    const totalCpuTime = cpuUsage.user + cpuUsage.system;
    this.cpuUsage.set(totalCpuTime / 1000000); // Convert to percentage approximation
  }

  // Tenant Metrics
  updateActiveUsers(tenantId: string, activeUserCount: number) {
    this.tenantActiveUsers.set({ tenant_id: tenantId }, activeUserCount);
  }

  // Utility Methods
  getMetrics(): string {
    return register.metrics();
  }

  getMetricsContentType(): string {
    return register.contentType;
  }

  private sanitizeRoute(route: string): string {
    // Remove dynamic path parameters to group similar routes
    return route
      .replace(/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, '/:id')
      .replace(/\/\d+/g, '/:id')
      .replace(/\/[^\/]+\?/g, '/:param?');
  }

  // Health Check Integration
  async getHealthMetrics(): Promise<Record<string, any>> {
    const metrics = await register.getSingleMetricAsString('cpt_vector_http_requests_total');
    const dbConnections = await register.getSingleMetricAsString('cpt_vector_db_connections_active');
    
    return {
      httpRequestsTotal: metrics,
      activeDbConnections: dbConnections,
      memoryUsage: process.memoryUsage(),
      uptime: process.uptime(),
    };
  }

  // Performance Monitoring
  startPerformanceMonitoring() {
    // Update system metrics every 30 seconds
    setInterval(() => {
      this.updateSystemMetrics();
    }, 30000);

    this.logger.log('Performance monitoring started');
  }
}