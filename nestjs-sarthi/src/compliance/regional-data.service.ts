import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

export interface RegionalConfig {
  region: string;
  isEU: boolean;
  requiresGDPR: boolean;
  requiresHIPAA: boolean;
  requiresPIPEDA: boolean;
  encryptionRequired: boolean;
  localProcessingRequired: boolean;
  crossBorderAllowed: boolean;
  dataResidencyRequired: boolean;
  auditLogRetention: string;
}

export interface DataOperation {
  type: 'read' | 'write' | 'process' | 'transfer' | 'delete';
  dataClassification: 'public' | 'internal' | 'confidential' | 'phi' | 'pii';
  sourceRegion: string;
  targetRegion?: string;
  tenantId: string;
  userId: string;
}

@Injectable()
export class RegionalDataService {
  private readonly logger = new Logger(RegionalDataService.name);
  private readonly regionalConfigs: Map<string, RegionalConfig>;

  constructor(private readonly configService: ConfigService) {
    this.regionalConfigs = this.initializeRegionalConfigs();
  }

  async getRegionalConfiguration(region: string): Promise<RegionalConfig | null> {
    return this.regionalConfigs.get(region) || null;
  }

  async determineDataProcessingRegion(
    tenantId: string,
    userRegion: string,
    dataClassification: string,
    preferredRegion?: string,
  ): Promise<{
    region: string;
    reasoning: string;
    complianceNotes: string[];
  }> {
    try {
      const userConfig = this.regionalConfigs.get(userRegion);
      
      if (!userConfig) {
        // Default to US region for unknown regions
        return {
          region: 'us-central1',
          reasoning: 'Unknown user region, defaulting to US for data processing',
          complianceNotes: ['Manual compliance review recommended for unknown regions'],
        };
      }

      // Check if user is in a data residency-required region
      if (userConfig.dataResidencyRequired) {
        return {
          region: userRegion,
          reasoning: 'Data residency requirements mandate processing in user region',
          complianceNotes: [
            'Data must be processed locally due to regional regulations',
            `Applicable regulations: ${this.getApplicableRegulations(userConfig)}`,
          ],
        };
      }

      // Check preferred region compliance
      if (preferredRegion) {
        const preferredConfig = this.regionalConfigs.get(preferredRegion);
        if (preferredConfig && this.canProcessInRegion(userConfig, preferredConfig, dataClassification)) {
          return {
            region: preferredRegion,
            reasoning: 'Preferred region is compliant for data processing',
            complianceNotes: [
              'Cross-border processing approved',
              'Adequate safeguards in place',
            ],
          };
        }
      }

      // Default to user region for sensitive data
      if (dataClassification === 'phi' || dataClassification === 'pii') {
        return {
          region: userRegion,
          reasoning: 'Sensitive data requires processing in user region',
          complianceNotes: [
            'PHI/PII data processed locally for enhanced privacy protection',
            'Cross-border transfer restrictions apply',
          ],
        };
      }

      // For non-sensitive data, allow optimal region selection
      const optimalRegion = this.selectOptimalRegion(userConfig, dataClassification);
      return {
        region: optimalRegion,
        reasoning: 'Selected optimal region for non-sensitive data processing',
        complianceNotes: [
          'Standard compliance measures apply',
          'Performance optimized region selection',
        ],
      };

    } catch (error) {
      this.logger.error('Failed to determine data processing region', {
        error: error.message,
        tenantId,
        userRegion,
        dataClassification,
      });

      return {
        region: 'us-central1',
        reasoning: 'Error in region determination, using safe default',
        complianceNotes: ['Manual review required due to processing error'],
      };
    }
  }

  async validateDataOperation(operation: DataOperation): Promise<{
    allowed: boolean;
    reason: string;
    requiredSafeguards: string[];
    complianceRisk: 'low' | 'medium' | 'high' | 'critical';
  }> {
    try {
      const sourceConfig = this.regionalConfigs.get(operation.sourceRegion);
      const targetConfig = operation.targetRegion ? this.regionalConfigs.get(operation.targetRegion) : null;

      if (!sourceConfig) {
        return {
          allowed: false,
          reason: 'Unknown source region',
          requiredSafeguards: ['Manual compliance review'],
          complianceRisk: 'high',
        };
      }

      const requiredSafeguards = [];
      let complianceRisk: 'low' | 'medium' | 'high' | 'critical' = 'low';

      // Cross-border operation validation
      if (operation.targetRegion && operation.sourceRegion !== operation.targetRegion) {
        if (!sourceConfig.crossBorderAllowed) {
          return {
            allowed: false,
            reason: 'Cross-border data operations not permitted from source region',
            requiredSafeguards: ['Local processing only'],
            complianceRisk: 'critical',
          };
        }

        if (!targetConfig) {
          return {
            allowed: false,
            reason: 'Unknown target region for cross-border operation',
            requiredSafeguards: ['Verify target region compliance'],
            complianceRisk: 'high',
          };
        }

        // Add cross-border safeguards
        requiredSafeguards.push('Standard Contractual Clauses');
        requiredSafeguards.push('Adequate encryption');
        complianceRisk = 'medium';

        // GDPR specific requirements
        if (sourceConfig.requiresGDPR || (targetConfig && targetConfig.requiresGDPR)) {
          requiredSafeguards.push('GDPR adequacy assessment');
          requiredSafeguards.push('Data subject consent verification');
          complianceRisk = 'high';
        }
      }

      // Sensitive data validation
      if (operation.dataClassification === 'phi') {
        requiredSafeguards.push('HIPAA safeguards');
        requiredSafeguards.push('End-to-end encryption');
        requiredSafeguards.push('Access audit logging');
        
        if (sourceConfig.requiresGDPR) {
          requiredSafeguards.push('GDPR special category data protections');
          complianceRisk = 'high';
        }
      }

      if (operation.dataClassification === 'pii') {
        if (sourceConfig.requiresGDPR) {
          requiredSafeguards.push('GDPR lawful basis verification');
          requiredSafeguards.push('Data minimization principles');
        }
        if (sourceConfig.requiresPIPEDA) {
          requiredSafeguards.push('PIPEDA consent requirements');
        }
      }

      // Encryption requirements
      if (sourceConfig.encryptionRequired) {
        requiredSafeguards.push('Data encryption at rest and in transit');
      }

      return {
        allowed: true,
        reason: 'Operation permitted with required safeguards',
        requiredSafeguards,
        complianceRisk,
      };

    } catch (error) {
      this.logger.error('Data operation validation failed', {
        error: error.message,
        operation,
      });

      return {
        allowed: false,
        reason: 'Validation error occurred',
        requiredSafeguards: ['Manual compliance review required'],
        complianceRisk: 'critical',
      };
    }
  }

  async getDataRetentionPolicy(region: string, dataClassification: string): Promise<{
    minimumRetention: string;
    maximumRetention: string;
    deletionRequired: boolean;
    rightToErasure: boolean;
    archivalAllowed: boolean;
  }> {
    const config = this.regionalConfigs.get(region);
    
    if (!config) {
      // Default policy
      return {
        minimumRetention: '1-year',
        maximumRetention: '7-years',
        deletionRequired: true,
        rightToErasure: false,
        archivalAllowed: true,
      };
    }

    // HIPAA requirements
    if (config.requiresHIPAA && dataClassification === 'phi') {
      return {
        minimumRetention: '6-years',
        maximumRetention: '7-years',
        deletionRequired: true,
        rightToErasure: false,
        archivalAllowed: true,
      };
    }

    // GDPR requirements
    if (config.requiresGDPR && (dataClassification === 'pii' || dataClassification === 'phi')) {
      return {
        minimumRetention: '0-days',
        maximumRetention: '10-years',
        deletionRequired: true,
        rightToErasure: true,
        archivalAllowed: false,
      };
    }

    // PIPEDA requirements
    if (config.requiresPIPEDA && dataClassification === 'pii') {
      return {
        minimumRetention: '1-year',
        maximumRetention: '7-years',
        deletionRequired: true,
        rightToErasure: true,
        archivalAllowed: true,
      };
    }

    // Default policy for other cases
    return {
      minimumRetention: '1-year',
      maximumRetention: '7-years',
      deletionRequired: true,
      rightToErasure: config.requiresGDPR,
      archivalAllowed: true,
    };
  }

  private initializeRegionalConfigs(): Map<string, RegionalConfig> {
    const configs = new Map<string, RegionalConfig>();

    // US Regions
    configs.set('us-central1', {
      region: 'us-central1',
      isEU: false,
      requiresGDPR: false,
      requiresHIPAA: true,
      requiresPIPEDA: false,
      encryptionRequired: true,
      localProcessingRequired: false,
      crossBorderAllowed: true,
      dataResidencyRequired: false,
      auditLogRetention: '7-years',
    });

    configs.set('us-east1', {
      region: 'us-east1',
      isEU: false,
      requiresGDPR: false,
      requiresHIPAA: true,
      requiresPIPEDA: false,
      encryptionRequired: true,
      localProcessingRequired: false,
      crossBorderAllowed: true,
      dataResidencyRequired: false,
      auditLogRetention: '7-years',
    });

    // EU Regions
    configs.set('europe-west1', {
      region: 'europe-west1',
      isEU: true,
      requiresGDPR: true,
      requiresHIPAA: false,
      requiresPIPEDA: false,
      encryptionRequired: true,
      localProcessingRequired: true,
      crossBorderAllowed: false,
      dataResidencyRequired: true,
      auditLogRetention: '3-years',
    });

    configs.set('europe-west3', {
      region: 'europe-west3',
      isEU: true,
      requiresGDPR: true,
      requiresHIPAA: false,
      requiresPIPEDA: false,
      encryptionRequired: true,
      localProcessingRequired: true,
      crossBorderAllowed: false,
      dataResidencyRequired: true,
      auditLogRetention: '3-years',
    });

    // Canada Regions
    configs.set('northamerica-northeast1', {
      region: 'northamerica-northeast1',
      isEU: false,
      requiresGDPR: false,
      requiresHIPAA: false,
      requiresPIPEDA: true,
      encryptionRequired: true,
      localProcessingRequired: true,
      crossBorderAllowed: false,
      dataResidencyRequired: true,
      auditLogRetention: '7-years',
    });

    return configs;
  }

  private canProcessInRegion(
    userConfig: RegionalConfig,
    targetConfig: RegionalConfig,
    dataClassification: string,
  ): boolean {
    // Sensitive data restrictions
    if ((dataClassification === 'phi' || dataClassification === 'pii') && userConfig.localProcessingRequired) {
      return false;
    }

    // Cross-border allowance
    if (!userConfig.crossBorderAllowed) {
      return false;
    }

    // GDPR restrictions
    if (userConfig.requiresGDPR && !targetConfig.isEU && dataClassification === 'pii') {
      return false;
    }

    return true;
  }

  private selectOptimalRegion(userConfig: RegionalConfig, dataClassification: string): string {
    // For non-sensitive data, prioritize performance regions
    if (dataClassification === 'public' || dataClassification === 'internal') {
      return userConfig.region; // Keep in user region for optimal latency
    }

    // For sensitive data, prioritize security regions
    return userConfig.region;
  }

  private getApplicableRegulations(config: RegionalConfig): string {
    const regulations = [];
    if (config.requiresGDPR) regulations.push('GDPR');
    if (config.requiresHIPAA) regulations.push('HIPAA');
    if (config.requiresPIPEDA) regulations.push('PIPEDA');
    return regulations.join(', ');
  }
}