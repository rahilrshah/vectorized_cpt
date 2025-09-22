import { Injectable, NestMiddleware, Logger } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';

export interface EnhancedRequest extends Request {
  requestId?: string;
  startTime?: number;
}

@Injectable()
export class RequestLoggerMiddleware implements NestMiddleware {
  private readonly logger = new Logger('RequestLogger');

  use(req: EnhancedRequest, res: Response, next: NextFunction) {
    // Generate unique request ID
    req.requestId = req.headers['x-correlation-id'] as string || uuidv4();
    req.startTime = Date.now();

    // Add request ID to response headers
    res.setHeader('X-Request-Id', req.requestId);

    // Skip logging for health checks and metrics to reduce noise
    if (this.shouldSkipLogging(req.url)) {
      return next();
    }

    // Log request start
    this.logger.log('Request started', {
      requestId: req.requestId,
      method: req.method,
      url: req.url,
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      contentLength: req.get('Content-Length'),
      tenantId: req.headers['x-tenant-id'],
      correlationId: req.headers['x-correlation-id'],
    });

    // Capture response details
    const originalSend = res.send;
    res.send = function(body) {
      const responseTime = Date.now() - req.startTime;
      
      // Log response completion
      const logLevel = res.statusCode >= 400 ? 'warn' : 'log';
      const logger = new Logger('RequestLogger');
      
      logger[logLevel]('Request completed', {
        requestId: req.requestId,
        method: req.method,
        url: req.url,
        statusCode: res.statusCode,
        responseTime: `${responseTime}ms`,
        contentLength: res.get('Content-Length'),
        tenantId: req.headers['x-tenant-id'],
      });

      // Add performance monitoring
      if (responseTime > 5000) {
        logger.warn('Slow request detected', {
          requestId: req.requestId,
          method: req.method,
          url: req.url,
          responseTime: `${responseTime}ms`,
          statusCode: res.statusCode,
        });
      }

      return originalSend.call(this, body);
    };

    next();
  }

  private shouldSkipLogging(url: string): boolean {
    const skipPaths = [
      '/health',
      '/ready',
      '/metrics',
      '/favicon.ico',
    ];
    
    return skipPaths.some(path => url.startsWith(path));
  }
}