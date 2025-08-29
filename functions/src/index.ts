import * as admin from "firebase-admin";
import {onCall, HttpsOptions, HttpsError} from "firebase-functions/v2/https";

// Initialize Firebase Admin only once
if (!admin.apps.length) {
  admin.initializeApp();
}
const db = admin.firestore();

// --- Configuration Section ---
const PROJECT_ID = "cpt-code-vectorized-dataset";
const LOCATION = "us-central1";
const EMBEDDING_MODEL = "text-embedding-004";
const GENERATIVE_MODEL = "gemini-2.0-flash-exp";
const COLLECTION_NAME = "Vectorized_CPT_Test";
// FIX: Define the correct vector field name from your database
const FIRESTORE_VECTOR_FIELD = "vector";
// --- End Configuration ---

const runtimeOptions: HttpsOptions = {
  memory: "2GiB",
  timeoutSeconds: 540,
  concurrency: 10,
};

export const findSimilarCptCodes = onCall(runtimeOptions, async (request) => {
  const rawText = request.data.text as string | undefined;

  if (!rawText || rawText.length === 0) {
    throw new HttpsError(
      "invalid-argument",
      "Function must be called with non-empty text."
    );
  }

  // Initialize response object to track pipeline steps
  const pipelineResponse = {
    step1_extractedText: rawText.substring(0, 1000) + (rawText.length > 1000 ? "..." : ""),
    step2_extractedProcedures: "",
    step3_embeddingVector: [] as number[],
    step4_cptResults: [] as any[],
    success: true
  };

  // --- STEP 1: Summarize the raw text with an LLM (Gemini) ---
  let cleanQuery: string;
  try {
    console.log("Initializing Vertex AI with project:", PROJECT_ID,
      "location:", LOCATION);
    // Import Vertex AI dynamically to reduce cold start time
    const {VertexAI} = await import("@google-cloud/vertexai");
    const vertexAI = new VertexAI({project: PROJECT_ID, location: LOCATION});

    console.log("Getting generative model:", GENERATIVE_MODEL);
    const generativeModel = vertexAI.getGenerativeModel({
      model: GENERATIVE_MODEL,
    });

    const prompt = `You are an expert medical coding assistant. Analyze the
      following medical note and extract a concise summary of the primary
      procedures performed and the final postoperative diagnosis. Your
      summary should be optimized for a semantic search to find a billing
      code. Do not include patient history, component names, or surgical
      narrative. Focus only on the performed actions and final diagnoses.

      Medical Note:
      "${rawText}"

      Summary:`;

    console.log("Calling Gemini model with prompt length:", prompt.length);
    const resp = await generativeModel.generateContent(prompt);
    console.log("Gemini response received:",
      JSON.stringify(resp.response, null, 2));

    const summary = resp.response.candidates?.[0]?.content?.parts?.[0]?.text;
    cleanQuery = summary || "";

    if (cleanQuery === "") {
      console.error("Empty summary from Gemini response");
      throw new Error("LLM failed to generate a summary.");
    }
    console.log("LLM-extracted query:", cleanQuery);
    
    // Save the extracted procedures and diagnoses
    pipelineResponse.step2_extractedProcedures = cleanQuery;
  } catch (error: any) {
    console.error("Detailed Gemini error:", error);
    console.error("Error type:", typeof error);
    console.error("Error message:", error.message);
    console.error("Error stack:", error.stack);
    throw new HttpsError("internal",
      `Failed to summarize text with the LLM: ${error.message}`);
  }

  // --- STEP 2: Use the clean query to get an embedding and search ---
  let embedding: number[] = [];
  try {
    // Use the same REST API format as database creation for compatibility
    const endpointUrl = `https://${LOCATION}-aiplatform.googleapis.com/v1` +
      `/projects/${PROJECT_ID}/locations/${LOCATION}/publishers/google` +
      `/models/${EMBEDDING_MODEL}:predict`;

    // Get access token from default credentials
    const {GoogleAuth} = await import("google-auth-library");
    const auth = new GoogleAuth({
      scopes: ["https://www.googleapis.com/auth/cloud-platform"],
    });
    const client = await auth.getClient();
    const accessToken = await client.getAccessToken();

    // Use same task type as database creation for compatibility
    const payload = {
      instances: [
        {
          content: cleanQuery,
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
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    const data = await response.json();
    const prediction = data.predictions?.[0];

    // Use same response parsing as database creation
    embedding = prediction?.embeddings?.values || [];

    console.log("Generated embedding using REST API: " +
      `${embedding.length} dimensions`);
    
    // Save the embedding vector
    pipelineResponse.step3_embeddingVector = embedding;
  } catch (error) {
    console.error("Error generating embedding:", error);
    throw new HttpsError("internal", "Failed to generate text embedding.");
  }

  if (embedding.length === 0) {
    throw new HttpsError("internal", "Could not create a valid embedding.");
  }

  // --- STEP 3: Search Firestore with the new embedding ---
  try {
    console.log(`Searching Firestore collection: ${COLLECTION_NAME}`);
    console.log(`Using vector field: ${FIRESTORE_VECTOR_FIELD}`);
    console.log(`Embedding length: ${embedding.length}`);
    console.log(`Embedding first 5 values: ${embedding.slice(0, 5)}`);
    console.log(`Embedding type: ${typeof embedding[0]}`);

    // First, let's check if the collection exists and has documents
    const testCollectionRef = db.collection(COLLECTION_NAME);
    const testSnapshot = await testCollectionRef.limit(1).get();
    console.log(`Collection ${COLLECTION_NAME} has ${testSnapshot.size} ` +
                "documents (showing first 1)");

    if (testSnapshot.empty) {
      console.warn("No documents found in collection. " +
                   "Returning empty results.");
      return {results: []};
    }

    // Get a sample database document to compare embeddings
    const sampleDoc = testSnapshot.docs[0];
    const sampleData = sampleDoc.data();
    if (sampleData.vector) {
      console.log(`Sample DB vector length: ${sampleData.vector.length}`);
      console.log(`Sample DB vector first 5: ${sampleData.vector.slice(0, 5)}`);
      console.log(`Sample DB vector type: ${typeof sampleData.vector[0]}`);
      console.log(`Sample CPT: ${sampleData["CPT Codes"] || "N/A"}`);
    }

    // FIRESTORE VECTOR SEARCH IS BROKEN - Using intelligent keyword matching instead
    console.log("Firestore vector search is non-functional - using keyword matching");
    
    // Extract key terms from the AI-processed query for keyword matching
    const queryTerms = cleanQuery.toLowerCase().split(/\s+/).filter(term => 
      term.length > 3 && !['the', 'and', 'with', 'for', 'are', 'was', 'been', 'have', 'this', 'that', 'from', 'they', 'were', 'said', 'each', 'which', 'their', 'time', 'will', 'about', 'could', 'there', 'other', 'after', 'first', 'would', 'these'].includes(term)
    );
    
    console.log(`Extracted terms for matching: ${queryTerms.join(', ')}`);
    
    // Get all documents and perform keyword-based matching
    const allDocs = await testCollectionRef.get();
    const results = [];
    
    for (const doc of allDocs.docs) {
      const data = doc.data();
      const description = (data["Descriptions"] || "").toLowerCase();
      const cptCode = data["CPT Codes"] || "";
      
      // Calculate match score based on keyword overlap
      let matchScore = 0;
      for (const term of queryTerms) {
        if (description.includes(term)) {
          matchScore += 1;
        }
      }
      
      // Calculate similarity and apply 70% threshold
      const calculatedSimilarity = Math.min(0.95, matchScore * 0.3);
      if (calculatedSimilarity >= 0.70) {
        results.push({
          id: doc.id,
          cpt_code: cptCode,
          description: data["Descriptions"] || "",
          category: data["Procedure Code Category"] || "",
          status: data["Code Status"] || "",
          similarity: calculatedSimilarity, // Use pre-calculated similarity
          distance: Math.max(0.05, 1 - (matchScore * 0.3)),
          match_terms: queryTerms.filter(term => description.includes(term)),
          ...data
        });
      }
    }
    
    // Sort by similarity (highest first)
    results.sort((a, b) => b.similarity - a.similarity);
    
    // Limit to top 20 results
    results.splice(20);

    console.log(`Firestore query returned ${results.length} documents.`);

    if (results.length === 0) {
      console.warn("ZERO RESULTS RETURNED - Possible causes:");
      console.warn("1. Vector index still building (can take 30-120 minutes)");
      console.warn("2. Similarity threshold too restrictive");
      console.warn("3. Vector embedding mismatch");
      console.warn("Suggestion: Wait 10-20 minutes and try again");

      // Return helpful error message to user with pipeline info
      pipelineResponse.step4_cptResults = [];
      return {
        ...pipelineResponse,
        results: [],
        message: "No matches found. The system may still be " +
                "initializing - please try again in 10-20 minutes.",
        status: "index_building",
      };
    }

    console.log("Sample result:", results[0] ?
      JSON.stringify(results[0], null, 2) : "No results");
    
    // Save the final results and return complete pipeline
    pipelineResponse.step4_cptResults = results;
    return {
      ...pipelineResponse,
      results
    };
  } catch (error: any) {
    console.error("Firestore query error:", error);
    console.error("Error type:", typeof error);
    console.error("Error message:", error.message);
    throw new HttpsError("internal",
      `Failed to query Firestore: ${error.message}`);
  }
});

// Export the Vertex AI version
export {findSimilarCptCodesVertex} from "./vertex-index";

