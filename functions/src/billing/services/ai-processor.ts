/**
 * AI Processor Service
 * Handles all AI/ML operations (Gemini, embeddings)
 */

import { Billing } from '../index';
import { VertexAI } from '@google-cloud/vertexai';
import { GoogleAuth } from 'google-auth-library';

export class AIProcessorService {
  private billing: Billing;

  constructor(billing: Billing) {
    this.billing = billing;
    
    const config = this.billing.getConfig();
    console.log(`🤖 AI Processor Service initialized`);
    console.log(`   Embedding Model: ${config.EMBEDDING_MODEL}`);
    console.log(`   Generative Model: ${config.GENERATIVE_MODEL}`);
  }

  /**
   * Extract procedures using Gemini
   * Exact port from original Firebase function logic
   */
  public async extractProceduresWithGemini(medicalText: string): Promise<string> {
    try {
      const config = this.billing.getConfig();
      
      console.log("🤖 Initializing Vertex AI with project:", config.PROJECT_ID, "location:", config.LOCATION);
      
      // Import VertexAI dynamically to reduce cold start time
      const vertexAI = new VertexAI({
        project: config.PROJECT_ID, 
        location: config.LOCATION
      });

      console.log("🤖 Getting generative model:", config.GENERATIVE_MODEL);
      const generativeModel = vertexAI.getGenerativeModel({
        model: config.GENERATIVE_MODEL,
      });

      const prompt = this.createMedicalExtractionPrompt(medicalText);

      console.log("🤖 Calling Gemini model with prompt length:", prompt.length);
      const resp = await generativeModel.generateContent(prompt);
      console.log("🤖 Gemini response received:", JSON.stringify(resp.response, null, 2));

      const summary = resp.response.candidates?.[0]?.content?.parts?.[0]?.text;
      const cleanQuery = summary || "";

      if (cleanQuery === "") {
        console.error("❌ Empty summary from Gemini response");
        throw new Error("LLM failed to generate a summary.");
      }
      
      console.log("✅ LLM-extracted query:", cleanQuery);
      return cleanQuery;

    } catch (error: any) {
      console.error("❌ Detailed Gemini error:", error);
      console.error("Error type:", typeof error);
      console.error("Error message:", error.message);
      console.error("Error stack:", error.stack);
      throw new Error(`Failed to summarize text with the LLM: ${error.message}`);
    }
  }

  /**
   * Enhanced medical extraction prompt with structured analysis
   * Extracts medical context for multi-code detection and accurate billing
   */
  private createMedicalExtractionPrompt(medicalText: string): string {
    return `You are an expert medical coding specialist with deep knowledge of CPT codes, anesthesia codes, and billing modifiers. Analyze the following medical note and extract comprehensive medical coding information.

ANALYSIS REQUIREMENTS:
1. ANATOMICAL PRECISION: Identify exact anatomical locations, sides (right/left/bilateral)
2. PROCEDURE CLASSIFICATION: Categorize by complexity, approach, and specialty
3. BILLING COMPONENTS: Identify all billable elements including anesthesia needs
4. MODIFIER REQUIREMENTS: Determine anatomical and procedural modifiers needed

Extract and provide:

PRIMARY PROCEDURES:
- Exact procedure names with anatomical specificity
- Surgical approach (open, arthroscopic, minimally invasive)
- Complexity level (minor, major, complex)

ANATOMICAL DETAILS:
- Specific body region and laterality (right/left/bilateral)
- Multiple locations if applicable
- Anatomical relationships

ANESTHESIA INFORMATION:
- Type required (local, regional, general, MAC)
- Estimated complexity and duration
- Special anesthesia considerations

MODIFIERS NEEDED:
- Anatomical modifiers (RT, LT, 50 for bilateral)
- Procedural modifiers (complexity, approach)
- Multiple procedure indicators

RELATED DIAGNOSES:
- Primary diagnosis requiring procedure
- Secondary relevant conditions
- Anatomical specificity of diagnoses

Medical Note:
"${medicalText}"

STRUCTURED MEDICAL CODING SUMMARY:
Provide a comprehensive summary optimized for CPT code matching that includes all billable components, anatomical precision, and modifier requirements. Focus on terminology that will match CPT code descriptions exactly.`;
  }

  /**
   * Generate embedding using Vertex AI
   * Exact port from original Firebase function embedding logic
   */
  public async generateEmbeddingVector(text: string): Promise<number[]> {
    try {
      const config = this.billing.getConfig();
      
      // Use the same REST API format as original Firebase function for compatibility
      const endpointUrl = config.getEmbeddingEndpointUrl();

      // Get access token from default credentials
      const auth = new GoogleAuth({
        scopes: ["https://www.googleapis.com/auth/cloud-platform"],
      });
      const client = await auth.getClient();
      const accessToken = await client.getAccessToken();

      // Use same task type as database creation for compatibility
      const payload = {
        instances: [
          {
            content: text,
            task_type: "RETRIEVAL_DOCUMENT",
          },
        ],
      };

      const response = await fetch(endpointUrl, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${accessToken.token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      const prediction = data.predictions?.[0];

      // Use same response parsing as original Firebase function
      const embedding = prediction?.embeddings?.values || [];

      console.log(`✅ Generated embedding using REST API: ${embedding.length} dimensions`);
      
      if (embedding.length === 0) {
        throw new Error("Could not create a valid embedding.");
      }

      return embedding;

    } catch (error: any) {
      console.error("❌ Error generating embedding:", error);
      throw new Error("Failed to generate text embedding.");
    }
  }

  /**
   * Validate embedding vector has correct dimensions
   */
  public validateEmbedding(embedding: number[]): boolean {
    const config = this.billing.getConfig();
    
    if (embedding.length !== config.DIMENSIONS) {
      console.error(`❌ Invalid embedding dimensions: ${embedding.length} (expected ${config.DIMENSIONS})`);
      return false;
    }

    // Check if all values are numbers
    if (!embedding.every(x => typeof x === 'number' && !isNaN(x) && isFinite(x))) {
      console.error("❌ Invalid embedding values: not all valid numbers");
      return false;
    }

    return true;
  }
}