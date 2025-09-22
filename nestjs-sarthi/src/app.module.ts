import { Module, MiddlewareConsumer, NestModule } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ThrottlerModule } from '@nestjs/throttler';
import { TerminusModule } from '@nestjs/terminus';
import { CacheModule } from '@nestjs/cache-manager';
import { redisStore } from 'cache-manager-redis-store';

// Configuration
import configuration from './config/configuration';

// Core modules
import { CptSearchModule } from './cpt-search/cpt-search.module';
import { VectorEngineModule } from './vector-engine/vector-engine.module';
import { SecurityModule } from './security/security.module';
import { AuditModule } from './audit/audit.module';
import { MonitoringModule } from './monitoring/monitoring.module';
import { HealthModule } from './health/health.module';
import { DataGovernanceModule } from './data-governance/data-governance.module';
import { AIGovernanceModule } from './ai-governance/ai-governance.module';
import { ComplianceModule } from './compliance/compliance.module';

// Common components
import { TenantMiddleware } from './common/middleware/tenant.middleware';
import { RequestLoggerMiddleware } from './common/middleware/request-logger.middleware';
import { SecurityMiddleware } from './common/middleware/security.middleware';

// Database entities
import { CptCode } from './database/entities/cpt-code.entity';
import { AuditLog } from './database/entities/audit-log.entity';
import { TenantConfig } from './database/entities/tenant-config.entity';

@Module({
  imports: [
    // Configuration management
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
      envFilePath: ['.env.local', '.env'],
      expandVariables: true,
    }),
    
    // Database connection
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (configService: ConfigService) => ({
        type: 'postgres',
        host: configService.get('database.host'),
        port: configService.get('database.port'),
        username: configService.get('database.username'),
        password: configService.get('database.password'),
        database: configService.get('database.name'),
        entities: [CptCode, AuditLog, TenantConfig],
        migrations: ['dist/database/migrations/*{.ts,.js}'],
        synchronize: configService.get('NODE_ENV') === 'development',
        logging: configService.get('database.logging'),
        ssl: configService.get('NODE_ENV') === 'production' ? {
          rejectUnauthorized: false,
          ca: configService.get('database.sslCert'),
        } : false,
        extra: {
          connectionTimeoutMillis: 5000,
          idleTimeoutMillis: 30000,
          max: 20,
        },
      }),
      inject: [ConfigService],
    }),
    
    // Redis cache
    CacheModule.registerAsync({
      imports: [ConfigModule],
      useFactory: async (configService: ConfigService) => ({
        store: redisStore,
        host: configService.get('redis.host'),
        port: configService.get('redis.port'),
        password: configService.get('redis.password'),
        db: configService.get('redis.database'),
        ttl: configService.get('redis.ttl'),
        max: configService.get('redis.maxItems'),
        no_ready_check: true,
        retry_strategy: (options) => {
          if (options.error && options.error.code === 'ECONNREFUSED') {
            return new Error('Redis server refused connection');
          }
          if (options.total_retry_time > 1000 * 60 * 60) {
            return new Error('Redis retry time exhausted');
          }
          if (options.attempt > 10) {
            return undefined;
          }
          return Math.min(options.attempt * 100, 3000);
        },
      }),
      inject: [ConfigService],
      isGlobal: true,
    }),
    
    // Rate limiting
    ThrottlerModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (configService: ConfigService) => ({
        throttlers: [{
          ttl: configService.get('rateLimit.ttl', 60000), // 1 minute
          limit: configService.get('rateLimit.limit', 100), // 100 requests per minute
        }],
        skipIf: (context) => {
          // Skip rate limiting for health checks
          const request = context.switchToHttp().getRequest();
          return request.url.includes('/health') || request.url.includes('/metrics');
        },
      }),
      inject: [ConfigService],
    }),
    
    // Health monitoring
    TerminusModule,
    
    // Feature modules
    CptSearchModule,
    VectorEngineModule,
    SecurityModule,
    AuditModule,
    MonitoringModule,
    HealthModule,
    DataGovernanceModule,
    AIGovernanceModule,
    ComplianceModule,
  ],
  controllers: [],
  providers: [],
})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    // Apply middleware in order of execution
    consumer
      .apply(
        RequestLoggerMiddleware,
        SecurityMiddleware,
        TenantMiddleware,
      )
      .forRoutes('*');
  }
}