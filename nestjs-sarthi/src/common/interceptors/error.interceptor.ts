import { Injectable, NestInterceptor, ExecutionContext, CallHandler, HttpException, HttpStatus, Logger } from '@nestjs/common';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { ConfigService } from '@nestjs/config';

export interface ErrorResponse {
  statusCode: number;
  message: string;
  error: string;
  timestamp: string;
  path: string;
  requestId: string;
  tenantId?: string;
}

@Injectable()
export class ErrorInterceptor implements NestInterceptor {
  private readonly logger = new Logger(ErrorInterceptor.name);
  private readonly isProduction: boolean;

  constructor(private readonly configService: ConfigService) {
    this.isProduction = this.configService.get('NODE_ENV') === 'production';
  }

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(
      catchError((error) => {
        const request = context.switchToHttp().getRequest();
        const response = context.switchToHttp().getResponse();
        
        const errorResponse = this.buildErrorResponse(error, request);
        
        // Log error with context
        this.logError(error, request, errorResponse);
        
        // Set response status
        response.status(errorResponse.statusCode);
        
        return throwError(() => new HttpException(errorResponse, errorResponse.statusCode));
      }),
    );
  }

  private buildErrorResponse(error: any, request: any): ErrorResponse {
    const requestId = request.requestId || 'unknown';
    const tenantId = request.tenant?.id;
    const path = request.url;
    const timestamp = new Date().toISOString();

    // Handle different error types
    if (error instanceof HttpException) {
      return {
        statusCode: error.getStatus(),
        message: this.sanitizeErrorMessage(error.message),
        error: error.constructor.name,
        timestamp,
        path,
        requestId,
        tenantId,
      };
    }

    // Handle validation errors
    if (error.name === 'ValidationError' || error.message?.includes('validation')) {
      return {
        statusCode: HttpStatus.BAD_REQUEST,
        message: this.isProduction ? 'Invalid request parameters' : this.sanitizeErrorMessage(error.message),
        error: 'ValidationError',
        timestamp,
        path,
        requestId,
        tenantId,
      };
    }

    // Handle database errors
    if (error.name === 'QueryFailedError' || error.code) {
      return {
        statusCode: HttpStatus.INTERNAL_SERVER_ERROR,
        message: this.isProduction ? 'Database operation failed' : 'Database error occurred',
        error: 'DatabaseError',
        timestamp,
        path,
        requestId,
        tenantId,
      };
    }

    // Handle timeout errors
    if (error.name === 'TimeoutError' || error.message?.includes('timeout')) {
      return {
        statusCode: HttpStatus.REQUEST_TIMEOUT,
        message: 'Request timeout - operation took too long',
        error: 'TimeoutError',
        timestamp,
        path,
        requestId,
        tenantId,
      };
    }

    // Handle rate limiting errors
    if (error.message?.includes('rate limit') || error.message?.includes('throttle')) {
      return {
        statusCode: HttpStatus.TOO_MANY_REQUESTS,
        message: 'Rate limit exceeded - please try again later',
        error: 'RateLimitError',
        timestamp,
        path,
        requestId,
        tenantId,
      };
    }

    // Handle authentication/authorization errors
    if (error.name === 'UnauthorizedError' || error.status === 401) {
      return {
        statusCode: HttpStatus.UNAUTHORIZED,
        message: 'Authentication required',
        error: 'UnauthorizedError',
        timestamp,
        path,
        requestId,
        tenantId,
      };
    }

    if (error.name === 'ForbiddenError' || error.status === 403) {
      return {
        statusCode: HttpStatus.FORBIDDEN,
        message: 'Access denied',
        error: 'ForbiddenError',
        timestamp,
        path,
        requestId,
        tenantId,
      };
    }

    // Handle Google Cloud / Vertex AI errors
    if (error.message?.includes('vertex') || error.message?.includes('google')) {
      return {
        statusCode: HttpStatus.SERVICE_UNAVAILABLE,
        message: 'External service temporarily unavailable',
        error: 'ExternalServiceError',
        timestamp,
        path,
        requestId,
        tenantId,
      };
    }

    // Generic error fallback
    return {
      statusCode: HttpStatus.INTERNAL_SERVER_ERROR,
      message: this.isProduction ? 'Internal server error' : this.sanitizeErrorMessage(error.message || 'Unknown error'),
      error: error.constructor.name || 'InternalServerError',
      timestamp,
      path,
      requestId,
      tenantId,
    };
  }

  private sanitizeErrorMessage(message: string): string {
    if (!message) return 'An error occurred';

    // Remove sensitive information from error messages
    const sensitivePatterns = [
      /password[:\s]*[^\s]+/gi,
      /token[:\s]*[^\s]+/gi,
      /key[:\s]*[^\s]+/gi,
      /secret[:\s]*[^\s]+/gi,
      /credential[:\s]*[^\s]+/gi,
      /api[_\s]*key[:\s]*[^\s]+/gi,
    ];

    let sanitized = message;
    sensitivePatterns.forEach(pattern => {
      sanitized = sanitized.replace(pattern, '[REDACTED]');
    });

    // In production, further sanitize technical details
    if (this.isProduction) {
      // Remove stack traces and file paths
      sanitized = sanitized.replace(/at\s+.*?\s+\(.*?\)/g, '');
      sanitized = sanitized.replace(/\/[^\s]*\.js:\d+:\d+/g, '');
      sanitized = sanitized.replace(/Error:\s*/g, '');
    }

    return sanitized.trim();
  }

  private logError(error: any, request: any, errorResponse: ErrorResponse) {
    const logContext = {
      requestId: errorResponse.requestId,
      tenantId: errorResponse.tenantId,
      path: errorResponse.path,
      method: request.method,
      statusCode: errorResponse.statusCode,
      ip: request.ip,
      userAgent: request.get('User-Agent'),
      userId: request.user?.sub,
      errorType: error.constructor.name,
      errorMessage: error.message,
    };

    // Log level based on error severity
    if (errorResponse.statusCode >= 500) {
      this.logger.error('Server error occurred', {
        ...logContext,
        stackTrace: this.isProduction ? undefined : error.stack,
      });
    } else if (errorResponse.statusCode >= 400) {
      this.logger.warn('Client error occurred', logContext);
    } else {
      this.logger.log('Request completed with error', logContext);
    }

    // Special handling for security-related errors
    if (errorResponse.statusCode === 401 || errorResponse.statusCode === 403) {
      this.logger.warn('Security-related error', {
        ...logContext,
        securityEvent: true,
      });
    }

    // Special handling for rate limiting
    if (errorResponse.statusCode === 429) {
      this.logger.warn('Rate limiting triggered', {
        ...logContext,
        rateLimitEvent: true,
      });
    }

    // Special handling for external service errors
    if (error.message?.includes('vertex') || error.message?.includes('google')) {
      this.logger.error('External service error', {
        ...logContext,
        externalService: 'google_cloud',
        serviceError: true,
      });
    }
  }
}