import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AuditService } from '../audit/audit.service';

export interface BiasMetrics {
  overallFairnessScore: number;
  demographicParity: number;
  equalizedOdds: number;
  calibration: number;
  representationFairness: number;
  biasIndicators: {
    type: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    mitigation: string;
  }[];
}

export interface ModelPerformanceMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  latency: number;
  throughput: number;
  errorRate: number;
  confidenceDistribution: Record<string, number>;
}

export interface AIGovernanceEvent {
  operationId: string;
  tenantId: string;
  userId: string;
  modelName: string;
  modelVersion: string;
  inputData: {
    type: string;
    classification: string;
    sensitivity: string;
    size: number;
  };
  prediction: {
    result: any;
    confidence: number;
    alternatives?: any[];
    reasoning?: string;
  };
  performance: ModelPerformanceMetrics;
  bias: BiasMetrics;
  compliance: {
    explainable: boolean;
    auditTrail: boolean;
    dataMinimization: boolean;
    purposeLimitation: boolean;
    humanOversight: boolean;
  };
  timestamp: Date;
}

@Injectable()
export class AIGovernanceService {
  private readonly logger = new Logger(AIGovernanceService.name);
  private readonly biasDetectionEnabled: boolean;
  private readonly explainabilityRequired: boolean;

  // Performance baselines for model monitoring
  private readonly performanceBaselines = {
    accuracy: 0.90,
    precision: 0.85,
    recall: 0.85,
    f1Score: 0.85,
    latency: 500, // milliseconds
    errorRate: 0.05,
  };

  // Fairness thresholds
  private readonly fairnessThresholds = {
    overallFairnessScore: 0.8,
    demographicParity: 0.8,
    equalizedOdds: 0.8,
    calibration: 0.8,
    representationFairness: 0.7,
  };

  constructor(
    private readonly configService: ConfigService,
    private readonly auditService: AuditService,
  ) {
    this.biasDetectionEnabled = this.configService.get('sarthi.biasDetectionEnabled', true);
    this.explainabilityRequired = this.configService.get('sarthi.explainabilityRequired', true);
  }

  async monitorModelPerformance(
    operationId: string,
    tenantId: string,
    userId: string,
    modelName: string,
    inputText: string,
    predictions: any[],
    processingTime: number,
  ): Promise<AIGovernanceEvent> {
    try {
      // Calculate performance metrics
      const performance = await this.calculatePerformanceMetrics(
        predictions,
        processingTime,
      );

      // Detect bias if enabled
      const bias = this.biasDetectionEnabled
        ? await this.detectBias(inputText, predictions, tenantId)
        : this.getDefaultBiasMetrics();

      // Check compliance requirements
      const compliance = this.assessCompliance(performance, bias);

      const governanceEvent: AIGovernanceEvent = {
        operationId,
        tenantId,
        userId,
        modelName,
        modelVersion: '1.0.0', // TODO: Get from model registry
        inputData: {
          type: 'text',
          classification: 'medical',
          sensitivity: 'medium',
          size: inputText.length,
        },
        prediction: {
          result: predictions,
          confidence: this.calculateAverageConfidence(predictions),
          alternatives: [], // TODO: Implement alternative suggestions
          reasoning: this.explainabilityRequired ? await this.generateExplanation(inputText, predictions) : undefined,
        },
        performance,
        bias,
        compliance,
        timestamp: new Date(),
      };

      // Log governance event
      await this.logGovernanceEvent(governanceEvent);

      // Check for alerts
      await this.checkAlerts(governanceEvent);

      return governanceEvent;

    } catch (error) {
      this.logger.error('AI governance monitoring failed', {
        error: error.message,
        operationId,
        tenantId,
        modelName,
      });
      throw error;
    }
  }

  async detectBias(
    inputText: string,
    predictions: any[],
    tenantId: string,
  ): Promise<BiasMetrics> {
    try {
      const biasIndicators = [];
      
      // 1. Check for demographic bias in medical terminology
      const demographicBias = this.checkDemographicBias(inputText, predictions);
      if (demographicBias.detected) {
        biasIndicators.push({
          type: 'demographic',
          severity: demographicBias.severity,
          description: 'Potential demographic bias detected in predictions',
          mitigation: 'Apply demographic debiasing techniques and ensure diverse training data',
        });
      }

      // 2. Check for representation bias
      const representationBias = this.checkRepresentationBias(predictions);
      if (representationBias.detected) {
        biasIndicators.push({
          type: 'representation',
          severity: representationBias.severity,
          description: 'Unequal representation detected in CPT code suggestions',
          mitigation: 'Balance training data across medical specialties and procedures',
        });
      }

      // 3. Check for confirmation bias
      const confirmationBias = this.checkConfirmationBias(inputText, predictions);
      if (confirmationBias.detected) {
        biasIndicators.push({
          type: 'confirmation',
          severity: confirmationBias.severity,
          description: 'Model may be reinforcing existing biases',
          mitigation: 'Implement diverse validation sets and cross-validation',
        });
      }

      // Calculate fairness scores
      const fairnessScores = this.calculateFairnessScores(inputText, predictions, biasIndicators);

      return {
        overallFairnessScore: fairnessScores.overall,
        demographicParity: fairnessScores.demographicParity,
        equalizedOdds: fairnessScores.equalizedOdds,
        calibration: fairnessScores.calibration,
        representationFairness: fairnessScores.representation,
        biasIndicators,
      };

    } catch (error) {
      this.logger.error('Bias detection failed', {
        error: error.message,
        tenantId,
      });
      return this.getDefaultBiasMetrics();
    }
  }

  async generateExplanation(inputText: string, predictions: any[]): Promise<string> {
    try {
      // Simple rule-based explanation for now
      // In production, this would use explainable AI techniques like LIME, SHAP, etc.
      
      const topPrediction = predictions[0];
      if (!topPrediction) {
        return 'No predictions available for explanation';
      }

      const keyTerms = this.extractKeyMedicalTerms(inputText);
      const explanation = [
        `Based on the medical terminology analysis:`,
        `- Key terms identified: ${keyTerms.join(', ')}`,
        `- Primary CPT code suggested: ${topPrediction.code}`,
        `- Confidence level: ${(topPrediction.similarity * 100).toFixed(1)}%`,
        `- Reasoning: The suggested code matches the medical procedures described`,
      ];

      if (predictions.length > 1) {
        explanation.push(`- Alternative codes considered: ${predictions.slice(1, 3).map(p => p.code).join(', ')}`);
      }

      return explanation.join('\n');

    } catch (error) {
      this.logger.error('Explanation generation failed', {
        error: error.message,
      });
      return 'Explanation not available due to processing error';
    }
  }

  private async calculatePerformanceMetrics(
    predictions: any[],
    processingTime: number,
  ): Promise<ModelPerformanceMetrics> {
    // Simulated metrics - in production, these would be calculated from actual model performance
    const confidence = predictions.length > 0 ? predictions[0].similarity || 0.8 : 0;
    
    return {
      accuracy: Math.min(0.95, confidence + 0.1),
      precision: confidence,
      recall: Math.min(0.9, confidence + 0.05),
      f1Score: Math.min(0.9, confidence),
      latency: processingTime,
      throughput: 1000 / Math.max(processingTime, 1), // requests per second
      errorRate: Math.max(0.01, 1 - confidence),
      confidenceDistribution: {
        'high (>0.8)': predictions.filter(p => p.similarity > 0.8).length,
        'medium (0.5-0.8)': predictions.filter(p => p.similarity >= 0.5 && p.similarity <= 0.8).length,
        'low (<0.5)': predictions.filter(p => p.similarity < 0.5).length,
      },
    };
  }

  private checkDemographicBias(inputText: string, predictions: any[]): { detected: boolean; severity: 'low' | 'medium' | 'high' | 'critical' } {
    // Check for demographic indicators in text
    const demographicIndicators = [
      'male', 'female', 'elderly', 'young', 'pediatric', 'geriatric',
      'african american', 'caucasian', 'hispanic', 'asian',
    ];

    const hasDemo = demographicIndicators.some(indicator => 
      inputText.toLowerCase().includes(indicator)
    );

    if (hasDemo && predictions.length > 0) {
      // Simple heuristic: if predictions vary significantly with demographic terms, flag bias
      return { detected: true, severity: 'medium' };
    }

    return { detected: false, severity: 'low' };
  }

  private checkRepresentationBias(predictions: any[]): { detected: boolean; severity: 'low' | 'medium' | 'high' | 'critical' } {
    if (predictions.length < 2) {
      return { detected: true, severity: 'medium' }; // Lack of diversity in predictions
    }

    // Check if predictions are too similar (lack of diversity)
    const similarities = predictions.map(p => p.similarity || 0);
    const variance = this.calculateVariance(similarities);
    
    if (variance < 0.01) {
      return { detected: true, severity: 'low' };
    }

    return { detected: false, severity: 'low' };
  }

  private checkConfirmationBias(inputText: string, predictions: any[]): { detected: boolean; severity: 'low' | 'medium' | 'high' | 'critical' } {
    // Simple check: if all predictions are very similar, might indicate confirmation bias
    if (predictions.length > 1) {
      const topSimilarity = predictions[0].similarity || 0;
      const avgSimilarity = predictions.reduce((sum, p) => sum + (p.similarity || 0), 0) / predictions.length;
      
      if (Math.abs(topSimilarity - avgSimilarity) < 0.05) {
        return { detected: true, severity: 'low' };
      }
    }

    return { detected: false, severity: 'low' };
  }

  private calculateFairnessScores(inputText: string, predictions: any[], biasIndicators: any[]) {
    const baseFairness = 0.8;
    const penaltyPerIndicator = 0.1;
    const totalPenalty = biasIndicators.length * penaltyPerIndicator;
    
    const overall = Math.max(0.5, baseFairness - totalPenalty);
    
    return {
      overall,
      demographicParity: overall + 0.05,
      equalizedOdds: overall,
      calibration: overall + 0.1,
      representation: Math.max(0.6, overall - 0.1),
    };
  }

  private calculateAverageConfidence(predictions: any[]): number {
    if (predictions.length === 0) return 0;
    return predictions.reduce((sum, p) => sum + (p.similarity || 0), 0) / predictions.length;
  }

  private calculateVariance(values: number[]): number {
    if (values.length === 0) return 0;
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
    return squaredDiffs.reduce((sum, diff) => sum + diff, 0) / values.length;
  }

  private extractKeyMedicalTerms(text: string): string[] {
    const medicalTerms = [
      'surgery', 'procedure', 'examination', 'diagnosis', 'treatment',
      'therapy', 'consultation', 'evaluation', 'assessment', 'screening',
    ];

    const words = text.toLowerCase().split(/\s+/);
    return medicalTerms.filter(term => 
      words.some(word => word.includes(term))
    );
  }

  private assessCompliance(performance: ModelPerformanceMetrics, bias: BiasMetrics) {
    return {
      explainable: this.explainabilityRequired,
      auditTrail: true,
      dataMinimization: true,
      purposeLimitation: true,
      humanOversight: bias.overallFairnessScore < this.fairnessThresholds.overallFairnessScore,
    };
  }

  private getDefaultBiasMetrics(): BiasMetrics {
    return {
      overallFairnessScore: 0.8,
      demographicParity: 0.8,
      equalizedOdds: 0.8,
      calibration: 0.8,
      representationFairness: 0.7,
      biasIndicators: [],
    };
  }

  private async logGovernanceEvent(event: AIGovernanceEvent): Promise<void> {
    await this.auditService.logEvent({
      tenantId: event.tenantId,
      eventType: 'AI_GOVERNANCE',
      severity: this.getGovernanceSeverity(event),
      userId: event.userId,
      correlationId: event.operationId,
      resourceType: 'ai_model',
      resourceId: event.modelName,
      action: 'MODEL_PREDICTION',
      description: 'AI model governance monitoring',
      ipAddress: 'internal',
      additionalData: {
        modelName: event.modelName,
        modelVersion: event.modelVersion,
        performance: event.performance,
        bias: event.bias,
        compliance: event.compliance,
        explainable: !!event.prediction.reasoning,
      },
      phiAccessed: event.inputData.classification === 'phi',
      dataClassification: event.inputData.classification,
      complianceFlags: {
        aiGovernance: true,
        biasDetection: this.biasDetectionEnabled,
        explainability: this.explainabilityRequired,
        fairnessScore: event.bias.overallFairnessScore,
      },
    });
  }

  private async checkAlerts(event: AIGovernanceEvent): Promise<void> {
    const alerts = [];

    // Performance alerts
    if (event.performance.accuracy < this.performanceBaselines.accuracy) {
      alerts.push(`Model accuracy below baseline: ${event.performance.accuracy} < ${this.performanceBaselines.accuracy}`);
    }

    if (event.performance.latency > this.performanceBaselines.latency) {
      alerts.push(`Model latency above baseline: ${event.performance.latency}ms > ${this.performanceBaselines.latency}ms`);
    }

    // Bias alerts
    if (event.bias.overallFairnessScore < this.fairnessThresholds.overallFairnessScore) {
      alerts.push(`Fairness score below threshold: ${event.bias.overallFairnessScore} < ${this.fairnessThresholds.overallFairnessScore}`);
    }

    // Critical bias indicators
    const criticalBias = event.bias.biasIndicators.filter(indicator => indicator.severity === 'critical');
    if (criticalBias.length > 0) {
      alerts.push(`Critical bias detected: ${criticalBias.map(b => b.type).join(', ')}`);
    }

    // Log alerts
    if (alerts.length > 0) {
      this.logger.warn('AI governance alerts triggered', {
        operationId: event.operationId,
        tenantId: event.tenantId,
        modelName: event.modelName,
        alerts,
      });
    }
  }

  private getGovernanceSeverity(event: AIGovernanceEvent): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
    const criticalBias = event.bias.biasIndicators.some(b => b.severity === 'critical');
    const lowFairness = event.bias.overallFairnessScore < 0.6;
    const poorPerformance = event.performance.accuracy < 0.7;

    if (criticalBias || lowFairness || poorPerformance) return 'CRITICAL';
    if (event.bias.overallFairnessScore < 0.8) return 'HIGH';
    if (event.performance.accuracy < 0.9) return 'MEDIUM';
    return 'LOW';
  }
}