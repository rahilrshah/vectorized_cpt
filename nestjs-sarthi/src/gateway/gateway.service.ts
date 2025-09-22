import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';

export interface GatewayConfig {
  serviceId: string;
  serviceName: string;
  version: string;
  healthCheckUrl: string;
  routes: GatewayRoute[];
  metadata: Record<string, any>;
}

export interface GatewayRoute {
  path: string;
  methods: string[];
  rateLimit?: {
    requests: number;
    window: number;
  };
  authentication: boolean;
  authorization?: string[];
  tenantIsolation: boolean;
}

@Injectable()
export class GatewayService implements OnModuleInit {
  private readonly logger = new Logger(GatewayService.name);
  private readonly gatewayUrl: string;
  private readonly authServiceUrl: string;
  private readonly serviceId: string;

  constructor(
    private readonly configService: ConfigService,
    private readonly httpService: HttpService,
  ) {
    this.gatewayUrl = this.configService.get('apiGateway.baseUrl');
    this.authServiceUrl = this.configService.get('apiGateway.authServiceUrl');
    this.serviceId = `sarthi-cpt-vector-service-${this.configService.get('NODE_ENV')}`;
  }

  async onModuleInit() {
    const registrationEnabled = this.configService.get('apiGateway.serviceRegistrationEnabled', true);
    
    if (registrationEnabled && this.gatewayUrl) {
      await this.registerWithGateway();
    } else {
      this.logger.warn('API Gateway registration disabled or gateway URL not configured');
    }
  }

  async registerWithGateway(): Promise<void> {
    try {
      const config = this.buildServiceConfig();
      
      this.logger.log('Registering service with Sarthi API Gateway', {
        serviceId: config.serviceId,
        gatewayUrl: this.gatewayUrl,
        routeCount: config.routes.length,
      });

      const response = await firstValueFrom(
        this.httpService.post(`${this.gatewayUrl}/services/register`, config, {
          timeout: 10000,
          headers: {
            'Content-Type': 'application/json',
            'X-Service-Id': this.serviceId,
            'X-Service-Version': config.version,
          },
        })
      );

      this.logger.log('Successfully registered with API Gateway', {
        serviceId: config.serviceId,
        registrationId: response.data.id,
        status: response.data.status,
      });

      // Start health check reporting
      this.startHealthReporting();

    } catch (error) {
      this.logger.error('Failed to register with API Gateway', {
        error: error.message,
        serviceId: this.serviceId,
        gatewayUrl: this.gatewayUrl,
      });
      
      // Retry registration after delay
      setTimeout(() => this.registerWithGateway(), 30000);
    }
  }

  private buildServiceConfig(): GatewayConfig {
    const baseUrl = this.configService.get('API_BASE_URL', 'http://localhost:8080');
    
    return {
      serviceId: this.serviceId,
      serviceName: 'Sarthi CPT Vector Search Service',
      version: '1.0.0',
      healthCheckUrl: `${baseUrl}/health`,
      routes: this.defineServiceRoutes(),
      metadata: {
        description: 'HIPAA-compliant CPT code search and medical note processing for Sarthi Healthcare Platform',
        owner: 'Sarthi Healthcare Platform',
        environment: this.configService.get('NODE_ENV'),
        // Sarthi service mesh metadata
        serviceMesh: {
          istio: {
            enabled: true,
            version: '1.15+',
            sidecarInjection: true,
            virtualServiceName: 'sarthi-cpt-vector-vs',
            destinationRuleName: 'sarthi-cpt-vector-dr',
            circuitBreaker: {
              maxConnections: 100,
              maxPendingRequests: 50,
              maxRetries: 3,
              consecutiveErrors: 5,
              interval: '30s',
              baseEjectionTime: '30s',
            },
          },
          gateway: {
            name: 'sarthi-healthcare-gateway',
            namespace: 'sarthi-system',
            hosts: ['api.sarthi.healthcare', 'api-staging.sarthi.healthcare'],
          },
        },
        // Sarthi platform integration
        sarthi: {
          platformVersion: '2.0',
          serviceType: 'microservice',
          businessDomain: 'healthcare-coding',
          dataClassification: 'phi-sensitive',
          complianceLevel: 'hipaa-high',
          integrationPoints: [
            'sarthi-api-gateway',
            'sarthi-auth-service',
            'sarthi-audit-service',
            'sarthi-monitoring',
          ],
        },
        compliance: ['HIPAA', 'SOC2', 'GDPR', 'PIPEDA'],
        capabilities: [
          'medical_note_processing',
          'cpt_code_search',
          'vector_similarity_search',
          'multi_tenant_support',
          'audit_logging',
          'phi_protection',
          'bias_detection',
          'explainable_ai',
        ],
        supportedTenants: ['sarthi-main', 'sarthi-clinic-1', 'sarthi-clinic-2', 'sarthi-research'],
        resourceRequirements: {
          cpu: '500m',
          memory: '1Gi',
          storage: '5Gi',
          gpuOptional: false,
        },
        dependencies: [
          'postgresql',
          'redis',
          'google-vertex-ai',
          'google-firestore',
          'sarthi-auth-service',
          'sarthi-audit-service',
        ],
        // AI/ML governance metadata
        aiGovernance: {
          modelType: 'text-embedding',
          modelProvider: 'google-vertex-ai',
          biasMonitoring: true,
          explainabilitySupport: true,
          dataLineageTracking: true,
          performanceThresholds: {
            accuracy: 0.9,
            latency: 500,
            fairnessScore: 0.8,
          },
        },
        // Data governance
        dataGovernance: {
          dataResidency: ['us-central1', 'us-east1'],
          encryptionAtRest: true,
          encryptionInTransit: true,
          retentionPolicy: '7-years',
          deletionPolicy: 'secure-wipe',
          crossBorderTransfer: 'restricted',
        },
      },
    };
  }

  private defineServiceRoutes(): GatewayRoute[] {
    return [
      {
        path: '/sarthi/api/v1/cpt-search/medical-note',
        methods: ['POST'],
        rateLimit: {
          requests: 50,
          window: 60000, // 1 minute
        },
        authentication: true,
        authorization: ['sarthi:cpt:search', 'sarthi:medical:process'],
        tenantIsolation: true,
      },
      {
        path: '/sarthi/api/v1/cpt-search/direct',
        methods: ['POST'],
        rateLimit: {
          requests: 100,
          window: 60000,
        },
        authentication: true,
        authorization: ['sarthi:cpt:search'],
        tenantIsolation: true,
      },
      {
        path: '/sarthi/api/v1/cpt-search/explain',
        methods: ['POST'],
        rateLimit: {
          requests: 30,
          window: 60000,
        },
        authentication: true,
        authorization: ['sarthi:cpt:explain'],
        tenantIsolation: true,
      },
      {
        path: '/sarthi/api/v1/cpt-search/analytics',
        methods: ['GET'],
        rateLimit: {
          requests: 20,
          window: 60000,
        },
        authentication: true,
        authorization: ['sarthi:cpt:analytics'],
        tenantIsolation: true,
      },
      {
        path: '/health',
        methods: ['GET'],
        authentication: false,
        tenantIsolation: false,
      },
      {
        path: '/ready',
        methods: ['GET'],
        authentication: false,
        tenantIsolation: false,
      },
      {
        path: '/metrics',
        methods: ['GET'],
        authentication: false,
        authorization: ['sarthi:monitoring:read'],
        tenantIsolation: false,
      },
      {
        path: '/sarthi/api/docs',
        methods: ['GET'],
        authentication: false,
        tenantIsolation: false,
      },
    ];
  }

  private startHealthReporting(): void {
    const interval = this.configService.get('health.checkInterval', 30000);
    
    setInterval(async () => {
      try {
        await this.reportHealthStatus();
      } catch (error) {
        this.logger.warn('Failed to report health status to gateway', {
          error: error.message,
          serviceId: this.serviceId,
        });
      }
    }, interval);

    this.logger.log('Started health reporting to API Gateway', {
      interval: `${interval}ms`,
      serviceId: this.serviceId,
    });
  }

  private async reportHealthStatus(): Promise<void> {
    if (!this.gatewayUrl) {
      return;
    }

    const healthData = {
      serviceId: this.serviceId,
      status: 'healthy', // This could be dynamic based on actual health checks
      timestamp: new Date().toISOString(),
      metadata: {
        uptime: process.uptime(),
        memoryUsage: process.memoryUsage(),
        version: '1.0.0',
      },
    };

    await firstValueFrom(
      this.httpService.put(
        `${this.gatewayUrl}/services/${this.serviceId}/health`,
        healthData,
        { timeout: 5000 }
      )
    );
  }

  async validateToken(token: string): Promise<any> {
    if (!this.authServiceUrl) {
      throw new Error('Auth service URL not configured');
    }

    try {
      const response = await firstValueFrom(
        this.httpService.post(
          `${this.authServiceUrl}/auth/validate`,
          { token },
          {
            timeout: 5000,
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          }
        )
      );

      return response.data;
    } catch (error) {
      this.logger.warn('Token validation failed', {
        error: error.message,
        authServiceUrl: this.authServiceUrl,
      });
      throw new Error('Invalid or expired token');
    }
  }

  async refreshServiceRegistration(): Promise<void> {
    this.logger.log('Refreshing service registration with API Gateway');
    await this.registerWithGateway();
  }

  async deregisterFromGateway(): Promise<void> {
    if (!this.gatewayUrl) {
      return;
    }

    try {
      await firstValueFrom(
        this.httpService.delete(`${this.gatewayUrl}/services/${this.serviceId}`, {
          timeout: 10000,
        })
      );

      this.logger.log('Successfully deregistered from API Gateway', {
        serviceId: this.serviceId,
      });
    } catch (error) {
      this.logger.error('Failed to deregister from API Gateway', {
        error: error.message,
        serviceId: this.serviceId,
      });
    }
  }

  getServiceMetadata(): Record<string, any> {
    return {
      serviceId: this.serviceId,
      version: '1.0.0',
      environment: this.configService.get('NODE_ENV'),
      registeredAt: new Date().toISOString(),
      gatewayUrl: this.gatewayUrl,
      healthCheckUrl: `${this.configService.get('API_BASE_URL')}/health`,
    };
  }
}