-- Initial PostgreSQL schema for Sarthi CPT Vector Service
-- HIPAA-compliant database structure with multi-tenant support

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE audit_event_type AS ENUM (
  'cpt_search',
  'cpt_access', 
  'user_login',
  'user_logout',
  'data_export',
  'system_access',
  'error_occurred',
  'security_violation'
);

CREATE TYPE audit_severity AS ENUM (
  'low',
  'medium', 
  'high',
  'critical'
);

-- Tenant configurations table
CREATE TABLE tenant_configs (
  tenant_id VARCHAR(100) PRIMARY KEY,
  tenant_name VARCHAR(200) NOT NULL,
  organization_id VARCHAR(100),
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'inactive')),
  subscription_tier VARCHAR(50) DEFAULT 'basic',
  admin_email VARCHAR(200) NOT NULL,
  admin_phone VARCHAR(20),
  billing_contact VARCHAR(200),
  settings JSONB,
  security_config JSONB,
  api_keys JSONB,
  permissions JSONB,
  resource_quotas JSONB,
  custom_domain VARCHAR(200),
  webhook_urls JSONB,
  integration_config JSONB,
  compliance_certifications JSONB,
  data_processing_agreement TEXT,
  privacy_policy_version VARCHAR(20),
  terms_of_service_version VARCHAR(20),
  last_accessed_at TIMESTAMP,
  total_requests BIGINT DEFAULT 0,
  monthly_request_limit INTEGER,
  current_month_requests INTEGER DEFAULT 0,
  created_by VARCHAR(100) NOT NULL,
  updated_by VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP,
  metadata JSONB
);

-- Indexes for tenant_configs
CREATE INDEX idx_tenant_configs_status ON tenant_configs(status);
CREATE INDEX idx_tenant_configs_subscription_tier ON tenant_configs(subscription_tier);
CREATE INDEX idx_tenant_configs_org_id ON tenant_configs(organization_id);

-- CPT codes table with tenant isolation
CREATE TABLE cpt_codes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id VARCHAR(100) NOT NULL,
  cpt_code VARCHAR(10) NOT NULL,
  description TEXT NOT NULL,
  category VARCHAR(100),
  status VARCHAR(20) DEFAULT 'active',
  vector_embedding JSONB,
  encrypted_data TEXT,
  data_classification VARCHAR(20) DEFAULT 'public' CHECK (data_classification IN ('public', 'restricted', 'confidential', 'phi')),
  created_by VARCHAR(100),
  updated_by VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  version INTEGER DEFAULT 1,
  metadata JSONB,
  
  -- Foreign key constraint
  CONSTRAINT fk_cpt_codes_tenant FOREIGN KEY (tenant_id) REFERENCES tenant_configs(tenant_id) ON DELETE CASCADE
);

-- Indexes for cpt_codes
CREATE UNIQUE INDEX idx_cpt_codes_tenant_code ON cpt_codes(tenant_id, cpt_code);
CREATE INDEX idx_cpt_codes_tenant_id ON cpt_codes(tenant_id);
CREATE INDEX idx_cpt_codes_category ON cpt_codes(tenant_id, category);
CREATE INDEX idx_cpt_codes_status ON cpt_codes(tenant_id, status);
CREATE INDEX idx_cpt_codes_classification ON cpt_codes(data_classification);

-- GIN index for vector embeddings (for efficient similarity search)
CREATE INDEX idx_cpt_codes_vector_embedding ON cpt_codes USING GIN (vector_embedding);

-- Audit logs table for HIPAA compliance
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id VARCHAR(100) NOT NULL,
  event_type audit_event_type NOT NULL,
  severity audit_severity DEFAULT 'low',
  user_id VARCHAR(100),
  session_id VARCHAR(100),
  correlation_id VARCHAR(100),
  resource_type VARCHAR(50),
  resource_id VARCHAR(100),
  action VARCHAR(50) NOT NULL,
  description TEXT NOT NULL,
  request_method VARCHAR(10),
  request_path VARCHAR(500),
  request_query TEXT,
  response_status INTEGER,
  response_time_ms INTEGER,
  ip_address VARCHAR(45) NOT NULL,
  user_agent VARCHAR(500),
  additional_data JSONB,
  phi_accessed BOOLEAN DEFAULT FALSE,
  data_classification VARCHAR(20) DEFAULT 'public',
  compliance_flags JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  retention_until TIMESTAMP,
  is_sensitive BOOLEAN DEFAULT FALSE,
  geo_location VARCHAR(100),
  
  -- Foreign key constraint
  CONSTRAINT fk_audit_logs_tenant FOREIGN KEY (tenant_id) REFERENCES tenant_configs(tenant_id) ON DELETE CASCADE
);

-- Indexes for audit_logs
CREATE INDEX idx_audit_logs_tenant_event ON audit_logs(tenant_id, event_type);
CREATE INDEX idx_audit_logs_tenant_created ON audit_logs(tenant_id, created_at);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_created ON audit_logs(event_type, created_at);
CREATE INDEX idx_audit_logs_correlation_id ON audit_logs(correlation_id);
CREATE INDEX idx_audit_logs_phi_accessed ON audit_logs(phi_accessed) WHERE phi_accessed = TRUE;
CREATE INDEX idx_audit_logs_retention ON audit_logs(retention_until);

-- Vector search optimization table (for caching common searches)
CREATE TABLE vector_search_cache (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id VARCHAR(100) NOT NULL,
  query_hash VARCHAR(64) NOT NULL,
  query_text TEXT NOT NULL,
  embedding_vector JSONB NOT NULL,
  search_results JSONB NOT NULL,
  result_count INTEGER NOT NULL,
  similarity_threshold FLOAT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NOT NULL,
  access_count INTEGER DEFAULT 0,
  last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  -- Foreign key constraint
  CONSTRAINT fk_vector_cache_tenant FOREIGN KEY (tenant_id) REFERENCES tenant_configs(tenant_id) ON DELETE CASCADE
);

-- Indexes for vector_search_cache
CREATE UNIQUE INDEX idx_vector_cache_tenant_hash ON vector_search_cache(tenant_id, query_hash);
CREATE INDEX idx_vector_cache_expires ON vector_search_cache(expires_at);
CREATE INDEX idx_vector_cache_tenant_created ON vector_search_cache(tenant_id, created_at);

-- Performance monitoring table
CREATE TABLE performance_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id VARCHAR(100) NOT NULL,
  metric_type VARCHAR(50) NOT NULL,
  metric_name VARCHAR(100) NOT NULL,
  metric_value FLOAT NOT NULL,
  dimensions JSONB,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  retention_days INTEGER DEFAULT 90,
  
  -- Foreign key constraint
  CONSTRAINT fk_performance_metrics_tenant FOREIGN KEY (tenant_id) REFERENCES tenant_configs(tenant_id) ON DELETE CASCADE
);

-- Indexes for performance_metrics
CREATE INDEX idx_performance_metrics_tenant_type ON performance_metrics(tenant_id, metric_type);
CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX idx_performance_metrics_retention ON performance_metrics(timestamp, retention_days);

-- Row Level Security (RLS) for multi-tenant isolation
ALTER TABLE cpt_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE vector_search_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;

-- RLS policies will be created programmatically based on tenant context

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_tenant_configs_updated_at 
    BEFORE UPDATE ON tenant_configs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cpt_codes_updated_at 
    BEFORE UPDATE ON cpt_codes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function for automatic audit log cleanup
CREATE OR REPLACE FUNCTION cleanup_expired_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs 
    WHERE retention_until < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log cleanup activity
    INSERT INTO audit_logs (
        tenant_id, event_type, severity, action, description, 
        ip_address, additional_data
    ) VALUES (
        'system', 'system_access', 'low', 'CLEANUP_AUDIT_LOGS',
        'Automatic audit log cleanup completed',
        '127.0.0.1', 
        jsonb_build_object('deleted_count', deleted_count)
    );
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function for vector search cache cleanup
CREATE OR REPLACE FUNCTION cleanup_expired_vector_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM vector_search_cache 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create initial system tenant
INSERT INTO tenant_configs (
    tenant_id, tenant_name, admin_email, created_by,
    settings, security_config
) VALUES (
    'system',
    'System Tenant', 
    'admin@sarthi.healthcare',
    'system',
    '{"maxRequestsPerMinute": 1000, "maxSearchResults": 100, "enableAdvancedSearch": true, "dataRetentionDays": 2555, "allowedFeatures": ["cpt:search", "cpt:admin", "audit:read"]}',
    '{"encryptionRequired": true, "auditLevel": "comprehensive", "phiHandlingEnabled": true, "dataResidencyRegion": "us-central1", "complianceProfile": "hipaa"}'
) ON CONFLICT (tenant_id) DO NOTHING;

-- Grant necessary permissions (adjust based on your application user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cpt_service_user;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO cpt_service_user;

COMMENT ON SCHEMA public IS 'Sarthi CPT Vector Service - HIPAA Compliant Multi-Tenant Database Schema';
COMMENT ON TABLE tenant_configs IS 'Multi-tenant configuration and settings';
COMMENT ON TABLE cpt_codes IS 'CPT codes with vector embeddings for similarity search';
COMMENT ON TABLE audit_logs IS 'HIPAA-compliant audit trail for all system activities';
COMMENT ON TABLE vector_search_cache IS 'Performance optimization cache for common vector searches';
COMMENT ON TABLE performance_metrics IS 'System performance monitoring and metrics';