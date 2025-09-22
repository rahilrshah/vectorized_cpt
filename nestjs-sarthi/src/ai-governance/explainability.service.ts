import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

export interface ExplanationResult {
  confidence: number;
  reasoning: string;
  keyFactors: {
    factor: string;
    importance: number;
    impact: 'positive' | 'negative' | 'neutral';
    description: string;
  }[];
  alternatives: {
    option: string;
    confidence: number;
    reasoning: string;
  }[];
  uncertainties: {
    source: string;
    level: 'low' | 'medium' | 'high';
    description: string;
  }[];
  recommendations: string[];
}

@Injectable()
export class ExplainabilityService {
  private readonly logger = new Logger(ExplainabilityService.name);

  constructor(private readonly configService: ConfigService) {}

  async explainCptPrediction(
    inputText: string,
    predictions: any[],
    tenantId: string,
  ): Promise<ExplanationResult> {
    try {
      if (!predictions || predictions.length === 0) {
        return this.createEmptyExplanation();
      }

      const topPrediction = predictions[0];
      const keyFactors = this.identifyKeyFactors(inputText, topPrediction);
      const alternatives = this.generateAlternatives(predictions.slice(1, 4));
      const uncertainties = this.identifyUncertainties(inputText, predictions);
      const recommendations = this.generateRecommendations(inputText, predictions);

      const explanation: ExplanationResult = {
        confidence: topPrediction.similarity || 0,
        reasoning: this.generateReasoning(inputText, topPrediction, keyFactors),
        keyFactors,
        alternatives,
        uncertainties,
        recommendations,
      };

      this.logger.log('CPT prediction explained', {
        tenantId,
        inputLength: inputText.length,
        predictionCount: predictions.length,
        confidence: explanation.confidence,
        keyFactorCount: keyFactors.length,
      });

      return explanation;

    } catch (error) {
      this.logger.error('Explainability analysis failed', {
        error: error.message,
        tenantId,
        inputLength: inputText?.length,
      });

      return this.createErrorExplanation(error.message);
    }
  }

  async explainSearchResults(
    query: string,
    results: any[],
    searchContext: {
      tenantId: string;
      searchType: string;
      parameters?: Record<string, any>;
    },
  ): Promise<ExplanationResult> {
    try {
      const keyFactors = this.analyzeSearchFactors(query, results);
      const alternatives = this.generateSearchAlternatives(query, results);
      const uncertainties = this.identifySearchUncertainties(query, results);
      const recommendations = this.generateSearchRecommendations(query, results);

      const explanation: ExplanationResult = {
        confidence: this.calculateSearchConfidence(results),
        reasoning: this.generateSearchReasoning(query, results, searchContext),
        keyFactors,
        alternatives,
        uncertainties,
        recommendations,
      };

      return explanation;

    } catch (error) {
      this.logger.error('Search explainability failed', {
        error: error.message,
        tenantId: searchContext.tenantId,
        query: query?.substring(0, 100),
      });

      return this.createErrorExplanation(error.message);
    }
  }

  private identifyKeyFactors(inputText: string, prediction: any): ExplanationResult['keyFactors'] {
    const factors = [];
    const text = inputText.toLowerCase();
    const cptDescription = prediction.description?.toLowerCase() || '';

    // Medical terminology matching
    const medicalTerms = this.extractMedicalTerms(text);
    if (medicalTerms.length > 0) {
      factors.push({
        factor: 'Medical Terminology',
        importance: 0.8,
        impact: 'positive' as const,
        description: `Identified medical terms: ${medicalTerms.join(', ')}`,
      });
    }

    // Procedure type matching
    const procedureTypes = this.identifyProcedureTypes(text);
    if (procedureTypes.length > 0) {
      factors.push({
        factor: 'Procedure Type',
        importance: 0.9,
        impact: 'positive' as const,
        description: `Procedure types detected: ${procedureTypes.join(', ')}`,
      });
    }

    // Body system/anatomy matching
    const anatomy = this.identifyAnatomicalReferences(text);
    if (anatomy.length > 0) {
      factors.push({
        factor: 'Anatomical References',
        importance: 0.7,
        impact: 'positive' as const,
        description: `Body systems/anatomy: ${anatomy.join(', ')}`,
      });
    }

    // Code category alignment
    const category = prediction.category || 'Unknown';
    factors.push({
      factor: 'CPT Code Category',
      importance: 0.6,
      impact: 'neutral' as const,
      description: `Code falls under category: ${category}`,
    });

    // Semantic similarity
    factors.push({
      factor: 'Semantic Similarity',
      importance: prediction.similarity || 0.5,
      impact: prediction.similarity > 0.8 ? 'positive' as const : 'neutral' as const,
      description: `Text-to-code semantic match: ${((prediction.similarity || 0) * 100).toFixed(1)}%`,
    });

    return factors.sort((a, b) => b.importance - a.importance);
  }

  private generateAlternatives(predictions: any[]): ExplanationResult['alternatives'] {
    return predictions.slice(0, 3).map(pred => ({
      option: `${pred.code} - ${pred.description?.substring(0, 80)}...`,
      confidence: pred.similarity || 0,
      reasoning: `Alternative with ${((pred.similarity || 0) * 100).toFixed(1)}% similarity`,
    }));
  }

  private identifyUncertainties(inputText: string, predictions: any[]): ExplanationResult['uncertainties'] {
    const uncertainties = [];

    // Low confidence
    if (predictions[0]?.similarity < 0.7) {
      uncertainties.push({
        source: 'Model Confidence',
        level: 'high' as const,
        description: 'Model confidence is below optimal threshold',
      });
    }

    // Ambiguous terminology
    const ambiguousTerms = this.findAmbiguousTerms(inputText);
    if (ambiguousTerms.length > 0) {
      uncertainties.push({
        source: 'Terminology Ambiguity',
        level: 'medium' as const,
        description: `Ambiguous terms found: ${ambiguousTerms.join(', ')}`,
      });
    }

    // Missing context
    if (inputText.length < 50) {
      uncertainties.push({
        source: 'Limited Context',
        level: 'medium' as const,
        description: 'Input text may be too brief for optimal code selection',
      });
    }

    // Close alternatives
    if (predictions.length > 1 && predictions[1].similarity > 0.8) {
      uncertainties.push({
        source: 'Similar Alternatives',
        level: 'low' as const,
        description: 'Multiple codes have high similarity scores',
      });
    }

    return uncertainties;
  }

  private generateRecommendations(inputText: string, predictions: any[]): string[] {
    const recommendations = [];

    // Low confidence recommendations
    if (predictions[0]?.similarity < 0.7) {
      recommendations.push('Consider providing more detailed medical information');
      recommendations.push('Verify the suggested code with clinical documentation');
    }

    // Multiple similar codes
    if (predictions.length > 1 && predictions[1].similarity > 0.8) {
      recommendations.push('Review alternative codes for best fit');
      recommendations.push('Consider the specific clinical context when choosing');
    }

    // General best practices
    recommendations.push('Cross-reference with official CPT code guidelines');
    recommendations.push('Ensure code matches the documented procedure exactly');

    // Input quality recommendations
    if (inputText.length < 100) {
      recommendations.push('More detailed procedure descriptions may improve accuracy');
    }

    return recommendations;
  }

  private generateReasoning(
    inputText: string,
    prediction: any,
    keyFactors: ExplanationResult['keyFactors'],
  ): string {
    const topFactors = keyFactors.slice(0, 3);
    const confidence = prediction.similarity || 0;

    let reasoning = `The model selected CPT code ${prediction.code} based on the following analysis:\n\n`;

    reasoning += `Primary factors:\n`;
    topFactors.forEach((factor, index) => {
      reasoning += `${index + 1}. ${factor.factor}: ${factor.description} (${(factor.importance * 100).toFixed(0)}% importance)\n`;
    });

    reasoning += `\nOverall confidence: ${(confidence * 100).toFixed(1)}%\n`;

    if (confidence > 0.8) {
      reasoning += `This is a high-confidence match indicating strong alignment between the input and code description.`;
    } else if (confidence > 0.6) {
      reasoning += `This is a moderate-confidence match that should be verified against clinical documentation.`;
    } else {
      reasoning += `This is a low-confidence match that requires careful review and validation.`;
    }

    return reasoning;
  }

  private analyzeSearchFactors(query: string, results: any[]): ExplanationResult['keyFactors'] {
    const factors = [];

    // Query complexity
    const wordCount = query.split(/\s+/).length;
    factors.push({
      factor: 'Query Complexity',
      importance: Math.min(wordCount / 10, 1),
      impact: wordCount > 5 ? 'positive' as const : 'neutral' as const,
      description: `Query contains ${wordCount} words providing ${wordCount > 5 ? 'good' : 'limited'} context`,
    });

    // Result diversity
    const uniqueCategories = new Set(results.map(r => r.category)).size;
    factors.push({
      factor: 'Result Diversity',
      importance: 0.7,
      impact: uniqueCategories > 3 ? 'positive' as const : 'neutral' as const,
      description: `Results span ${uniqueCategories} different CPT categories`,
    });

    return factors;
  }

  private generateSearchAlternatives(query: string, results: any[]): ExplanationResult['alternatives'] {
    // Suggest query refinements
    const alternatives = [];

    if (query.length < 20) {
      alternatives.push({
        option: 'Expand query with more details',
        confidence: 0.8,
        reasoning: 'More specific medical terminology could improve results',
      });
    }

    if (results.length > 20) {
      alternatives.push({
        option: 'Add procedure modifiers',
        confidence: 0.7,
        reasoning: 'Narrowing search scope could provide more relevant results',
      });
    }

    return alternatives;
  }

  private identifySearchUncertainties(query: string, results: any[]): ExplanationResult['uncertainties'] {
    const uncertainties = [];

    if (results.length === 0) {
      uncertainties.push({
        source: 'No Results',
        level: 'high' as const,
        description: 'Search returned no matching CPT codes',
      });
    }

    if (results.length > 50) {
      uncertainties.push({
        source: 'Too Many Results',
        level: 'medium' as const,
        description: 'Search may be too broad, consider adding specificity',
      });
    }

    return uncertainties;
  }

  private generateSearchRecommendations(query: string, results: any[]): string[] {
    const recommendations = [];

    if (results.length === 0) {
      recommendations.push('Try broader medical terminology');
      recommendations.push('Check spelling of medical terms');
      recommendations.push('Consider synonyms for procedures');
    } else if (results.length > 50) {
      recommendations.push('Add procedure modifiers or anatomical details');
      recommendations.push('Specify the type of service (evaluation, procedure, etc.)');
    }

    recommendations.push('Review top results for clinical relevance');
    return recommendations;
  }

  private calculateSearchConfidence(results: any[]): number {
    if (results.length === 0) return 0;
    if (results.length === 1) return results[0].similarity || 0.5;
    
    const avgSimilarity = results.reduce((sum, r) => sum + (r.similarity || 0), 0) / results.length;
    return Math.min(avgSimilarity + 0.1, 1); // Boost for having multiple results
  }

  private generateSearchReasoning(
    query: string,
    results: any[],
    context: { searchType: string; parameters?: Record<string, any> },
  ): string {
    let reasoning = `Search analysis for query: "${query}"\n\n`;
    
    reasoning += `Search type: ${context.searchType}\n`;
    reasoning += `Results found: ${results.length}\n\n`;

    if (results.length > 0) {
      reasoning += `Top result: ${results[0].code} (${((results[0].similarity || 0) * 100).toFixed(1)}% match)\n`;
      reasoning += `The search algorithm identified relevant CPT codes based on semantic similarity and medical terminology matching.`;
    } else {
      reasoning += `No matching codes found. This may indicate the need for different search terms or that the described procedure may not have a direct CPT code match.`;
    }

    return reasoning;
  }

  private extractMedicalTerms(text: string): string[] {
    const medicalTerms = [
      'surgery', 'procedure', 'examination', 'consultation', 'evaluation',
      'therapy', 'treatment', 'injection', 'biopsy', 'removal', 'repair',
      'replacement', 'reconstruction', 'diagnostic', 'screening', 'monitoring',
    ];

    return medicalTerms.filter(term => text.includes(term));
  }

  private identifyProcedureTypes(text: string): string[] {
    const procedureTypes = [
      'surgical', 'diagnostic', 'therapeutic', 'preventive', 'emergency',
      'outpatient', 'inpatient', 'minimally invasive', 'open procedure',
    ];

    return procedureTypes.filter(type => text.includes(type.replace(' ', '')));
  }

  private identifyAnatomicalReferences(text: string): string[] {
    const anatomy = [
      'heart', 'lung', 'liver', 'kidney', 'brain', 'spine', 'knee', 'hip',
      'shoulder', 'hand', 'foot', 'abdomen', 'chest', 'head', 'neck',
      'cardiovascular', 'respiratory', 'digestive', 'neurological',
    ];

    return anatomy.filter(part => text.includes(part));
  }

  private findAmbiguousTerms(text: string): string[] {
    const ambiguousTerms = [
      'procedure', 'treatment', 'examination', 'evaluation', 'assessment',
      'intervention', 'manipulation', 'therapy', 'care', 'service',
    ];

    return ambiguousTerms.filter(term => text.includes(term));
  }

  private createEmptyExplanation(): ExplanationResult {
    return {
      confidence: 0,
      reasoning: 'No predictions available to explain',
      keyFactors: [],
      alternatives: [],
      uncertainties: [{
        source: 'No Data',
        level: 'high',
        description: 'No predictions were generated to analyze',
      }],
      recommendations: ['Ensure input data is provided', 'Check system connectivity'],
    };
  }

  private createErrorExplanation(errorMessage: string): ExplanationResult {
    return {
      confidence: 0,
      reasoning: `Analysis failed due to error: ${errorMessage}`,
      keyFactors: [],
      alternatives: [],
      uncertainties: [{
        source: 'System Error',
        level: 'high',
        description: 'Explainability analysis encountered an error',
      }],
      recommendations: ['Retry the operation', 'Contact support if issue persists'],
    };
  }
}