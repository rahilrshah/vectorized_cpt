import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Between, MoreThan } from 'typeorm';
import { ConfigService } from '@nestjs/config';
import { AuditLog, AuditEventType, AuditSeverity } from '../database/entities/audit-log.entity';

export interface CreateAuditLogDto {
  tenantId: string;
  eventType: AuditEventType;
  severity?: AuditSeverity;
  userId?: string;
  sessionId?: string;
  correlationId?: string;
  resourceType?: string;
  resourceId?: string;
  action: string;
  description: string;
  requestMethod?: string;
  requestPath?: string;
  requestQuery?: string;
  responseStatus?: number;
  responseTimeMs?: number;
  ipAddress: string;
  userAgent?: string;
  additionalData?: Record<string, any>;
  phiAccessed?: boolean;
  dataClassification?: string;
  complianceFlags?: Record<string, any>;
}

@Injectable()
export class AuditService {
  private readonly logger = new Logger(AuditService.name);
  private readonly retentionDays: number;

  constructor(
    @InjectRepository(AuditLog)
    private readonly auditLogRepository: Repository<AuditLog>,
    private readonly configService: ConfigService,
  ) {
    this.retentionDays = this.configService.get('hipaa.auditRetentionDays', 2555); // 7 years default
  }

  async logEvent(dto: CreateAuditLogDto): Promise<AuditLog> {
    try {
      // Calculate retention date
      const retentionUntil = new Date();
      retentionUntil.setDate(retentionUntil.getDate() + this.retentionDays);

      // Create audit log entry
      const auditLog = this.auditLogRepository.create({
        ...dto,
        severity: dto.severity || AuditSeverity.LOW,
        dataClassification: dto.dataClassification || 'public',
        retentionUntil,
        isSensitive: dto.phiAccessed || dto.severity === AuditSeverity.CRITICAL,
        geoLocation: this.extractGeoLocation(dto.ipAddress),
      });

      const savedLog = await this.auditLogRepository.save(auditLog);

      // Log high-severity events for immediate attention
      if (dto.severity === AuditSeverity.HIGH || dto.severity === AuditSeverity.CRITICAL) {
        this.logger.warn('High-severity audit event', {
          id: savedLog.id,
          tenantId: dto.tenantId,
          eventType: dto.eventType,
          description: dto.description,
        });
      }

      return savedLog;
    } catch (error) {
      this.logger.error('Failed to create audit log', {
        error: error.message,
        dto: this.sanitizeAuditData(dto),
      });
      throw error;
    }
  }

  async getAuditLogs(
    tenantId: string,
    filters: {
      eventType?: AuditEventType;
      userId?: string;
      startDate?: Date;
      endDate?: Date;
      severity?: AuditSeverity;
      limit?: number;
      offset?: number;
    } = {},
  ): Promise<{ logs: AuditLog[]; total: number }> {
    try {
      const queryBuilder = this.auditLogRepository
        .createQueryBuilder('audit')
        .where('audit.tenantId = :tenantId', { tenantId });

      // Apply filters
      if (filters.eventType) {
        queryBuilder.andWhere('audit.eventType = :eventType', { eventType: filters.eventType });
      }

      if (filters.userId) {
        queryBuilder.andWhere('audit.userId = :userId', { userId: filters.userId });
      }

      if (filters.severity) {
        queryBuilder.andWhere('audit.severity = :severity', { severity: filters.severity });
      }

      if (filters.startDate && filters.endDate) {
        queryBuilder.andWhere('audit.createdAt BETWEEN :startDate AND :endDate', {
          startDate: filters.startDate,
          endDate: filters.endDate,
        });
      } else if (filters.startDate) {
        queryBuilder.andWhere('audit.createdAt >= :startDate', { startDate: filters.startDate });
      }

      // Get total count
      const total = await queryBuilder.getCount();

      // Apply pagination
      queryBuilder
        .orderBy('audit.createdAt', 'DESC')
        .limit(filters.limit || 50)
        .offset(filters.offset || 0);

      const logs = await queryBuilder.getMany();

      return { logs, total };
    } catch (error) {
      this.logger.error('Failed to retrieve audit logs', {
        error: error.message,
        tenantId,
        filters,
      });
      throw error;
    }
  }

  async getSecurityEvents(
    tenantId: string,
    timeRange: { start: Date; end: Date },
  ): Promise<AuditLog[]> {
    try {
      return await this.auditLogRepository.find({
        where: {
          tenantId,
          eventType: AuditEventType.SECURITY_VIOLATION,
          createdAt: Between(timeRange.start, timeRange.end),
        },
        order: { createdAt: 'DESC' },
        take: 100,
      });
    } catch (error) {
      this.logger.error('Failed to retrieve security events', {
        error: error.message,
        tenantId,
        timeRange,
      });
      throw error;
    }
  }

  async getComplianceReport(
    tenantId: string,
    period: { start: Date; end: Date },
  ): Promise<{
    totalEvents: number;
    eventsByType: Record<string, number>;
    phiAccessEvents: number;
    securityViolations: number;
    averageResponseTime: number;
  }> {
    try {
      const logs = await this.auditLogRepository.find({
        where: {
          tenantId,
          createdAt: Between(period.start, period.end),
        },
      });

      const eventsByType = logs.reduce((acc, log) => {
        acc[log.eventType] = (acc[log.eventType] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      const phiAccessEvents = logs.filter(log => log.phiAccessed).length;
      const securityViolations = logs.filter(log => log.eventType === AuditEventType.SECURITY_VIOLATION).length;
      
      const responseTimes = logs
        .filter(log => log.responseTimeMs !== null)
        .map(log => log.responseTimeMs);
      
      const averageResponseTime = responseTimes.length > 0
        ? responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length
        : 0;

      return {
        totalEvents: logs.length,
        eventsByType,
        phiAccessEvents,
        securityViolations,
        averageResponseTime,
      };
    } catch (error) {
      this.logger.error('Failed to generate compliance report', {
        error: error.message,
        tenantId,
        period,
      });
      throw error;
    }
  }

  async cleanupExpiredLogs(): Promise<number> {
    try {
      const result = await this.auditLogRepository.delete({
        retentionUntil: MoreThan(new Date()),
      });

      this.logger.log('Cleaned up expired audit logs', {
        deletedCount: result.affected,
      });

      return result.affected || 0;
    } catch (error) {
      this.logger.error('Failed to cleanup expired audit logs', {
        error: error.message,
      });
      throw error;
    }
  }

  async logSecurityViolation(
    tenantId: string,
    description: string,
    additionalData: Record<string, any>,
    ipAddress: string,
    userAgent?: string,
  ): Promise<AuditLog> {
    return this.logEvent({
      tenantId,
      eventType: AuditEventType.SECURITY_VIOLATION,
      severity: AuditSeverity.CRITICAL,
      action: 'SECURITY_VIOLATION',
      description,
      ipAddress,
      userAgent,
      additionalData,
      dataClassification: 'confidential',
    });
  }

  async logCptSearch(
    tenantId: string,
    userId: string,
    searchQuery: string,
    resultCount: number,
    responseTimeMs: number,
    ipAddress: string,
    requestId: string,
  ): Promise<AuditLog> {
    return this.logEvent({
      tenantId,
      eventType: AuditEventType.CPT_SEARCH,
      severity: AuditSeverity.LOW,
      userId,
      correlationId: requestId,
      resourceType: 'cpt_code',
      action: 'SEARCH',
      description: `CPT code search performed`,
      responseTimeMs,
      ipAddress,
      additionalData: {
        searchQuery: this.sanitizeSearchQuery(searchQuery),
        resultCount,
        searchType: 'vector_search',
      },
    });
  }

  private sanitizeAuditData(dto: CreateAuditLogDto): Partial<CreateAuditLogDto> {
    const sanitized = { ...dto };
    
    // Remove sensitive information
    if (sanitized.additionalData) {
      const sensitiveKeys = ['password', 'token', 'key', 'secret'];
      Object.keys(sanitized.additionalData).forEach(key => {
        if (sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive))) {
          sanitized.additionalData[key] = '[REDACTED]';
        }
      });
    }

    return sanitized;
  }

  private sanitizeSearchQuery(query: string): string {
    // Remove potential PHI from search queries while preserving medical terms
    let sanitized = query;
    
    // Remove potential patient identifiers
    sanitized = sanitized.replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]'); // SSN pattern
    sanitized = sanitized.replace(/\b\d{10,15}\b/g, '[ID]'); // Long numbers that might be IDs
    sanitized = sanitized.replace(/\b[A-Z]{2}\d{8,}\b/g, '[MRN]'); // Medical record number patterns
    
    return sanitized;
  }

  private extractGeoLocation(ipAddress: string): string {
    // Basic geo-location extraction (implement with actual geo-IP service)
    if (ipAddress.startsWith('127.') || ipAddress.startsWith('192.168.') || ipAddress.startsWith('10.')) {
      return 'local';
    }
    
    // For production, integrate with geo-IP service
    return 'unknown';
  }
}