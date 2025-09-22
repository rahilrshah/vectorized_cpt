import { Injectable, NestInterceptor, ExecutionContext, CallHandler, Logger } from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { AuditService } from '../../audit/audit.service';
import { AuditEventType, AuditSeverity } from '../../database/entities/audit-log.entity';

@Injectable()
export class AuditInterceptor implements NestInterceptor {
  private readonly logger = new Logger(AuditInterceptor.name);

  constructor(private readonly auditService: AuditService) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const response = context.switchToHttp().getResponse();
    const startTime = Date.now();

    // Extract audit context
    const auditContext = this.extractAuditContext(request, context);

    return next.handle().pipe(
      tap((data) => {
        // Log successful operation
        this.logSuccessfulOperation(auditContext, response, startTime, data);
      }),
      catchError((error) => {
        // Log failed operation
        this.logFailedOperation(auditContext, response, startTime, error);
        throw error;
      }),
    );
  }

  private extractAuditContext(request: any, context: ExecutionContext) {
    const handler = context.getHandler();
    const controllerClass = context.getClass();
    
    return {
      tenantId: request.tenant?.id || 'unknown',
      userId: request.user?.sub || 'anonymous',
      sessionId: request.user?.sessionId || request.requestId,
      correlationId: request.requestId,
      method: request.method,
      path: request.url,
      query: this.sanitizeQuery(request.query),
      ipAddress: request.ip,
      userAgent: request.get('User-Agent'),
      handlerName: handler.name,
      controllerName: controllerClass.name,
      timestamp: new Date(),
    };
  }

  private async logSuccessfulOperation(auditContext: any, response: any, startTime: number, data: any) {
    const responseTime = Date.now() - startTime;
    
    try {
      // Determine if this operation accessed PHI
      const phiAccessed = this.detectPhiAccess(auditContext.path, data);
      
      // Determine event type
      const eventType = this.determineEventType(auditContext.method, auditContext.path);
      
      // Log to audit service
      await this.auditService.logEvent({
        tenantId: auditContext.tenantId,
        eventType,
        severity: phiAccessed ? AuditSeverity.HIGH : AuditSeverity.LOW,
        userId: auditContext.userId,
        sessionId: auditContext.sessionId,
        correlationId: auditContext.correlationId,
        resourceType: this.extractResourceType(auditContext.path),
        action: `${auditContext.method}_${auditContext.handlerName}`,
        description: `Successful ${auditContext.method} request to ${auditContext.path}`,
        requestMethod: auditContext.method,
        requestPath: auditContext.path,
        requestQuery: JSON.stringify(auditContext.query),
        responseStatus: response.statusCode || 200,
        responseTimeMs: responseTime,
        ipAddress: auditContext.ipAddress,
        userAgent: auditContext.userAgent,
        phiAccessed,
        additionalData: {
          controllerName: auditContext.controllerName,
          handlerName: auditContext.handlerName,
          resultCount: Array.isArray(data?.results) ? data.results.length : undefined,
        },
      });
    } catch (error) {
      this.logger.error('Failed to log successful operation audit', {
        error: error.message,
        auditContext,
      });
    }
  }

  private async logFailedOperation(auditContext: any, response: any, startTime: number, error: any) {
    const responseTime = Date.now() - startTime;
    
    try {
      await this.auditService.logEvent({
        tenantId: auditContext.tenantId,
        eventType: AuditEventType.ERROR_OCCURRED,
        severity: this.getErrorSeverity(error.status || 500),
        userId: auditContext.userId,
        sessionId: auditContext.sessionId,
        correlationId: auditContext.correlationId,
        resourceType: this.extractResourceType(auditContext.path),
        action: `${auditContext.method}_${auditContext.handlerName}_ERROR`,
        description: `Failed ${auditContext.method} request to ${auditContext.path}: ${error.message}`,
        requestMethod: auditContext.method,
        requestPath: auditContext.path,
        requestQuery: JSON.stringify(auditContext.query),
        responseStatus: error.status || 500,
        responseTimeMs: responseTime,
        ipAddress: auditContext.ipAddress,
        userAgent: auditContext.userAgent,
        additionalData: {
          errorType: error.constructor.name,
          errorMessage: error.message,
          stackTrace: error.stack?.split('\n').slice(0, 5), // First 5 lines only
        },
      });
    } catch (auditError) {
      this.logger.error('Failed to log failed operation audit', {
        auditError: auditError.message,
        originalError: error.message,
        auditContext,
      });
    }
  }

  private sanitizeQuery(query: any): any {
    // Remove sensitive information from query parameters
    const sanitized = { ...query };
    const sensitiveKeys = ['password', 'token', 'key', 'secret', 'api_key'];
    
    Object.keys(sanitized).forEach(key => {
      if (sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive))) {
        sanitized[key] = '[REDACTED]';
      }
    });
    
    return sanitized;
  }

  private detectPhiAccess(path: string, data: any): boolean {
    // Detect if the operation involved accessing PHI
    // For CPT search, this would typically be false unless patient data is involved
    
    // Check path patterns that might involve PHI
    const phiPatterns = [
      '/patient',
      '/medical-record',
      '/diagnosis',
      '/treatment',
    ];
    
    if (phiPatterns.some(pattern => path.includes(pattern))) {
      return true;
    }
    
    // Check if response data contains potential PHI markers
    if (data && typeof data === 'object') {
      const phiIndicators = ['patient', 'ssn', 'dob', 'medical_record'];
      const dataString = JSON.stringify(data).toLowerCase();
      
      if (phiIndicators.some(indicator => dataString.includes(indicator))) {
        return true;
      }
    }
    
    return false;
  }

  private determineEventType(method: string, path: string): AuditEventType {
    if (path.includes('/cpt') || path.includes('/search')) {
      return AuditEventType.CPT_SEARCH;
    }
    
    if (path.includes('/auth') || path.includes('/login')) {
      return AuditEventType.USER_LOGIN;
    }
    
    return AuditEventType.SYSTEM_ACCESS;
  }

  private extractResourceType(path: string): string {
    if (path.includes('/cpt')) return 'cpt_code';
    if (path.includes('/auth')) return 'authentication';
    if (path.includes('/health')) return 'health_check';
    
    return 'unknown';
  }

  private getErrorSeverity(statusCode: number): AuditSeverity {
    if (statusCode >= 500) return AuditSeverity.HIGH;
    if (statusCode >= 400) return AuditSeverity.MEDIUM;
    return AuditSeverity.LOW;
  }
}