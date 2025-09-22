import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn, Index } from 'typeorm';

export enum AuditEventType {
  CPT_SEARCH = 'cpt_search',
  CPT_ACCESS = 'cpt_access',
  USER_LOGIN = 'user_login',
  USER_LOGOUT = 'user_logout',
  DATA_EXPORT = 'data_export',
  SYSTEM_ACCESS = 'system_access',
  ERROR_OCCURRED = 'error_occurred',
  SECURITY_VIOLATION = 'security_violation',
}

export enum AuditSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

@Entity('audit_logs')
@Index(['tenantId', 'eventType'])
@Index(['tenantId', 'createdAt'])
@Index(['userId'])
@Index(['eventType', 'createdAt'])
export class AuditLog {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'tenant_id', length: 100 })
  @Index()
  tenantId: string;

  @Column({ name: 'event_type', type: 'enum', enum: AuditEventType })
  eventType: AuditEventType;

  @Column({ name: 'severity', type: 'enum', enum: AuditSeverity, default: AuditSeverity.LOW })
  severity: AuditSeverity;

  @Column({ name: 'user_id', length: 100, nullable: true })
  userId: string;

  @Column({ name: 'session_id', length: 100, nullable: true })
  sessionId: string;

  @Column({ name: 'correlation_id', length: 100, nullable: true })
  correlationId: string;

  @Column({ name: 'resource_type', length: 50, nullable: true })
  resourceType: string;

  @Column({ name: 'resource_id', length: 100, nullable: true })
  resourceId: string;

  @Column({ name: 'action', length: 50 })
  action: string;

  @Column({ name: 'description', type: 'text' })
  description: string;

  @Column({ name: 'request_method', length: 10, nullable: true })
  requestMethod: string;

  @Column({ name: 'request_path', length: 500, nullable: true })
  requestPath: string;

  @Column({ name: 'request_query', type: 'text', nullable: true })
  requestQuery: string;

  @Column({ name: 'response_status', type: 'integer', nullable: true })
  responseStatus: number;

  @Column({ name: 'response_time_ms', type: 'integer', nullable: true })
  responseTimeMs: number;

  @Column({ name: 'ip_address', length: 45 })
  ipAddress: string;

  @Column({ name: 'user_agent', length: 500, nullable: true })
  userAgent: string;

  @Column({ name: 'additional_data', type: 'jsonb', nullable: true })
  additionalData: Record<string, any>;

  @Column({ name: 'phi_accessed', type: 'boolean', default: false })
  phiAccessed: boolean;

  @Column({ name: 'data_classification', length: 20, default: 'public' })
  dataClassification: string;

  @Column({ name: 'compliance_flags', type: 'jsonb', nullable: true })
  complianceFlags: Record<string, any>;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @Column({ name: 'retention_until', type: 'timestamp', nullable: true })
  retentionUntil: Date;

  @Column({ name: 'is_sensitive', type: 'boolean', default: false })
  isSensitive: boolean;

  @Column({ name: 'geo_location', length: 100, nullable: true })
  geoLocation: string;
}