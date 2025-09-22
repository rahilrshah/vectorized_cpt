import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AuditService } from '../audit/audit.service';

export interface DataLineageEvent {
  operationId: string;
  tenantId: string;
  userId?: string;
  operationType: 'read' | 'write' | 'transform' | 'delete' | 'search';
  dataSource: {
    type: 'database' | 'api' | 'file' | 'external';
    identifier: string;
    location: string;
    schema?: string;
    table?: string;
  };
  dataTarget?: {
    type: 'database' | 'api' | 'file' | 'external';
    identifier: string;
    location: string;
    schema?: string;
    table?: string;
  };
  dataFields: {
    name: string;
    type: string;
    classification: 'public' | 'internal' | 'confidential' | 'phi' | 'pii';
    sensitivity: 'low' | 'medium' | 'high' | 'critical';
  }[];
  transformation?: {
    type: 'filter' | 'aggregate' | 'join' | 'vectorize' | 'encrypt' | 'redact';
    description: string;
    algorithm?: string;
    parameters?: Record<string, any>;
  };
  compliance: {
    regulation: string[];
    purpose: string;
    legalBasis?: string;
    retentionPeriod?: string;
  };
  metadata: {
    timestamp: Date;
    processingTime?: number;
    recordCount?: number;
    dataVolume?: number;
    qualityScore?: number;
  };
}

@Injectable()
export class DataLineageService {
  private readonly logger = new Logger(DataLineageService.name);

  constructor(
    private readonly configService: ConfigService,
    private readonly auditService: AuditService,
  ) {}

  async trackDataLineage(event: DataLineageEvent): Promise<void> {
    try {
      // Log data lineage event for audit trail
      await this.auditService.logEvent({
        tenantId: event.tenantId,
        eventType: 'DATA_LINEAGE',
        severity: this.getSeverityFromClassification(event.dataFields),
        userId: event.userId,
        correlationId: event.operationId,
        resourceType: 'data_lineage',
        resourceId: event.operationId,
        action: `DATA_${event.operationType.toUpperCase()}`,
        description: `Data lineage tracking for ${event.operationType} operation`,
        ipAddress: 'internal',
        additionalData: {
          dataSource: event.dataSource,
          dataTarget: event.dataTarget,
          dataFields: event.dataFields.map(field => ({
            name: field.name,
            type: field.type,
            classification: field.classification,
            sensitivity: field.sensitivity,
          })),
          transformation: event.transformation,
          compliance: event.compliance,
          metadata: event.metadata,
        },
        phiAccessed: event.dataFields.some(field => 
          field.classification === 'phi' || field.classification === 'pii'
        ),
        dataClassification: this.getHighestClassification(event.dataFields),
        complianceFlags: {
          gdprApplicable: event.compliance.regulation.includes('GDPR'),
          hipaaApplicable: event.compliance.regulation.includes('HIPAA'),
          pipedaApplicable: event.compliance.regulation.includes('PIPEDA'),
          dataMinimization: true,
          purposeLimitation: !!event.compliance.purpose,
        },
      });

      // Send to data governance platform if enabled
      if (this.configService.get('sarthi.dataGovernanceEnabled', true)) {
        await this.sendToDataGovernancePlatform(event);
      }

      this.logger.log('Data lineage tracked successfully', {
        operationId: event.operationId,
        tenantId: event.tenantId,
        operationType: event.operationType,
        dataFieldCount: event.dataFields.length,
        containsPHI: event.dataFields.some(f => f.classification === 'phi'),
      });

    } catch (error) {
      this.logger.error('Failed to track data lineage', {
        error: error.message,
        operationId: event.operationId,
        tenantId: event.tenantId,
        operationType: event.operationType,
      });
      throw error;
    }
  }

  async trackCptSearch(
    operationId: string,
    tenantId: string,
    userId: string,
    searchQuery: string,
    results: any[],
    processingTime: number,
  ): Promise<void> {
    const lineageEvent: DataLineageEvent = {
      operationId,
      tenantId,
      userId,
      operationType: 'search',
      dataSource: {
        type: 'database',
        identifier: 'cpt-codes-vectorized',
        location: 'google-firestore',
        schema: 'healthcare',
        table: 'cpt_codes',
      },
      dataFields: [
        {
          name: 'search_query',
          type: 'text',
          classification: 'internal',
          sensitivity: 'low',
        },
        {
          name: 'cpt_code',
          type: 'string',
          classification: 'public',
          sensitivity: 'low',
        },
        {
          name: 'description',
          type: 'text',
          classification: 'public',
          sensitivity: 'low',
        },
        {
          name: 'vector_embedding',
          type: 'vector',
          classification: 'internal',
          sensitivity: 'medium',
        },
      ],
      transformation: {
        type: 'vectorize',
        description: 'Convert medical text to vector embeddings for similarity search',
        algorithm: 'text-embedding-004',
        parameters: {
          dimensions: 768,
          similarityThreshold: 0.7,
          maxResults: results.length,
        },
      },
      compliance: {
        regulation: ['HIPAA', 'GDPR'],
        purpose: 'Medical coding assistance and billing optimization',
        legalBasis: 'Legitimate interest for healthcare operations',
        retentionPeriod: '7-years',
      },
      metadata: {
        timestamp: new Date(),
        processingTime,
        recordCount: results.length,
        dataVolume: searchQuery.length + JSON.stringify(results).length,
        qualityScore: this.calculateSearchQualityScore(results),
      },
    };

    await this.trackDataLineage(lineageEvent);
  }

  async trackDataAccess(
    operationId: string,
    tenantId: string,
    userId: string,
    resourceType: string,
    resourceId: string,
    fieldsAccessed: string[],
  ): Promise<void> {
    const lineageEvent: DataLineageEvent = {
      operationId,
      tenantId,
      userId,
      operationType: 'read',
      dataSource: {
        type: 'database',
        identifier: resourceType,
        location: 'postgresql',
        schema: 'public',
        table: resourceType,
      },
      dataFields: fieldsAccessed.map(field => ({
        name: field,
        type: 'unknown',
        classification: this.classifyDataField(field),
        sensitivity: this.getFieldSensitivity(field),
      })),
      compliance: {
        regulation: ['HIPAA', 'GDPR'],
        purpose: 'Healthcare data access for authorized operations',
        legalBasis: 'Healthcare operations and treatment',
        retentionPeriod: '7-years',
      },
      metadata: {
        timestamp: new Date(),
        recordCount: 1,
      },
    };

    await this.trackDataLineage(lineageEvent);
  }

  private async sendToDataGovernancePlatform(event: DataLineageEvent): Promise<void> {
    // Implementation would send to external data governance platform
    // For now, we'll log it as a structured event
    this.logger.log('Data lineage event for governance platform', {
      operationId: event.operationId,
      tenantId: event.tenantId,
      operationType: event.operationType,
      dataClassification: this.getHighestClassification(event.dataFields),
      complianceRegulations: event.compliance.regulation,
      containsSensitiveData: event.dataFields.some(f => 
        f.sensitivity === 'high' || f.sensitivity === 'critical'
      ),
    });
  }

  private getSeverityFromClassification(dataFields: DataLineageEvent['dataFields']): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
    const hasPHI = dataFields.some(f => f.classification === 'phi');
    const hasPII = dataFields.some(f => f.classification === 'pii');
    const hasCritical = dataFields.some(f => f.sensitivity === 'critical');
    const hasHigh = dataFields.some(f => f.sensitivity === 'high');

    if (hasPHI || hasCritical) return 'CRITICAL';
    if (hasPII || hasHigh) return 'HIGH';
    if (dataFields.some(f => f.sensitivity === 'medium')) return 'MEDIUM';
    return 'LOW';
  }

  private getHighestClassification(dataFields: DataLineageEvent['dataFields']): string {
    const priorities = ['phi', 'pii', 'confidential', 'internal', 'public'];
    for (const priority of priorities) {
      if (dataFields.some(f => f.classification === priority)) {
        return priority;
      }
    }
    return 'public';
  }

  private calculateSearchQualityScore(results: any[]): number {
    if (!results || results.length === 0) return 0;
    
    // Simple quality score based on result count and similarity scores
    const avgScore = results.reduce((sum, result) => 
      sum + (result.similarity || 0), 0) / results.length;
    
    return Math.round(avgScore * 100) / 100;
  }

  private classifyDataField(fieldName: string): 'public' | 'internal' | 'confidential' | 'phi' | 'pii' {
    const phiFields = ['ssn', 'medical_record_number', 'patient_id', 'diagnosis'];
    const piiFields = ['email', 'phone', 'address', 'name', 'birth_date'];
    const confidentialFields = ['password', 'secret', 'key', 'token'];

    const lowerField = fieldName.toLowerCase();
    
    if (phiFields.some(phi => lowerField.includes(phi))) return 'phi';
    if (piiFields.some(pii => lowerField.includes(pii))) return 'pii';
    if (confidentialFields.some(conf => lowerField.includes(conf))) return 'confidential';
    if (lowerField.includes('internal') || lowerField.includes('private')) return 'internal';
    
    return 'public';
  }

  private getFieldSensitivity(fieldName: string): 'low' | 'medium' | 'high' | 'critical' {
    const classification = this.classifyDataField(fieldName);
    
    switch (classification) {
      case 'phi': return 'critical';
      case 'pii': return 'high';
      case 'confidential': return 'high';
      case 'internal': return 'medium';
      default: return 'low';
    }
  }
}