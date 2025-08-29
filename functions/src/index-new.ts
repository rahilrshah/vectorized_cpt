/**
 * Updated Firebase Functions using Billing Class Architecture
 * Maintains backward compatibility while using new organized structure
 */

import * as admin from "firebase-admin";
import { onCall, HttpsOptions, HttpsError } from "firebase-functions/v2/https";
import { Billing } from "./billing";

// Initialize Firebase Admin only once
if (!admin.apps.length) {
  admin.initializeApp();
}

// Runtime configuration
const runtimeOptions: HttpsOptions = {
  memory: "2GiB",
  timeoutSeconds: 540,
  concurrency: 10,
};

// Initialize global Billing system instance
let billingSystem: Billing | null = null;

function getBillingSystem(): Billing {
  if (!billingSystem) {
    billingSystem = new Billing();
  }
  return billingSystem;
}

/**
 * Main CPT Code Search Function - Updated to use Billing class
 * Maintains exact same interface as original function
 */
export const findSimilarCptCodes = onCall(runtimeOptions, async (request) => {
  const rawText = request.data.text as string | undefined;

  if (!rawText || rawText.length === 0) {
    throw new HttpsError(
      "invalid-argument",
      "Function must be called with non-empty text."
    );
  }

  try {
    // Use the new Billing system
    const billing = getBillingSystem();
    
    console.log("🏥 Processing request using Billing class architecture");
    
    // Process medical note using the unified Billing system
    const result = await billing.processMedicalNote(rawText);
    
    console.log(`✅ Billing system processing complete: ${result.success}`);
    
    return result;

  } catch (error: any) {
    console.error("❌ Billing system error:", error);
    
    // Return error in same format as original function
    return {
      step1_extractedText: rawText.substring(0, 1000) + (rawText.length > 1000 ? "..." : ""),
      step2_extractedProcedures: "",
      step3_embeddingVector: [],
      step4_cptResults: [],
      results: [],
      success: false,
      error: error.message
    };
  }
});

/**
 * New endpoint: Direct CPT Search (skip AI processing)
 */
export const searchCptCodesDirect = onCall(runtimeOptions, async (request) => {
  const query = request.data.query as string | undefined;
  const maxResults = request.data.maxResults as number | undefined;

  if (!query || query.length === 0) {
    throw new HttpsError(
      "invalid-argument",
      "Function must be called with non-empty query."
    );
  }

  try {
    const billing = getBillingSystem();
    
    console.log("🔍 Direct CPT search using Billing class");
    
    const results = await billing.searchCPTCodes(query, maxResults || 20);
    
    return {
      query: query,
      results: results,
      total_results: results.length,
      success: true
    };

  } catch (error: any) {
    console.error("❌ Direct search error:", error);
    
    return {
      query: query,
      results: [],
      total_results: 0,
      success: false,
      error: error.message
    };
  }
});

/**
 * System Health Check endpoint
 */
export const systemHealth = onCall(runtimeOptions, async (request) => {
  try {
    const billing = getBillingSystem();
    
    console.log("🩺 System health check using Billing class");
    
    const healthStatus = await billing.getSystemHealth();
    
    return healthStatus;

  } catch (error: any) {
    console.error("❌ Health check error:", error);
    
    return {
      status: "unhealthy",
      timestamp: Date.now(),
      services: {},
      version: "1.0.0",
      error: error.message
    };
  }
});

/**
 * Configuration endpoint (for debugging)
 */
export const getSystemConfig = onCall(runtimeOptions, async (request) => {
  try {
    const billing = getBillingSystem();
    const config = billing.getConfig();
    
    // Return sanitized configuration (no sensitive data)
    return {
      project_id: config.PROJECT_ID,
      location: config.LOCATION,
      collection_name: config.COLLECTION_NAME,
      embedding_model: config.EMBEDDING_MODEL,
      generative_model: config.GENERATIVE_MODEL,
      dimensions: config.DIMENSIONS,
      version: "1.0.0",
      architecture: "Billing Class"
    };

  } catch (error: any) {
    console.error("❌ Config retrieval error:", error);
    
    return {
      error: error.message,
      version: "1.0.0"
    };
  }
});

// Export the Billing class for potential direct use
export { Billing } from "./billing";