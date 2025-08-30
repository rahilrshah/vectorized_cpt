/**
 * Medical Coding Service - Multi-code detection and billing intelligence
 * Handles anesthesia codes, modifiers, and comprehensive medical billing
 */

import { Billing } from '../index';

interface CodeResult {
  code: string;
  description: string;
  type: string;
  similarity: number;
  reason: string;
}

interface ModifierResult {
  code: string;
  description: string;
  type: string;
  reason: string;
}

interface ComprehensiveResult {
  primary_codes: any[];
  anesthesia_codes: CodeResult[];
  modifiers: ModifierResult[];
  related_codes: CodeResult[];
  coding_confidence: string;
  medical_specialty: string;
  billing_summary: any;
}

export class MedicalCodingService {
  private billing: Billing;
  
  // CPT to Anesthesia Code Mapping (common procedures)
  private cptAnesthesiaMap: { [key: string]: string } = {
    // Knee procedures
    '27447': '00402',  // Total knee arthroplasty -> Anesthesia for procedures on knee
    '27446': '00402',  // Partial knee replacement
    '27440': '00402',  // Total knee arthroplasty with patella
    '29881': '00400',  // Arthroscopy, knee -> Anesthesia for procedures on knee
    '29882': '00400',  // Arthroscopy with meniscectomy
    
    // Hip procedures  
    '27130': '01200',  // Total hip arthroplasty -> Anesthesia for procedures on hip
    '27132': '01200',  // Conversion to total hip arthroplasty
    '27134': '01200',  // Revision of total hip arthroplasty
    
    // Shoulder procedures
    '23472': '01630',  // Total shoulder arthroplasty -> Anesthesia for shoulder
    '29827': '01630',  // Arthroscopy, shoulder
    
    // Spine procedures
    '22558': '00600',  // Arthrodesis, anterior interbody -> Anesthesia for spine
    '22612': '00600',  // Arthrodesis, posterior
    
    // Hand/Wrist procedures
    '25332': '01810',  // Arthroplasty, wrist -> Anesthesia for forearm/wrist/hand
  };
  
  // Medical specialties for context
  private medicalSpecialties: { [key: string]: string[] } = {
    'orthopedic': ['knee', 'hip', 'shoulder', 'spine', 'joint', 'bone'],
    'cardiovascular': ['heart', 'cardiac', 'vessel', 'artery', 'vein'],
    'neurological': ['brain', 'nerve', 'spinal', 'neural'],
    'gastroenterology': ['stomach', 'intestine', 'colon', 'liver'],
    'gynecology': ['uterus', 'ovary', 'cervix', 'fallopian']
  };

  constructor(billing: Billing) {
    this.billing = billing;
    
    console.log(`🏥 Medical Coding Service initialized for project: ${this.billing.getConfig().PROJECT_ID}`);
    console.log(`   Multi-code detection enabled`);
  }

  /**
   * Comprehensive multi-code detection for complete medical billing
   */
  public detectComprehensiveCodes(
    primaryCptCodes: any[], 
    aiExtractedText: string, 
    originalMedicalNote: string
  ): ComprehensiveResult {
    try {
      const result: ComprehensiveResult = {
        primary_codes: primaryCptCodes,
        anesthesia_codes: [],
        modifiers: [],
        related_codes: [],
        coding_confidence: this.calculateConfidence(primaryCptCodes),
        medical_specialty: this.detectSpecialty(aiExtractedText),
        billing_summary: {}
      };
      
      // Process each primary CPT code
      for (const cptResult of primaryCptCodes) {
        const cptCode = cptResult.cpt_code || '';
        
        // 1. Detect anesthesia codes
        const anesthesiaCodes = this.detectAnesthesiaCodes(cptCode, aiExtractedText);
        result.anesthesia_codes.push(...anesthesiaCodes);
        
        // 2. Detect anatomical modifiers
        const modifiers = this.detectModifiers(aiExtractedText, originalMedicalNote);
        result.modifiers.push(...modifiers);
        
        // 3. Detect related/secondary codes
        const relatedCodes = this.detectRelatedCodes(cptCode, aiExtractedText);
        result.related_codes.push(...relatedCodes);
      }
      
      // Remove duplicates
      result.anesthesia_codes = this.removeDuplicateCodes(result.anesthesia_codes);
      result.modifiers = this.removeDuplicateModifiers(result.modifiers);
      result.related_codes = this.removeDuplicateCodes(result.related_codes);
      
      // Generate billing summary
      result.billing_summary = this.generateBillingSummary(result);
      
      console.log(`🏥 Multi-code detection completed:`);
      console.log(`   Primary codes: ${result.primary_codes.length}`);
      console.log(`   Anesthesia codes: ${result.anesthesia_codes.length}`);
      console.log(`   Modifiers: ${result.modifiers.length}`);
      console.log(`   Related codes: ${result.related_codes.length}`);
      
      return result;
      
    } catch (error: any) {
      console.error(`❌ Error in comprehensive code detection: ${error.message}`);
      return {
        primary_codes: primaryCptCodes,
        anesthesia_codes: [],
        modifiers: [],
        related_codes: [],
        coding_confidence: 'low',
        medical_specialty: 'general',
        billing_summary: { error: error.message }
      };
    }
  }

  /**
   * Detect anesthesia codes based on primary CPT and procedure context
   */
  private detectAnesthesiaCodes(primaryCpt: string, medicalText: string): CodeResult[] {
    const anesthesiaCodes: CodeResult[] = [];
    
    // Direct CPT to anesthesia mapping
    if (primaryCpt in this.cptAnesthesiaMap) {
      const anesthesiaCode = this.cptAnesthesiaMap[primaryCpt];
      anesthesiaCodes.push({
        code: anesthesiaCode,
        description: this.getAnesthesiaDescription(anesthesiaCode),
        type: 'anesthesia',
        similarity: 0.98,  // High confidence for mapped codes
        reason: `Standard anesthesia for CPT ${primaryCpt}`
      });
    }
    
    // Context-based anesthesia detection
    const lowerText = medicalText.toLowerCase();
    
    if (lowerText.includes('general anesthesia') || lowerText.includes('under general')) {
      if (anesthesiaCodes.length === 0) {  // Only add if not already detected
        // Infer anesthesia based on procedure complexity
        if (['arthroplasty', 'replacement', 'major'].some(term => lowerText.includes(term))) {
          anesthesiaCodes.push({
            code: '00400',  // Default for major orthopedic
            description: 'Anesthesia for procedures on the knee',
            type: 'anesthesia',
            similarity: 0.85,
            reason: 'General anesthesia indicated for major procedure'
          });
        }
      }
    }
    
    return anesthesiaCodes;
  }

  /**
   * Detect anatomical and procedural modifiers
   */
  private detectModifiers(medicalText: string, originalNote: string): ModifierResult[] {
    const modifiers: ModifierResult[] = [];
    const combinedText = (medicalText + " " + originalNote).toLowerCase();
    
    // Anatomical laterality detection
    const hasRight = combinedText.includes('right');
    const hasLeft = combinedText.includes('left');
    const hasBilateral = combinedText.includes('bilateral');
    
    if (hasRight && !hasLeft && !hasBilateral) {
      modifiers.push({
        code: 'RT',
        description: 'Right side',
        type: 'anatomical',
        reason: 'Right laterality identified'
      });
    } else if (hasLeft && !hasRight && !hasBilateral) {
      modifiers.push({
        code: 'LT',
        description: 'Left side', 
        type: 'anatomical',
        reason: 'Left laterality identified'
      });
    } else if (hasBilateral || (hasRight && hasLeft)) {
      modifiers.push({
        code: '50',
        description: 'Bilateral procedure',
        type: 'anatomical',
        reason: 'Bilateral procedure identified'
      });
    }
    
    // Procedural modifiers
    if (combinedText.includes('multiple procedures') || combinedText.includes('additional procedure')) {
      modifiers.push({
        code: '51',
        description: 'Multiple procedures',
        type: 'procedural',
        reason: 'Multiple procedures indicated'
      });
    }
    
    if (combinedText.includes('reduced services') || combinedText.includes('partial procedure')) {
      modifiers.push({
        code: '52',
        description: 'Reduced services',
        type: 'procedural', 
        reason: 'Reduced services indicated'
      });
    }
    
    return modifiers;
  }

  /**
   * Detect related diagnostic or ancillary codes
   */
  private detectRelatedCodes(primaryCpt: string, medicalText: string): CodeResult[] {
    const relatedCodes: CodeResult[] = [];
    const lowerText = medicalText.toLowerCase();
    
    // Common diagnostic codes based on procedures
    const diagnosticMappings: { [key: string]: Array<{code: string, description: string, type: string}> } = {
      '27447': [  // Total knee arthroplasty
        { code: 'M17.9', description: 'Osteoarthritis of knee, unspecified', type: 'diagnosis' },
        { code: 'Z96.651', description: 'Presence of right artificial knee joint', type: 'status' }
      ],
      '27130': [  // Total hip arthroplasty
        { code: 'M16.9', description: 'Osteoarthritis of hip, unspecified', type: 'diagnosis' },
        { code: 'Z96.641', description: 'Presence of right artificial hip joint', type: 'status' }
      ]
    };
    
    if (primaryCpt in diagnosticMappings) {
      for (const related of diagnosticMappings[primaryCpt]) {
        // Adjust laterality for status codes
        if (lowerText.includes('right') && related.code.includes('Z96')) {
          relatedCodes.push({
            ...related,
            similarity: 0.95,
            reason: `Standard diagnosis for ${primaryCpt}`
          });
        } else if (lowerText.includes('left') && related.code.includes('Z96')) {
          // Adjust code for left side
          const leftCode = related.code.replace('641', '642').replace('651', '652');  // Right to left
          relatedCodes.push({
            code: leftCode,
            description: related.description.replace('right', 'left'),
            type: related.type,
            similarity: 0.95,
            reason: `Standard diagnosis for ${primaryCpt} - left side`
          });
        } else {
          relatedCodes.push({
            ...related,
            similarity: 0.90,
            reason: `Standard diagnosis for ${primaryCpt}`
          });
        }
      }
    }
    
    return relatedCodes;
  }

  /**
   * Detect medical specialty based on procedure context
   */
  private detectSpecialty(medicalText: string): string {
    const lowerText = medicalText.toLowerCase();
    
    for (const [specialty, keywords] of Object.entries(this.medicalSpecialties)) {
      if (keywords.some(keyword => lowerText.includes(keyword))) {
        return specialty;
      }
    }
    
    return 'general';
  }

  /**
   * Calculate overall coding confidence based on primary code similarities
   */
  private calculateConfidence(primaryCodes: any[]): string {
    if (primaryCodes.length === 0) {
      return 'low';
    }
    
    const avgSimilarity = primaryCodes.reduce((sum, code) => 
      sum + (code.similarity || 0), 0) / primaryCodes.length;
    
    if (avgSimilarity >= 0.9) {
      return 'high';
    } else if (avgSimilarity >= 0.7) {
      return 'medium';
    } else {
      return 'low';
    }
  }

  /**
   * Get description for anesthesia codes
   */
  private getAnesthesiaDescription(anesthesiaCode: string): string {
    const descriptions: { [key: string]: string } = {
      '00400': 'Anesthesia for procedures on the knee',
      '00402': 'Anesthesia for procedures on the knee; total knee arthroplasty',
      '01200': 'Anesthesia for procedures on hip joint',
      '01630': 'Anesthesia for procedures on shoulder and axilla',
      '00600': 'Anesthesia for procedures on cervical spine and cord',
      '01810': 'Anesthesia for procedures on forearm, wrist, and hand'
    };
    return descriptions[anesthesiaCode] || 'Anesthesia procedure';
  }

  /**
   * Remove duplicate codes from list
   */
  private removeDuplicateCodes(codes: CodeResult[]): CodeResult[] {
    const seenCodes = new Set<string>();
    const uniqueCodes: CodeResult[] = [];
    
    for (const codeDict of codes) {
      if (!seenCodes.has(codeDict.code)) {
        seenCodes.add(codeDict.code);
        uniqueCodes.push(codeDict);
      }
    }
    
    return uniqueCodes;
  }

  /**
   * Remove duplicate modifiers from list
   */
  private removeDuplicateModifiers(modifiers: ModifierResult[]): ModifierResult[] {
    const seenModifiers = new Set<string>();
    const uniqueModifiers: ModifierResult[] = [];
    
    for (const modifierDict of modifiers) {
      if (!seenModifiers.has(modifierDict.code)) {
        seenModifiers.add(modifierDict.code);
        uniqueModifiers.push(modifierDict);
      }
    }
    
    return uniqueModifiers;
  }

  /**
   * Generate comprehensive billing summary
   */
  private generateBillingSummary(result: ComprehensiveResult): any {
    return {
      total_codes: result.primary_codes.length + result.anesthesia_codes.length + result.related_codes.length,
      has_modifiers: result.modifiers.length > 0,
      has_anesthesia: result.anesthesia_codes.length > 0,
      complexity: result.primary_codes.length + result.related_codes.length > 2 ? 'complex' : 'simple',
      specialty: result.medical_specialty,
      billing_confidence: result.coding_confidence
    };
  }
}