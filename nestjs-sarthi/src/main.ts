import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { ConfigService } from '@nestjs/config';
import helmet from 'helmet';
import compression from 'compression';
import { AppModule } from './app.module';
import { TenantMiddleware } from './common/middleware/tenant.middleware';
import { AuditInterceptor } from './common/interceptors/audit.interceptor';
import { ErrorInterceptor } from './common/interceptors/error.interceptor';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  
  const app = await NestFactory.create(AppModule);
  const configService = app.get(ConfigService);
  
  // Security middleware
  app.use(helmet({
    hsts: {
      maxAge: 31536000,
      includeSubDomains: true,
      preload: true
    },
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", "data:", "https:"],
        connectSrc: ["'self'"]
      }
    }
  }));
  
  app.use(compression());
  
  // Global validation pipe with HIPAA-compliant error messages
  app.useGlobalPipes(new ValidationPipe({
    whitelist: true,
    forbidNonWhitelisted: true,
    transform: true,
    disableErrorMessages: configService.get('NODE_ENV') === 'production',
    exceptionFactory: (errors) => {
      logger.warn('Validation failed', { errors: errors.map(e => e.constraints) });
      throw new Error('Invalid request parameters');
    }
  }));
  
  // Global interceptors
  app.useGlobalInterceptors(
    new AuditInterceptor(),
    new ErrorInterceptor()
  );
  
  // Sarthi API prefix
  app.setGlobalPrefix('sarthi/api/v1');
  
  // CORS for API Gateway integration
  app.enableCors({
    origin: configService.get('ALLOWED_ORIGINS')?.split(',') || ['http://localhost:3000'],
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Tenant-Id', 'X-Correlation-Id'],
    credentials: true
  });
  
  // Swagger documentation (disabled in production)
  if (configService.get('NODE_ENV') !== 'production') {
    const config = new DocumentBuilder()
      .setTitle('Sarthi CPT Vector Search API')
      .setDescription('HIPAA-compliant CPT code search microservice for Sarthi Healthcare Platform with AI governance and bias detection')
      .setVersion('1.0.0')
      .addBearerAuth()
      .addTag('cpt-search', 'CPT code search operations')
      .addTag('explainability', 'AI model explainability features')
      .addTag('analytics', 'Search analytics and insights')
      .addTag('health', 'Health monitoring endpoints')
      .addTag('audit', 'Audit and compliance endpoints')
      .addServer(configService.get('API_BASE_URL', 'http://localhost:8080'), 'Development server')
      .addServer('https://api.sarthi.healthcare', 'Production server')
      .addServer('https://api-staging.sarthi.healthcare', 'Staging server')
      .build();
    
    const document = SwaggerModule.createDocument(app, config);
    SwaggerModule.setup('sarthi/api/docs', app, document, {
      swaggerOptions: {
        persistAuthorization: true,
        defaultModelExpandDepth: 2,
        defaultModelsExpandDepth: 1,
        tagsSorter: 'alpha',
        operationsSorter: 'alpha'
      }
    });
    
    logger.log('📚 Sarthi API documentation available at /sarthi/api/docs');
  }
  
  const port = configService.get('PORT', 8080);
  
  await app.listen(port, '0.0.0.0');
  
  logger.log(`🚀 CPT Vector Service running on port ${port}`);
  logger.log(`🏥 Sarthi Healthcare Platform integration active`);
  logger.log(`🔒 HIPAA compliance mode: ${configService.get('HIPAA_COMPLIANCE_ENABLED', 'true')}`);
  logger.log(`🌍 Environment: ${configService.get('NODE_ENV', 'development')}`);
}

bootstrap().catch((error) => {
  const logger = new Logger('Bootstrap');
  logger.error('Failed to start application', error);
  process.exit(1);
});