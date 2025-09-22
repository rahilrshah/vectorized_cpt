import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

export interface DataClassificationResult {
  classification: 'public' | 'internal' | 'confidential' | 'phi' | 'pii';
  sensitivity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  reasons: string[];
  appliedRules: string[];
  recommendations: string[];
}

export interface ClassificationRule {
  id: string;
  name: string;
  description: string;
  pattern: RegExp | string;
  classification: DataClassificationResult['classification'];
  sensitivity: DataClassificationResult['sensitivity'];
  confidence: number;
  priority: number;
}

@Injectable()
export class DataClassificationService {
  private readonly logger = new Logger(DataClassificationService.name);
  private readonly classificationRules: ClassificationRule[];

  constructor(private readonly configService: ConfigService) {
    this.classificationRules = this.initializeClassificationRules();
  }

  async classifyData(
    data: string | Record<string, any>,
    context?: {
      fieldName?: string;
      dataType?: string;
      source?: string;
      tenantId?: string;
    },
  ): Promise<DataClassificationResult> {
    try {
      const textData = typeof data === 'string' ? data : JSON.stringify(data);
      const appliedRules: ClassificationRule[] = [];
      const reasons: string[] = [];

      // Apply classification rules
      for (const rule of this.classificationRules) {
        if (this.ruleMatches(rule, textData, context)) {
          appliedRules.push(rule);
          reasons.push(`Matched rule: ${rule.name}`);
        }
      }

      // Determine final classification based on highest priority and sensitivity
      const finalClassification = this.determineClassification(appliedRules, textData, context);

      // Generate recommendations
      const recommendations = this.generateRecommendations(finalClassification, appliedRules);

      const result: DataClassificationResult = {
        classification: finalClassification.classification,
        sensitivity: finalClassification.sensitivity,
        confidence: finalClassification.confidence,
        reasons,
        appliedRules: appliedRules.map(rule => rule.id),
        recommendations,
      };

      this.logger.log('Data classification completed', {
        classification: result.classification,
        sensitivity: result.sensitivity,
        confidence: result.confidence,
        ruleCount: appliedRules.length,
        fieldName: context?.fieldName,
        tenantId: context?.tenantId,
      });

      return result;

    } catch (error) {
      this.logger.error('Data classification failed', {
        error: error.message,
        fieldName: context?.fieldName,
        dataType: context?.dataType,
      });

      // Return safe default classification
      return {
        classification: 'internal',
        sensitivity: 'medium',
        confidence: 0.5,
        reasons: ['Classification failed, using default'],
        appliedRules: [],
        recommendations: ['Manual review required due to classification error'],
      };
    }
  }

  async classifyMedicalText(text: string, tenantId: string): Promise<DataClassificationResult> {
    const medicalContext = {
      fieldName: 'medical_text',
      dataType: 'text',
      source: 'medical_note',
      tenantId,
    };

    // Check for PHI patterns in medical text
    const result = await this.classifyData(text, medicalContext);

    // Medical text specific enhancements
    if (this.containsMedicalTerminology(text)) {
      result.reasons.push('Contains medical terminology');
      
      if (this.containsPatientIdentifiers(text)) {
        result.classification = 'phi';
        result.sensitivity = 'critical';
        result.confidence = Math.min(result.confidence + 0.3, 1.0);
        result.reasons.push('Contains potential patient identifiers');
      }
    }

    return result;
  }

  private initializeClassificationRules(): ClassificationRule[] {
    return [
      // PHI Rules
      {
        id: 'phi-ssn',
        name: 'Social Security Number',
        description: 'Detects SSN patterns',
        pattern: /\b\d{3}-\d{2}-\d{4}\b/,
        classification: 'phi',
        sensitivity: 'critical',
        confidence: 0.95,
        priority: 1,
      },
      {
        id: 'phi-mrn',
        name: 'Medical Record Number',
        description: 'Detects MRN patterns',
        pattern: /\b(MRN|mrn|medical.?record.?number).{0,10}\d{6,}\b/i,
        classification: 'phi',
        sensitivity: 'critical',
        confidence: 0.9,
        priority: 1,
      },
      {
        id: 'phi-patient-id',
        name: 'Patient Identifier',
        description: 'Detects patient ID patterns',
        pattern: /\b(patient.?id|patient.?number).{0,10}[A-Z0-9]{6,}\b/i,
        classification: 'phi',
        sensitivity: 'critical',
        confidence: 0.85,
        priority: 1,
      },
      
      // PII Rules
      {
        id: 'pii-email',
        name: 'Email Address',
        description: 'Detects email addresses',
        pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/,
        classification: 'pii',
        sensitivity: 'high',
        confidence: 0.95,
        priority: 2,
      },
      {
        id: 'pii-phone',
        name: 'Phone Number',
        description: 'Detects phone number patterns',
        pattern: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/,
        classification: 'pii',
        sensitivity: 'high',
        confidence: 0.8,
        priority: 2,
      },
      
      // Medical Terminology
      {
        id: 'medical-diagnosis',
        name: 'Medical Diagnosis',
        description: 'Detects diagnostic terminology',
        pattern: /(diagnosis|diagnosed|condition|syndrome|disease|disorder)/i,
        classification: 'internal',
        sensitivity: 'medium',
        confidence: 0.7,
        priority: 3,
      },
      {
        id: 'medical-procedure',
        name: 'Medical Procedure',
        description: 'Detects procedure terminology',
        pattern: /(surgery|procedure|operation|treatment|therapy|injection)/i,
        classification: 'internal',
        sensitivity: 'medium',
        confidence: 0.7,
        priority: 3,
      },
      
      // CPT Codes
      {
        id: 'cpt-code',
        name: 'CPT Code',
        description: 'Detects CPT code patterns',
        pattern: /\b\d{5}\b/,
        classification: 'public',
        sensitivity: 'low',
        confidence: 0.6,
        priority: 4,
      },
      
      // Confidential Data
      {
        id: 'confidential-credentials',
        name: 'Credentials',
        description: 'Detects credential patterns',
        pattern: /(password|secret|key|token|credential)/i,
        classification: 'confidential',
        sensitivity: 'high',
        confidence: 0.9,
        priority: 2,
      },
    ];
  }

  private ruleMatches(
    rule: ClassificationRule,
    data: string,
    context?: any,
  ): boolean {
    if (rule.pattern instanceof RegExp) {
      return rule.pattern.test(data);
    } else {
      return data.toLowerCase().includes(rule.pattern.toLowerCase());
    }
  }

  private determineClassification(
    appliedRules: ClassificationRule[],
    data: string,
    context?: any,
  ): {
    classification: DataClassificationResult['classification'];
    sensitivity: DataClassificationResult['sensitivity'];
    confidence: number;
  } {
    if (appliedRules.length === 0) {
      return {
        classification: 'internal',
        sensitivity: 'low',
        confidence: 0.5,
      };
    }

    // Sort by priority and sensitivity
    const sortedRules = appliedRules.sort((a, b) => {
      if (a.priority !== b.priority) return a.priority - b.priority;
      const sensitivityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return sensitivityOrder[b.sensitivity] - sensitivityOrder[a.sensitivity];
    });

    const topRule = sortedRules[0];
    const avgConfidence = appliedRules.reduce((sum, rule) => sum + rule.confidence, 0) / appliedRules.length;

    return {
      classification: topRule.classification,
      sensitivity: topRule.sensitivity,
      confidence: avgConfidence,
    };
  }

  private generateRecommendations(
    classification: DataClassificationResult,
    appliedRules: ClassificationRule[],
  ): string[] {
    const recommendations: string[] = [];

    if (classification.classification === 'phi' || classification.classification === 'pii') {
      recommendations.push('Ensure HIPAA compliance measures are in place');
      recommendations.push('Apply encryption for data at rest and in transit');
      recommendations.push('Implement access controls and audit logging');
      recommendations.push('Consider data minimization techniques');
    }

    if (classification.sensitivity === 'critical' || classification.sensitivity === 'high') {
      recommendations.push('Restrict access to authorized personnel only');
      recommendations.push('Enable enhanced monitoring and alerting');
      recommendations.push('Consider data redaction for non-essential uses');
    }

    if (classification.confidence < 0.7) {
      recommendations.push('Manual review recommended due to low confidence');
      recommendations.push('Consider additional classification rules');
    }

    return recommendations;
  }

  private containsMedicalTerminology(text: string): boolean {
    const medicalTerms = [
      'patient', 'diagnosis', 'treatment', 'therapy', 'medication', 'surgery',
      'procedure', 'symptom', 'condition', 'disease', 'disorder', 'syndrome',
      'examination', 'assessment', 'prognosis', 'pathology', 'radiology',
    ];

    const lowerText = text.toLowerCase();
    return medicalTerms.some(term => lowerText.includes(term));
  }

  private containsPatientIdentifiers(text: string): boolean {
    const identifierPatterns = [
      /\b(patient|mr|mrs|ms)\.?\s+[A-Z][a-z]+/,  // Patient names
      /\b(dob|date.?of.?birth).{0,10}\d{1,2}\/\d{1,2}\/\d{2,4}/i,  // DOB
      /\b\d{3}-\d{2}-\d{4}\b/,  // SSN
      /\b[A-Z]{2}\d{6,}\b/,  // ID patterns
    ];

    return identifierPatterns.some(pattern => pattern.test(text));
  }
}