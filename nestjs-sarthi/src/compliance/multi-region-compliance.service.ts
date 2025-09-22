import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AuditService } from '../audit/audit.service';

export interface RegionComplianceRules {
  region: string;
  regulations: string[];
  dataResidency: {
    required: boolean;
    allowedRegions: string[];
    encryptionRequired: boolean;
    localProcessingOnly: boolean;
  };
  crossBorderTransfer: {
    allowed: boolean;
    requiresConsent: boolean;
    adequacyDecision: boolean;
    safeguards: string[];
  };
  retentionRules: {
    minimumPeriod: string;
    maximumPeriod: string;
    deletionRequired: boolean;
    rightToErasure: boolean;
  };
  auditRequirements: {
    logRetention: string;
    reportingFrequency: string;
    externalAudits: boolean;
    realTimeMonitoring: boolean;
  };
}

export interface ComplianceAssessment {
  compliant: boolean;
  region: string;
  regulations: string[];
  violations: {
    type: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    remediation: string;
  }[];
  recommendations: string[];
  riskScore: number;
}

@Injectable()
export class MultiRegionComplianceService {
  private readonly logger = new Logger(MultiRegionComplianceService.name);
  private readonly complianceRules: Map<string, RegionComplianceRules>;

  constructor(
    private readonly configService: ConfigService,
    private readonly auditService: AuditService,
  ) {
    this.complianceRules = this.initializeComplianceRules();
  }

  async assessCompliance(
    tenantId: string,
    dataLocation: string,
    dataClassification: string,
    operation: {
      type: string;
      sourceRegion: string;
      targetRegion?: string;
      crossBorder: boolean;
    },
  ): Promise<ComplianceAssessment> {
    try {
      const sourceRules = this.complianceRules.get(operation.sourceRegion);
      const targetRules = operation.targetRegion ? this.complianceRules.get(operation.targetRegion) : null;

      if (!sourceRules) {
        throw new Error(`No compliance rules found for region: ${operation.sourceRegion}`);
      }

      const violations = [];
      const recommendations = [];
      let riskScore = 0;

      // Data residency compliance
      const residencyCheck = this.checkDataResidency(dataLocation, sourceRules, dataClassification);
      if (!residencyCheck.compliant) {
        violations.push(...residencyCheck.violations);
        riskScore += residencyCheck.riskScore;
      }

      // Cross-border transfer compliance
      if (operation.crossBorder && targetRules) {
        const transferCheck = this.checkCrossBorderTransfer(sourceRules, targetRules, dataClassification);
        if (!transferCheck.compliant) {
          violations.push(...transferCheck.violations);
          riskScore += transferCheck.riskScore;
        }
      }

      // Data classification compliance
      const classificationCheck = this.checkDataClassification(dataClassification, sourceRules);
      if (!classificationCheck.compliant) {
        violations.push(...classificationCheck.violations);
        riskScore += classificationCheck.riskScore;
      }

      // Retention compliance
      const retentionCheck = this.checkRetentionCompliance(operation.type, sourceRules);
      recommendations.push(...retentionCheck.recommendations);

      // Generate recommendations
      recommendations.push(...this.generateRecommendations(violations, sourceRules));

      const assessment: ComplianceAssessment = {
        compliant: violations.length === 0,
        region: operation.sourceRegion,
        regulations: sourceRules.regulations,
        violations,
        recommendations,
        riskScore: Math.min(100, riskScore),
      };

      // Log compliance assessment
      await this.logComplianceAssessment(tenantId, assessment, operation);

      this.logger.log('Compliance assessment completed', {
        tenantId,
        region: operation.sourceRegion,
        compliant: assessment.compliant,
        violationCount: violations.length,
        riskScore: assessment.riskScore,
      });

      return assessment;

    } catch (error) {
      this.logger.error('Compliance assessment failed', {
        error: error.message,
        tenantId,
        operation,
      });

      return {
        compliant: false,
        region: operation.sourceRegion,
        regulations: [],
        violations: [{
          type: 'assessment_error',
          severity: 'high',
          description: `Compliance assessment failed: ${error.message}`,
          remediation: 'Contact compliance team for manual review',
        }],
        recommendations: ['Manual compliance review required'],
        riskScore: 75,
      };
    }
  }

  async enforceDataSovereignty(
    tenantId: string,
    dataType: string,
    requestedRegion: string,
    userRegion: string,
  ): Promise<{
    allowed: boolean;
    enforcedRegion: string;
    reason: string;
  }> {
    try {
      const rules = this.complianceRules.get(userRegion);
      if (!rules) {
        return {
          allowed: false,
          enforcedRegion: 'us-central1',
          reason: `No compliance rules for region ${userRegion}`,
        };
      }

      // Check if data can be processed in requested region
      if (rules.dataResidency.required) {
        if (!rules.dataResidency.allowedRegions.includes(requestedRegion)) {
          return {
            allowed: false,
            enforcedRegion: rules.dataResidency.allowedRegions[0],
            reason: 'Data residency requirements enforce local processing',
          };
        }
      }

      // Check cross-border restrictions
      if (requestedRegion !== userRegion && !rules.crossBorderTransfer.allowed) {
        return {
          allowed: false,
          enforcedRegion: userRegion,
          reason: 'Cross-border data transfer not permitted',
        };
      }

      return {
        allowed: true,
        enforcedRegion: requestedRegion,
        reason: 'Request complies with data sovereignty rules',
      };

    } catch (error) {
      this.logger.error('Data sovereignty enforcement failed', {
        error: error.message,
        tenantId,
        requestedRegion,
        userRegion,
      });

      return {
        allowed: false,
        enforcedRegion: 'us-central1',
        reason: 'Error in sovereignty check, defaulting to secure region',
      };
    }
  }

  private initializeComplianceRules(): Map<string, RegionComplianceRules> {
    const rules = new Map<string, RegionComplianceRules>();

    // United States - HIPAA
    rules.set('us-central1', {
      region: 'us-central1',
      regulations: ['HIPAA', 'SOX', 'CCPA'],
      dataResidency: {
        required: true,
        allowedRegions: ['us-central1', 'us-east1', 'us-west1'],
        encryptionRequired: true,
        localProcessingOnly: false,
      },
      crossBorderTransfer: {
        allowed: true,
        requiresConsent: false,
        adequacyDecision: true,
        safeguards: ['Standard Contractual Clauses', 'Encryption', 'Access Controls'],
      },
      retentionRules: {
        minimumPeriod: '6-years',
        maximumPeriod: '7-years',
        deletionRequired: true,
        rightToErasure: false,
      },
      auditRequirements: {
        logRetention: '7-years',
        reportingFrequency: 'annual',
        externalAudits: true,
        realTimeMonitoring: true,
      },
    });

    // European Union - GDPR
    rules.set('europe-west1', {
      region: 'europe-west1',
      regulations: ['GDPR', 'Medical Device Regulation (MDR)'],
      dataResidency: {
        required: true,
        allowedRegions: ['europe-west1', 'europe-west3', 'europe-west4'],
        encryptionRequired: true,
        localProcessingOnly: true,
      },
      crossBorderTransfer: {
        allowed: false,
        requiresConsent: true,
        adequacyDecision: false,
        safeguards: ['Standard Contractual Clauses', 'Binding Corporate Rules', 'Adequate Encryption'],
      },
      retentionRules: {
        minimumPeriod: '0-years',
        maximumPeriod: '10-years',
        deletionRequired: true,
        rightToErasure: true,
      },
      auditRequirements: {
        logRetention: '3-years',
        reportingFrequency: 'continuous',
        externalAudits: true,
        realTimeMonitoring: true,
      },
    });

    // Canada - PIPEDA
    rules.set('northamerica-northeast1', {
      region: 'northamerica-northeast1',
      regulations: ['PIPEDA', 'Personal Health Information Protection Act (PHIPA)'],
      dataResidency: {
        required: true,
        allowedRegions: ['northamerica-northeast1', 'northamerica-northeast2'],
        encryptionRequired: true,
        localProcessingOnly: true,
      },
      crossBorderTransfer: {
        allowed: false,
        requiresConsent: true,
        adequacyDecision: false,
        safeguards: ['Adequate Level of Protection', 'Explicit Consent', 'Contractual Safeguards'],
      },
      retentionRules: {
        minimumPeriod: '1-year',
        maximumPeriod: '7-years',
        deletionRequired: true,
        rightToErasure: true,
      },
      auditRequirements: {
        logRetention: '7-years',
        reportingFrequency: 'annual',
        externalAudits: false,
        realTimeMonitoring: false,
      },
    });

    return rules;
  }

  private checkDataResidency(
    dataLocation: string,
    rules: RegionComplianceRules,
    dataClassification: string,
  ): { compliant: boolean; violations: any[]; riskScore: number } {
    const violations = [];
    let riskScore = 0;

    if (rules.dataResidency.required && !rules.dataResidency.allowedRegions.includes(dataLocation)) {
      violations.push({
        type: 'data_residency',
        severity: dataClassification === 'phi' ? 'critical' : 'high',
        description: `Data must be stored in allowed regions: ${rules.dataResidency.allowedRegions.join(', ')}`,
        remediation: `Move data to compliant region or implement data sovereignty controls`,
      });
      riskScore += dataClassification === 'phi' ? 40 : 25;
    }

    if (rules.dataResidency.localProcessingOnly && dataLocation !== rules.region) {
      violations.push({
        type: 'local_processing',
        severity: 'high',
        description: 'Data must be processed locally within the region',
        remediation: 'Ensure processing occurs within the same region as data storage',
      });
      riskScore += 20;
    }

    return { compliant: violations.length === 0, violations, riskScore };
  }

  private checkCrossBorderTransfer(
    sourceRules: RegionComplianceRules,
    targetRules: RegionComplianceRules,
    dataClassification: string,
  ): { compliant: boolean; violations: any[]; riskScore: number } {
    const violations = [];
    let riskScore = 0;

    if (!sourceRules.crossBorderTransfer.allowed) {
      violations.push({
        type: 'cross_border_prohibited',
        severity: 'critical',
        description: 'Cross-border data transfer is prohibited by source region regulations',
        remediation: 'Process data locally or implement adequate safeguards',
      });
      riskScore += 50;
    }

    if (sourceRules.crossBorderTransfer.requiresConsent && dataClassification === 'phi') {
      violations.push({
        type: 'consent_required',
        severity: 'high',
        description: 'Explicit consent required for cross-border transfer of healthcare data',
        remediation: 'Obtain explicit consent or use anonymized data',
      });
      riskScore += 30;
    }

    if (!sourceRules.crossBorderTransfer.adequacyDecision && !targetRules.crossBorderTransfer.adequacyDecision) {
      violations.push({
        type: 'adequacy_decision',
        severity: 'medium',
        description: 'No adequacy decision exists between source and target regions',
        remediation: 'Implement additional safeguards such as Standard Contractual Clauses',
      });
      riskScore += 15;
    }

    return { compliant: violations.length === 0, violations, riskScore };
  }

  private checkDataClassification(
    dataClassification: string,
    rules: RegionComplianceRules,
  ): { compliant: boolean; violations: any[]; riskScore: number } {
    const violations = [];
    let riskScore = 0;

    if (dataClassification === 'phi' && !rules.dataResidency.encryptionRequired) {
      violations.push({
        type: 'encryption_required',
        severity: 'critical',
        description: 'PHI data requires encryption at rest and in transit',
        remediation: 'Enable encryption for all PHI data',
      });
      riskScore += 35;
    }

    return { compliant: violations.length === 0, violations, riskScore };
  }

  private checkRetentionCompliance(
    operationType: string,
    rules: RegionComplianceRules,
  ): { recommendations: string[] } {
    const recommendations = [];

    recommendations.push(`Ensure data retention complies with ${rules.retentionRules.minimumPeriod} minimum period`);
    recommendations.push(`Data must be deleted after ${rules.retentionRules.maximumPeriod} maximum period`);

    if (rules.retentionRules.rightToErasure) {
      recommendations.push('Implement right to erasure procedures for individual data subjects');
    }

    return { recommendations };
  }

  private generateRecommendations(violations: any[], rules: RegionComplianceRules): string[] {
    const recommendations = [];

    if (violations.some(v => v.type === 'data_residency')) {
      recommendations.push('Implement data localization controls');
      recommendations.push('Review and update data storage locations');
    }

    if (violations.some(v => v.type === 'cross_border_prohibited')) {
      recommendations.push('Implement local processing workflows');
      recommendations.push('Consider data anonymization for cross-border operations');
    }

    if (violations.some(v => v.severity === 'critical')) {
      recommendations.push('Immediate remediation required for critical compliance violations');
      recommendations.push('Consider suspending operations until compliance is achieved');
    }

    recommendations.push('Regular compliance audits recommended');
    recommendations.push('Monitor regulatory changes for ongoing compliance');

    return recommendations;
  }

  private async logComplianceAssessment(
    tenantId: string,
    assessment: ComplianceAssessment,
    operation: any,
  ): Promise<void> {
    await this.auditService.logEvent({
      tenantId,
      eventType: 'COMPLIANCE_ASSESSMENT',
      severity: assessment.compliant ? 'LOW' : (assessment.riskScore > 50 ? 'CRITICAL' : 'HIGH'),
      resourceType: 'compliance',
      action: 'ASSESS_COMPLIANCE',
      description: 'Multi-region compliance assessment',
      ipAddress: 'internal',
      additionalData: {
        region: assessment.region,
        regulations: assessment.regulations,
        compliant: assessment.compliant,
        violationCount: assessment.violations.length,
        riskScore: assessment.riskScore,
        operation,
      },
      complianceFlags: {
        multiRegionCompliance: true,
        riskScore: assessment.riskScore,
        regulations: assessment.regulations,
        dataResidencyCompliant: !assessment.violations.some(v => v.type === 'data_residency'),
        crossBorderCompliant: !assessment.violations.some(v => v.type.includes('cross_border')),
      },
    });
  }
}