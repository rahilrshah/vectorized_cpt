import { Entity, Column, PrimaryColumn, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

export interface TenantSettings {
  maxRequestsPerMinute: number;
  maxSearchResults: number;
  enableAdvancedSearch: boolean;
  dataRetentionDays: number;
  allowedFeatures: string[];
  customConfigurations: Record<string, any>;
}

export interface TenantSecurityConfig {
  encryptionRequired: boolean;
  auditLevel: 'minimal' | 'standard' | 'comprehensive';
  phiHandlingEnabled: boolean;
  dataResidencyRegion: string;
  complianceProfile: 'basic' | 'hipaa' | 'enterprise';
}

@Entity('tenant_configs')
@Index(['status'])
@Index(['subscriptionTier'])
export class TenantConfig {
  @PrimaryColumn({ name: 'tenant_id', length: 100 })
  tenantId: string;

  @Column({ name: 'tenant_name', length: 200 })
  tenantName: string;

  @Column({ name: 'organization_id', length: 100, nullable: true })
  organizationId: string;

  @Column({ name: 'status', length: 20, default: 'active' })
  status: string; // active, suspended, inactive

  @Column({ name: 'subscription_tier', length: 50, default: 'basic' })
  subscriptionTier: string; // basic, professional, enterprise

  @Column({ name: 'admin_email', length: 200 })
  adminEmail: string;

  @Column({ name: 'admin_phone', length: 20, nullable: true })
  adminPhone: string;

  @Column({ name: 'billing_contact', length: 200, nullable: true })
  billingContact: string;

  @Column({ name: 'settings', type: 'jsonb', nullable: true })
  settings: TenantSettings;

  @Column({ name: 'security_config', type: 'jsonb', nullable: true })
  securityConfig: TenantSecurityConfig;

  @Column({ name: 'api_keys', type: 'jsonb', nullable: true })
  apiKeys: Record<string, any>;

  @Column({ name: 'permissions', type: 'jsonb', nullable: true })
  permissions: string[];

  @Column({ name: 'resource_quotas', type: 'jsonb', nullable: true })
  resourceQuotas: Record<string, any>;

  @Column({ name: 'custom_domain', length: 200, nullable: true })
  customDomain: string;

  @Column({ name: 'webhook_urls', type: 'jsonb', nullable: true })
  webhookUrls: Record<string, string>;

  @Column({ name: 'integration_config', type: 'jsonb', nullable: true })
  integrationConfig: Record<string, any>;

  @Column({ name: 'compliance_certifications', type: 'jsonb', nullable: true })
  complianceCertifications: string[];

  @Column({ name: 'data_processing_agreement', type: 'text', nullable: true })
  dataProcessingAgreement: string;

  @Column({ name: 'privacy_policy_version', length: 20, nullable: true })
  privacyPolicyVersion: string;

  @Column({ name: 'terms_of_service_version', length: 20, nullable: true })
  termsOfServiceVersion: string;

  @Column({ name: 'last_accessed_at', type: 'timestamp', nullable: true })
  lastAccessedAt: Date;

  @Column({ name: 'total_requests', type: 'bigint', default: 0 })
  totalRequests: number;

  @Column({ name: 'monthly_request_limit', type: 'integer', nullable: true })
  monthlyRequestLimit: number;

  @Column({ name: 'current_month_requests', type: 'integer', default: 0 })
  currentMonthRequests: number;

  @Column({ name: 'created_by', length: 100 })
  createdBy: string;

  @Column({ name: 'updated_by', length: 100, nullable: true })
  updatedBy: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  @Column({ name: 'expires_at', type: 'timestamp', nullable: true })
  expiresAt: Date;

  @Column({ name: 'metadata', type: 'jsonb', nullable: true })
  metadata: Record<string, any>;
}