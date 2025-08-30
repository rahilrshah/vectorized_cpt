/**
 * Billing Class Architecture for Firebase Functions
 * TypeScript implementation that mirrors the Python structure
 */

import { BillingConfig } from './config';
import { CPTSearchService } from './services/cpt-search';
import { AIProcessorService } from './services/ai-processor';
import { FirestoreService } from './services/firestore-service';
import { MedicalCodingService } from './services/medical-coding';

export interface ProcessingResponse {
  step1_extractedText: string;
  step2_extractedProcedures: string;
  step3_embeddingVector: number[];
  step4_cptResults: any[];
  results: any[];
  success: boolean;
  processing_time_ms?: number;
  error?: string;
}

export class Billing {
  private config: BillingConfig;
  private cptSearch: CPTSearchService;
  private aiProcessor: AIProcessorService;
  private firestoreService: FirestoreService;
  private medicalCoding: MedicalCodingService;

  constructor() {
    console.log("🏥 Initializing Medical Billing System (TypeScript)...");
    
    // Initialize configuration
    this.config = new BillingConfig();
    
    // Initialize services
    this.cptSearch = new CPTSearchService(this);
    this.aiProcessor = new AIProcessorService(this);
    this.firestoreService = new FirestoreService(this);
    this.medicalCoding = new MedicalCodingService(this);
    
    console.log("✅ Billing System Ready (TypeScript)");
  }

  public getConfig(): BillingConfig {
    return this.config;
  }

  public getCPTSearch(): CPTSearchService {
    return this.cptSearch;
  }

  public getAIProcessor(): AIProcessorService {
    return this.aiProcessor;
  }

  public getFirestoreService(): FirestoreService {
    return this.firestoreService;
  }

  /**
   * Complete medical note processing pipeline
   * Replicates exact Firebase function behavior using new architecture
   */
  public async processMedicalNote(text: string, maxResults: number = 20): Promise<ProcessingResponse> {
    const startTime = Date.now();
    
    // Initialize response structure (same as original Firebase function)
    const pipelineResponse: ProcessingResponse = {
      step1_extractedText: text.substring(0, 1000) + (text.length > 1000 ? "..." : ""),
      step2_extractedProcedures: "",
      step3_embeddingVector: [],
      step4_cptResults: [],
      results: [],
      success: true
    };

    try {
      // Step 2: Extract procedures with Gemini AI
      console.log("🤖 Step 2: Extracting procedures with AI...");
      const procedures = await this.aiProcessor.extractProceduresWithGemini(text);
      pipelineResponse.step2_extractedProcedures = procedures;

      // Step 3: Generate embedding vector
      console.log("🧮 Step 3: Generating embedding vector...");
      const embedding = await this.aiProcessor.generateEmbeddingVector(procedures);
      pipelineResponse.step3_embeddingVector = embedding;

      // Step 4: Search CPT codes
      console.log("🔍 Step 4: Searching CPT codes...");
      const primaryResults = await this.cptSearch.searchWithVector(embedding, procedures);
      
      // Apply max_results limit to primary results
      const limitedResults = primaryResults.slice(0, maxResults);
      
      // Step 5: Comprehensive multi-code detection (NEW ENHANCEMENT)
      console.log("🏥 Step 5: Multi-code detection...");
      const comprehensiveCodes = this.medicalCoding.detectComprehensiveCodes(
        limitedResults, procedures, text
      );
      
      pipelineResponse.step4_cptResults = limitedResults;  // Maintain backward compatibility
      pipelineResponse.results = limitedResults;           // Legacy format
      (pipelineResponse as any).comprehensive_codes = comprehensiveCodes;  // NEW: Enhanced results

      // Add processing time
      const processingTime = Date.now() - startTime;
      pipelineResponse.processing_time_ms = processingTime;

      console.log(`✅ Processing complete: ${limitedResults.length} results in ${processingTime}ms`);
      return pipelineResponse;

    } catch (error: any) {
      console.error(`❌ Processing failed: ${error.message}`);
      pipelineResponse.success = false;
      pipelineResponse.error = error.message;
      return pipelineResponse;
    }
  }

  /**
   * Direct CPT code search (skip Gemini processing)
   */
  public async searchCPTCodes(query: string, maxResults: number = 20): Promise<any[]> {
    try {
      // Generate embedding directly from query
      const embedding = await this.aiProcessor.generateEmbeddingVector(query);
      
      // Search with vector
      const results = await this.cptSearch.searchWithVector(embedding, query);
      
      return results.slice(0, maxResults);
      
    } catch (error: any) {
      console.error(`❌ Search failed: ${error.message}`);
      return [];
    }
  }

  /**
   * System health check
   */
  public async getSystemHealth(): Promise<any> {
    const healthStatus = {
      status: "healthy",
      timestamp: Date.now(),
      services: {} as any,
      version: "1.0.0"
    };

    try {
      // Check AI Processor
      healthStatus.services.ai_processor = await this.checkAIProcessorHealth();
      
      // Check Firestore
      healthStatus.services.firestore = await this.checkFirestoreHealth();
      
      // Check Vertex AI
      healthStatus.services.vertex_ai = await this.checkVertexAIHealth();

      // Overall system status
      const failedServices = Object.keys(healthStatus.services).filter(
        key => healthStatus.services[key] !== "operational"
      );
      
      if (failedServices.length > 0) {
        healthStatus.status = "degraded";
        (healthStatus as any).failed_services = failedServices;
      }

    } catch (error: any) {
      healthStatus.status = "unhealthy";
      (healthStatus as any).error = error.message;
    }

    return healthStatus;
  }

  private async checkAIProcessorHealth(): Promise<string> {
    try {
      const result = await this.aiProcessor.extractProceduresWithGemini("Patient underwent routine checkup.");
      return result ? "operational" : "degraded";
    } catch {
      return "failed";
    }
  }

  private async checkFirestoreHealth(): Promise<string> {
    try {
      const stats = await this.firestoreService.getCollectionStats();
      return stats.document_count > 0 ? "operational" : "degraded";
    } catch {
      return "failed";
    }
  }

  private async checkVertexAIHealth(): Promise<string> {
    try {
      const testEmbedding = await this.aiProcessor.generateEmbeddingVector("test");
      return testEmbedding.length === 768 ? "operational" : "degraded";
    } catch {
      return "failed";
    }
  }
}