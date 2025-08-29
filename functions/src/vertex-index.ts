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

// Vertex AI Vector Search Configuration
const VERTEX_ENDPOINT_NAME = 
  "projects/65650340228/locations/us-central1/indexEndpoints/2122622590584356864";
const DEPLOYED_INDEX_ID = "cpt_deployed_index";
// --- End Configuration ---

const runtimeOptions: HttpsOptions = {
  memory: "2GiB",
  timeoutSeconds: 540,
  concurrency: 10,
};

export const findSimilarCptCodesVertex = onCall(runtimeOptions, async (request) => {
  const rawText = request.data.text as string | undefined;

  if (!rawText || rawText.length === 0) {
    throw new HttpsError(
      "invalid-argument",
      "Function must be called with non-empty text."
    );
  }

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

    const prompt = `You are an expert medical coding assistant specializing in CPT code identification. Analyze the following clinical documentation and extract ONLY the key billable procedures and primary diagnoses that would require CPT codes.

INSTRUCTIONS:
- Extract the main surgical or therapeutic procedures performed
- Include the primary and secondary diagnoses
- Focus on billable services, not routine care
- Use standard medical terminology
- Be concise but specific
- Format as: "Procedure: [procedure name]. Diagnosis: [diagnosis]"

CLINICAL DOCUMENTATION:
"${rawText}"

EXTRACTED PROCEDURES AND DIAGNOSES:`;

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
  } catch (error: any) {
    console.error("Detailed Gemini error:", error);
    console.error("Error type:", typeof error);
    console.error("Error message:", error.message);
    console.error("Error stack:", error.stack);
    throw new HttpsError("internal",
      `Failed to summarize text with the LLM: ${error.message}`);
  }

  // --- STEP 2: Use the clean query to get an embedding ---
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

    // Use RETRIEVAL_QUERY for search queries (different from database RETRIEVAL_DOCUMENT)
    const payload = {
      instances: [
        {
          content: cleanQuery,
          task_type: "RETRIEVAL_QUERY",
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
  } catch (error) {
    console.error("Error generating embedding:", error);
    throw new HttpsError("internal", "Failed to generate text embedding.");
  }

  if (embedding.length === 0) {
    throw new HttpsError("internal", "Could not create a valid embedding.");
  }

  // --- STEP 3: Search using Vertex AI Vector Search ---
  try {
    console.log(`Searching Vertex AI Vector Search endpoint: ${VERTEX_ENDPOINT_NAME}`);
    console.log(`Using deployed index: ${DEPLOYED_INDEX_ID}`);
    console.log(`Embedding length: ${embedding.length}`);

    // Use the AI Platform SDK instead of REST API
    const {MatchServiceClient} = await import("@google-cloud/aiplatform");
    const matchClient = new MatchServiceClient({
      apiEndpoint: `${LOCATION}-aiplatform.googleapis.com`,
    });

    const request = {
      indexEndpoint: VERTEX_ENDPOINT_NAME,
      deployedIndexId: DEPLOYED_INDEX_ID,
      queries: [
        {
          datapoint: {
            featureVector: embedding,
          },
          neighborCount: 20,
        },
      ],
      returnFullDatapoint: false,
    };

    console.log("Performing vector search via AI Platform SDK...");
    const [response] = await matchClient.findNeighbors(request);
    const searchResponse = response;

    const nearestNeighbors = searchResponse.nearestNeighbors?.[0]?.neighbors || [];
    console.log(`Vector search returned ${nearestNeighbors.length} results`);

    if (nearestNeighbors.length === 0) {
      console.warn("ZERO RESULTS RETURNED from Vertex AI Vector Search");
      console.warn("Possible causes:");
      console.warn("1. Index deployment still in progress");
      console.warn("2. No similar vectors found");
      console.warn("3. Configuration issue");

      return {
        results: [],
        message: "No matches found. The system may still be " +
                "initializing - please try again in a few minutes.",
        status: "no_results",
      };
    }

    // --- STEP 4: Get full CPT details from Firestore for the matched IDs ---
    const cptCodes = nearestNeighbors.map((neighbor: any) => {
      // Extract CPT code from the datapoint ID
      const datapointId = neighbor.datapoint?.datapointId || "";
      // Remove 'cpt_' prefix if present
      return datapointId.startsWith("cpt_") ? datapointId.substring(4) : datapointId;
    });

    console.log(`Getting details for CPT codes: ${cptCodes.join(", ")}`);

    // Get full details from Firestore
    const results: any[] = [];

    for (let i = 0; i < nearestNeighbors.length; i++) {
      const neighbor = nearestNeighbors[i];
      const cptCode = cptCodes[i];
      const distance = neighbor.distance || 0;
      const similarity = 1.0 - distance; // Convert distance to similarity

      try {
        // Query Firestore for the full CPT details
        const cptQuery = db.collection(COLLECTION_NAME)
          .where("CPT Codes", "==", cptCode)
          .limit(1);

        const cptSnapshot = await cptQuery.get();

        if (!cptSnapshot.empty) {
          const cptDoc = cptSnapshot.docs[0];
          const cptData = cptDoc.data();

          results.push({
            id: cptDoc.id,
            cpt_code: cptData["CPT Codes"] || cptCode,
            description: cptData["Descriptions"] || "",
            category: cptData["Procedure Code Category"] || "",
            status: cptData["Code Status"] || "",
            similarity: similarity,
            distance: distance,
            ...cptData, // Include all other fields
          });
        } else {
          // Fallback if not found in Firestore
          console.warn(`CPT code ${cptCode} not found in Firestore`);
          results.push({
            cpt_code: cptCode,
            description: "Details not found",
            similarity: similarity,
            distance: distance,
          });
        }
      } catch (error) {
        console.error(`Error getting details for CPT ${cptCode}:`, error);
        // Continue with other results
        results.push({
          cpt_code: cptCode,
          description: "Error retrieving details",
          similarity: similarity,
          distance: distance,
        });
      }
    }

    console.log(`Firestore query completed. Returning ${results.length} results.`);
    console.log("Sample result:", results[0] ?
      JSON.stringify({...results[0], description: results[0].description?.substring(0, 100)}, null, 2) : "No results");

    return {results};
  } catch (error: any) {
    console.error("Vertex AI Vector Search error:", error);
    console.error("Error type:", typeof error);
    console.error("Error message:", error.message);

    // Check if it's a deployment issue
    if (error.message?.includes("503") || error.message?.includes("unavailable")) {
      return {
        results: [],
        message: "Vector search service is still initializing. Please try again in a few minutes.",
        status: "service_initializing",
      };
    }

    throw new HttpsError("internal",
      `Failed to query Vertex AI Vector Search: ${error.message}`);
  }
});
