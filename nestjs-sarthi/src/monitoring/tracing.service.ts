import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { trace, context, SpanStatusCode, SpanKind } from '@opentelemetry/api';

@Injectable()
export class TracingService {
  private readonly logger = new Logger(TracingService.name);
  private readonly tracer = trace.getTracer('cpt-vector-service', '1.0.0');
  private readonly isEnabled: boolean;

  constructor(private readonly configService: ConfigService) {
    this.isEnabled = this.configService.get('monitoring.enableTracing', true);
    
    if (this.isEnabled) {
      this.logger.log('Distributed tracing enabled');
    } else {
      this.logger.warn('Distributed tracing disabled');
    }
  }

  startSpan(name: string, attributes?: Record<string, any>) {
    if (!this.isEnabled) {
      return null;
    }

    return this.tracer.startSpan(name, {
      kind: SpanKind.INTERNAL,
      attributes: {
        'service.name': 'cpt-vector-service',
        'service.version': '1.0.0',
        ...attributes,
      },
    });
  }

  startHttpSpan(name: string, method: string, url: string, tenantId?: string) {
    if (!this.isEnabled) {
      return null;
    }

    return this.tracer.startSpan(name, {
      kind: SpanKind.SERVER,
      attributes: {
        'http.method': method,
        'http.url': url,
        'http.scheme': 'https',
        'tenant.id': tenantId || 'unknown',
        'service.name': 'cpt-vector-service',
      },
    });
  }

  startDatabaseSpan(operation: string, table: string, tenantId?: string) {
    if (!this.isEnabled) {
      return null;
    }

    return this.tracer.startSpan(`db.${operation}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        'db.system': 'postgresql',
        'db.operation': operation,
        'db.sql.table': table,
        'tenant.id': tenantId || 'system',
      },
    });
  }

  startVectorSpan(operation: string, modelType?: string, tenantId?: string) {
    if (!this.isEnabled) {
      return null;
    }

    return this.tracer.startSpan(`vector.${operation}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        'ai.operation': operation,
        'ai.model.type': modelType || 'text-embedding-004',
        'ai.provider': 'google_vertex_ai',
        'tenant.id': tenantId || 'system',
      },
    });
  }

  startCacheSpan(operation: string, cacheType: string, tenantId?: string) {
    if (!this.isEnabled) {
      return null;
    }

    return this.tracer.startSpan(`cache.${operation}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        'cache.type': cacheType,
        'cache.operation': operation,
        'tenant.id': tenantId || 'system',
      },
    });
  }

  setSpanAttributes(span: any, attributes: Record<string, any>) {
    if (!this.isEnabled || !span) {
      return;
    }

    span.setAttributes(attributes);
  }

  setSpanStatus(span: any, success: boolean, message?: string) {
    if (!this.isEnabled || !span) {
      return;
    }

    if (success) {
      span.setStatus({ code: SpanStatusCode.OK });
    } else {
      span.setStatus({ 
        code: SpanStatusCode.ERROR, 
        message: message || 'Operation failed' 
      });
    }
  }

  recordException(span: any, error: Error) {
    if (!this.isEnabled || !span) {
      return;
    }

    span.recordException(error);
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: error.message,
    });
  }

  endSpan(span: any) {
    if (!this.isEnabled || !span) {
      return;
    }

    span.end();
  }

  async withSpan<T>(
    name: string, 
    operation: (span: any) => Promise<T>, 
    attributes?: Record<string, any>
  ): Promise<T> {
    if (!this.isEnabled) {
      return operation(null);
    }

    const span = this.startSpan(name, attributes);
    
    try {
      const result = await operation(span);
      this.setSpanStatus(span, true);
      return result;
    } catch (error) {
      this.recordException(span, error);
      throw error;
    } finally {
      this.endSpan(span);
    }
  }

  async withHttpSpan<T>(
    name: string,
    method: string,
    url: string,
    operation: (span: any) => Promise<T>,
    tenantId?: string
  ): Promise<T> {
    if (!this.isEnabled) {
      return operation(null);
    }

    const span = this.startHttpSpan(name, method, url, tenantId);
    
    try {
      const result = await operation(span);
      this.setSpanAttributes(span, { 'http.status_code': 200 });
      this.setSpanStatus(span, true);
      return result;
    } catch (error) {
      this.setSpanAttributes(span, { 
        'http.status_code': error.status || 500,
        'error.type': error.constructor.name,
      });
      this.recordException(span, error);
      throw error;
    } finally {
      this.endSpan(span);
    }
  }

  getTraceId(): string | undefined {
    if (!this.isEnabled) {
      return undefined;
    }

    const activeSpan = trace.getActiveSpan();
    if (activeSpan) {
      return activeSpan.spanContext().traceId;
    }
    
    return undefined;
  }

  getSpanId(): string | undefined {
    if (!this.isEnabled) {
      return undefined;
    }

    const activeSpan = trace.getActiveSpan();
    if (activeSpan) {
      return activeSpan.spanContext().spanId;
    }
    
    return undefined;
  }

  createChildContext(parentSpan: any) {
    if (!this.isEnabled || !parentSpan) {
      return context.active();
    }

    return trace.setSpan(context.active(), parentSpan);
  }

  runInContext<T>(contextToUse: any, operation: () => T): T {
    if (!this.isEnabled) {
      return operation();
    }

    return context.with(contextToUse, operation);
  }
}