import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { ConfigService } from '@nestjs/config';
import { CptCode } from '../database/entities/cpt-code.entity';
import { VectorEngineService } from '../vector-engine/vector-engine.service';
import { AuditService } from '../audit/audit.service';
import { DataLineageService } from '../data-governance/data-lineage.service';
import { DataClassificationService } from '../data-governance/data-classification.service';
import { AIGovernanceService } from '../ai-governance/ai-governance.service';
import { CptSearchResult } from './dto/cpt-search.dto';
import { v4 as uuidv4 } from 'uuid';

export interface SearchOptions {
  tenantId: string;
  maxResults?: number;
  similarityThreshold?: number;
  enableComprehensiveSearch?: boolean;
  categories?: string[];
}

export interface MedicalNoteProcessingResult {
  extractedText: string;
  extractedProcedures: string;
  embeddingDimensions: number;
  primaryResults: CptSearchResult[];
  comprehensiveResults?: CptSearchResult[];
  results: CptSearchResult[];
}

@Injectable()
export class CptSearchService {
  private readonly logger = new Logger(CptSearchService.name);

  constructor(
    @InjectRepository(CptCode)
    private readonly cptCodeRepository: Repository<CptCode>,
    private readonly vectorEngineService: VectorEngineService,
    private readonly auditService: AuditService,
    private readonly dataLineageService: DataLineageService,
    private readonly dataClassificationService: DataClassificationService,
    private readonly aiGovernanceService: AIGovernanceService,
    private readonly configService: ConfigService,
  ) {}

  async processMedicalNote(
    text: string,
    options: SearchOptions,
    userId?: string,
  ): Promise<MedicalNoteProcessingResult> {
    const startTime = Date.now();
    const operationId = uuidv4();

    try {
      // Step 1: Classify medical text for data governance
      const classification = await this.dataClassificationService.classifyMedicalText(
        text,
        options.tenantId,
      );

      this.logger.log('Medical text classified', {
        operationId,
        tenantId: options.tenantId,
        classification: classification.classification,
        sensitivity: classification.sensitivity,
        confidence: classification.confidence,
      });

      // Step 2: Extract text (already provided)
      const extractedText = text.substring(0, 1000) + (text.length > 1000 ? '...' : '');

      // Step 3: Extract procedures using AI (placeholder)
      const extractedProcedures = await this.extractProceduresWithAI(text);

      // Step 3: Generate embedding vector
      const embedding = await this.vectorEngineService.generateEmbedding(extractedProcedures);
      
      // Step 4: Search CPT codes
      const primaryResults = await this.searchWithVector(embedding, extractedProcedures, options);

      // Step 5: Comprehensive search (if enabled)
      let comprehensiveResults: CptSearchResult[] = [];
      if (options.enableComprehensiveSearch) {
        comprehensiveResults = await this.performComprehensiveSearch(text, primaryResults, options);
      }

      const finalResults = options.enableComprehensiveSearch && comprehensiveResults.length > 0
        ? comprehensiveResults
        : primaryResults;

      // AI governance monitoring
      const governanceEvent = await this.aiGovernanceService.monitorModelPerformance(
        operationId,
        options.tenantId,
        userId || 'system',
        'text-embedding-004',
        text,
        finalResults,
        Date.now() - startTime,
      );

      // Track data lineage for governance
      await this.dataLineageService.trackCptSearch(
        operationId,
        options.tenantId,
        userId || 'system',
        extractedProcedures,
        finalResults,
        Date.now() - startTime,
      );

      // Log audit event
      await this.auditService.logCptSearch(
        options.tenantId,
        userId || 'system',
        extractedProcedures,
        finalResults.length,
        Date.now() - startTime,
        '127.0.0.1', // TODO: Get actual IP from context
        operationId,
      );

      return {
        extractedText,
        extractedProcedures,
        embeddingDimensions: embedding.length,
        primaryResults,
        comprehensiveResults: options.enableComprehensiveSearch ? comprehensiveResults : undefined,
        results: finalResults,
      };
    } catch (error) {
      this.logger.error('Medical note processing failed', {
        error: error.message,
        tenantId: options.tenantId,
        textLength: text.length,
      });
      throw error;
    }
  }

  async directSearch(
    query: string,
    options: SearchOptions,
  ): Promise<CptSearchResult[]> {
    try {
      // Generate embedding for query
      const embedding = await this.vectorEngineService.generateEmbedding(query);
      
      // Search with vector
      return await this.searchWithVector(embedding, query, options);
    } catch (error) {
      this.logger.error('Direct search failed', {
        error: error.message,
        tenantId: options.tenantId,
        query,
      });
      throw error;
    }
  }

  private async extractProceduresWithAI(text: string): Promise<string> {
    // TODO: Implement actual Gemini AI integration
    // For now, return a simplified version of the text
    
    // Basic medical procedure extraction logic
    const medicalKeywords = [
      'surgery', 'procedure', 'operation', 'treatment', 'therapy',
      'examination', 'diagnostic', 'test', 'scan', 'biopsy',
      'arthroscopy', 'endoscopy', 'laparoscopy', 'catheterization',
    ];

    const sentences = text.toLowerCase().split(/[.!?]+/);
    const medicalSentences = sentences.filter(sentence =>
      medicalKeywords.some(keyword => sentence.includes(keyword))
    );

    return medicalSentences.join('. ').trim() || text.substring(0, 200);
  }

  private async searchWithVector(
    embedding: number[],
    query: string,
    options: SearchOptions,
  ): Promise<CptSearchResult[]> {
    try {
      // Get CPT codes for tenant
      const queryBuilder = this.cptCodeRepository
        .createQueryBuilder('cpt')
        .where('cpt.tenantId = :tenantId', { tenantId: options.tenantId })
        .andWhere('cpt.status = :status', { status: 'active' });

      // Apply category filter if provided
      if (options.categories && options.categories.length > 0) {
        queryBuilder.andWhere('cpt.category IN (:...categories)', { categories: options.categories });
      }

      const cptCodes = await queryBuilder.getMany();

      if (cptCodes.length === 0) {
        this.logger.warn('No CPT codes found for tenant', { tenantId: options.tenantId });
        return [];
      }

      // Calculate similarities
      const results: CptSearchResult[] = [];
      const similarityThreshold = options.similarityThreshold || 0.7;

      for (const cptCode of cptCodes) {
        if (!cptCode.vectorEmbedding || cptCode.vectorEmbedding.length === 0) {
          continue;
        }

        const similarity = this.vectorEngineService.calculateSimilarity(
          embedding,
          cptCode.vectorEmbedding,
        );

        if (similarity >= similarityThreshold) {
          const result: CptSearchResult = {
            cptCode: cptCode.cptCode,
            description: cptCode.description,
            category: cptCode.category || '',
            status: cptCode.status,
            similarity,
            distance: 1 - similarity,
            matchTerms: this.extractMatchTerms(query, cptCode.description),
            metadata: cptCode.metadata,
          };

          results.push(result);
        }
      }

      // Sort by similarity (highest first)
      results.sort((a, b) => b.similarity - a.similarity);

      // Limit results
      const maxResults = options.maxResults || 20;
      return results.slice(0, maxResults);
    } catch (error) {
      this.logger.error('Vector search failed', {
        error: error.message,
        tenantId: options.tenantId,
        embeddingLength: embedding.length,
      });
      throw error;
    }
  }

  private async performComprehensiveSearch(
    originalText: string,
    primaryResults: CptSearchResult[],
    options: SearchOptions,
  ): Promise<CptSearchResult[]> {
    // TODO: Implement comprehensive multi-code detection
    // This would include related procedures, modifiers, etc.
    
    // For now, return primary results with potential enhancements
    return primaryResults;
  }

  private extractMatchTerms(query: string, description: string): string[] {
    const queryTerms = query.toLowerCase().split(/\s+/).filter(term => term.length > 3);
    const descriptionLower = description.toLowerCase();
    
    return queryTerms.filter(term => descriptionLower.includes(term));
  }
}