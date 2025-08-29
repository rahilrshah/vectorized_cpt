/**
 * Billing Configuration Class
 * TypeScript version of the Python BillingConfig
 */

export class BillingConfig {
  // --- Firebase Function Config ---
  public readonly PROJECT_ID = "cpt-code-vectorized-dataset";
  public readonly LOCATION = "us-central1";
  public readonly EMBEDDING_MODEL = "text-embedding-004";
  public readonly GENERATIVE_MODEL = "gemini-2.0-flash-exp";
  public readonly COLLECTION_NAME = "Vectorized_CPT_Test";
  public readonly FIRESTORE_VECTOR_FIELD = "vector";

  // --- Processing Config ---
  public readonly DIMENSIONS = 768;
  public readonly SIMILARITY_THRESHOLD = 0.70;
  public readonly MAX_RESULTS_DEFAULT = 20;

  // --- Runtime Config ---
  public readonly MEMORY = "2GiB";
  public readonly TIMEOUT_SECONDS = 540;
  public readonly CONCURRENCY = 10;

  constructor() {
    console.log("📋 Configuration loaded successfully");
    console.log(`   Project: ${this.PROJECT_ID}`);
    console.log(`   Location: ${this.LOCATION}`);
    console.log(`   Collection: ${this.COLLECTION_NAME}`);
    console.log(`   Embedding Model: ${this.EMBEDDING_MODEL}`);
    console.log(`   Generative Model: ${this.GENERATIVE_MODEL}`);
  }

  public getEmbeddingEndpointUrl(): string {
    return `https://${this.LOCATION}-aiplatform.googleapis.com/v1` +
           `/projects/${this.PROJECT_ID}/locations/${this.LOCATION}` +
           `/publishers/google/models/${this.EMBEDDING_MODEL}:predict`;
  }

  public getGenerativeEndpointUrl(): string {
    return `https://${this.LOCATION}-aiplatform.googleapis.com/v1` +
           `/projects/${this.PROJECT_ID}/locations/${this.LOCATION}` +
           `/publishers/google/models/${this.GENERATIVE_MODEL}:generateContent`;
  }

  public validate(): boolean {
    const required = [
      this.PROJECT_ID,
      this.LOCATION,
      this.COLLECTION_NAME,
      this.EMBEDDING_MODEL,
      this.GENERATIVE_MODEL
    ];

    const missing = required.filter(field => !field);
    
    if (missing.length > 0) {
      console.error(`❌ Missing required configuration fields: ${missing.length} missing`);
      return false;
    }

    console.log("✅ Configuration validation passed");
    return true;
  }

  public toDict(): any {
    return {
      project_id: this.PROJECT_ID,
      location: this.LOCATION,
      collection_name: this.COLLECTION_NAME,
      embedding_model: this.EMBEDDING_MODEL,
      generative_model: this.GENERATIVE_MODEL,
      dimensions: this.DIMENSIONS,
      similarity_threshold: this.SIMILARITY_THRESHOLD
    };
  }
}