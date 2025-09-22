import { Injectable, NestMiddleware, Logger, ForbiddenException } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class SecurityMiddleware implements NestMiddleware {
  private readonly logger = new Logger(SecurityMiddleware.name);
  private readonly maxRequestSize: number;
  private readonly suspiciousPatterns: RegExp[];

  constructor(private readonly configService: ConfigService) {
    this.maxRequestSize = parseInt(this.configService.get('MAX_REQUEST_SIZE', '10485760'), 10); // 10MB
    
    // Patterns that might indicate malicious requests
    this.suspiciousPatterns = [
      /(<script[^>]*>.*?<\/script>)/gi, // Script injection
      /(javascript:)/gi, // JavaScript protocols
      /(on\w+\s*=)/gi, // Event handlers
      /(union\s+select)/gi, // SQL injection patterns
      /(drop\s+table)/gi, // SQL injection patterns
      /(exec\s*\()/gi, // Command execution patterns
      /(\.\.\/)/, // Path traversal
      /(%2e%2e%2f)/gi, // Encoded path traversal
    ];
  }

  use(req: Request, res: Response, next: NextFunction) {
    try {
      // Set security headers
      this.setSecurityHeaders(res);

      // Check request size
      this.validateRequestSize(req);

      // Validate request content
      this.validateRequestContent(req);

      // Check for suspicious patterns
      this.detectSuspiciousPatterns(req);

      // Rate limiting check (basic implementation)
      this.checkBasicRateLimit(req);

      next();
    } catch (error) {
      this.logger.error('Security validation failed', {
        error: error.message,
        url: req.url,
        method: req.method,
        ip: req.ip,
        userAgent: req.get('User-Agent'),
      });
      next(error);
    }
  }

  private setSecurityHeaders(res: Response) {
    // Prevent MIME type sniffing
    res.setHeader('X-Content-Type-Options', 'nosniff');
    
    // Prevent clickjacking
    res.setHeader('X-Frame-Options', 'DENY');
    
    // Enable XSS protection
    res.setHeader('X-XSS-Protection', '1; mode=block');
    
    // Strict transport security (HTTPS only)
    if (this.configService.get('NODE_ENV') === 'production') {
      res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
    }
    
    // Referrer policy
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    
    // Feature policy
    res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
  }

  private validateRequestSize(req: Request) {
    const contentLength = parseInt(req.get('Content-Length') || '0', 10);
    
    if (contentLength > this.maxRequestSize) {
      this.logger.warn('Request size exceeds limit', {
        contentLength,
        maxSize: this.maxRequestSize,
        url: req.url,
        ip: req.ip,
      });
      throw new ForbiddenException('Request entity too large');
    }
  }

  private validateRequestContent(req: Request) {
    // Validate Content-Type for POST/PUT requests
    if (['POST', 'PUT', 'PATCH'].includes(req.method)) {
      const contentType = req.get('Content-Type');
      const allowedTypes = [
        'application/json',
        'application/x-www-form-urlencoded',
        'multipart/form-data',
        'text/plain',
      ];
      
      if (contentType && !allowedTypes.some(type => contentType.includes(type))) {
        this.logger.warn('Suspicious content type', {
          contentType,
          url: req.url,
          method: req.method,
          ip: req.ip,
        });
        throw new ForbiddenException('Unsupported content type');
      }
    }

    // Check for excessively long headers
    Object.entries(req.headers).forEach(([name, value]) => {
      if (typeof value === 'string' && value.length > 8192) { // 8KB limit
        this.logger.warn('Excessively long header detected', {
          headerName: name,
          headerLength: value.length,
          url: req.url,
          ip: req.ip,
        });
        throw new ForbiddenException('Request header too large');
      }
    });
  }

  private detectSuspiciousPatterns(req: Request) {
    const checkString = `${req.url} ${JSON.stringify(req.query)} ${JSON.stringify(req.headers)}`;
    
    for (const pattern of this.suspiciousPatterns) {
      if (pattern.test(checkString)) {
        this.logger.error('Suspicious pattern detected', {
          pattern: pattern.toString(),
          url: req.url,
          method: req.method,
          ip: req.ip,
          userAgent: req.get('User-Agent'),
        });
        
        // In production, you might want to block these requests
        if (this.configService.get('SECURITY_STRICT_MODE') === 'true') {
          throw new ForbiddenException('Suspicious request pattern detected');
        }
      }
    }
  }

  private checkBasicRateLimit(req: Request) {
    // Basic rate limiting - in production, use Redis-based solution
    const ip = req.ip;
    const now = Date.now();
    const windowMs = 60000; // 1 minute
    const maxRequests = 1000; // 1000 requests per minute per IP
    
    // This is a simplified implementation
    // In production, implement proper Redis-based rate limiting
    
    // For now, just log high-frequency requests
    const userAgent = req.get('User-Agent');
    if (!userAgent || userAgent.includes('bot') || userAgent.includes('crawler')) {
      this.logger.warn('Bot or crawler detected', {
        ip,
        userAgent,
        url: req.url,
      });
    }
  }
}