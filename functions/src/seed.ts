import * as admin from "firebase-admin";
import {v1} from "@google-cloud/aiplatform";
import {google} from "@google-cloud/aiplatform/build/protos/protos";
import {parse} from "csv-parse/sync";
import * as fs from "fs";
import * as path from "path";

// --- CONFIGURATION ---
// eslint-disable-next-line @typescript-eslint/no-var-requires
const serviceAccount = require(
  "../cpt-code-vectorized-dataset-firebase-adminsdk-fbsvc-2c5f693340.json"
);

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});
const db = admin.firestore();

const PROJECT_ID = "cpt-code-vectorized-dataset";
const LOCATION = "us-central1";
const EMBEDDING_MODEL = "text-embedding-004";
const CSV_FILENAME = "CPT_Codes_Raw.csv";
const COLLECTION_NAME = "Vectorized_CPT_Test";

// FIX: Use the EXACT field names from your Firestore and CSV
const CSV_DESCRIPTION_COLUMN = "Descriptions";
const CSV_CPT_CODE_COLUMN = "CPT Codes"; // This must match your CSV header
const FIRESTORE_CPT_CODE_FIELD = "CPT Codes";
const FIRESTORE_VECTOR_FIELD = "vector"; // This must match your Firestore field

// --- SCRIPT LOGIC ---
/**
 * Generate embedding for text using Vertex AI
 * @param {string} text - Text to embed
 * @return {Promise<number[]>} Embedding vector
 */
async function getEmbedding(text: string): Promise<number[]> {
  const clientOptions = {apiEndpoint: `${LOCATION}-aiplatform.googleapis.com`};
  const predictionServiceClient = new v1.PredictionServiceClient(clientOptions);
  const endpoint = `projects/${PROJECT_ID}/locations/${LOCATION}` +
    `/publishers/google/models/${EMBEDDING_MODEL}`;
  const instance = {
    structValue: {
      fields: {
        content: {stringValue: text},
        task_type: {stringValue: "RETRIEVAL_DOCUMENT"},
      },
    },
  };
  const requestPayload = {
    endpoint,
    instances: [instance as google.protobuf.IValue],
  };
  const [response] = await predictionServiceClient.predict(requestPayload);
  const prediction = (response.predictions || [])[0];
  const values = prediction.structValue?.fields?.embeddings?.structValue
    ?.fields?.values?.listValue?.values;
  return values?.map((v) => v.numberValue || 0) || [];
}

/**
 * Repopulate database with new vectors
 */
async function repopulateDatabase() {
  console.log(
    "--- Starting Firestore Repopulation " +
    `Process for collection: ${COLLECTION_NAME} ---`
  );
  const csvPath = path.join(__dirname, "..", CSV_FILENAME);
  const fileContent = fs.readFileSync(csvPath, {encoding: "utf-8"});
  const records: { [key: string]: string }[] = parse(fileContent, {
    columns: true,
    skip_empty_lines: true,
  });
  console.log(`Found ${records.length} records in CSV.`);

  for (const [index, record] of records.entries()) {
    const cptCode = record[CSV_CPT_CODE_COLUMN];
    const description = record[CSV_DESCRIPTION_COLUMN];

    if (!cptCode || !description) {
      console.warn(`[Record ${index + 1}] Skipping record.`);
      continue;
    }
    const cleanCptCode = cptCode.trim();
    try {
      process.stdout.write(
        `[Record ${index + 1}/${records.length}] CPT ${cleanCptCode}: `
      );

      // FIX: Query using the correct Firestore field name
      const query = db.collection(COLLECTION_NAME)
        .where(FIRESTORE_CPT_CODE_FIELD, "==", cleanCptCode).limit(1);
      const snapshot = await query.get();

      if (snapshot.empty) {
        console.warn(
          "SKIPPED. No doc found with " +
          `${FIRESTORE_CPT_CODE_FIELD} = "${cleanCptCode}".`
        );
        continue;
      }
      const docId = snapshot.docs[0].id;
      process.stdout.write(`Found doc (${docId}). Generating vector... `);
      const newVector = await getEmbedding(description);

      if (newVector.length === 0) {
        console.warn("SKIPPED. Failed to generate vector.");
        continue;
      }
      const docRef = db.collection(COLLECTION_NAME).doc(docId);

      // FIX: Update using the correct Firestore field name, dynamically
      await docRef.update({
        [FIRESTORE_VECTOR_FIELD]: newVector,
      });
      console.log("UPDATED.");
    } catch (error) {
      console.error(
        `\nERROR on record ${index + 1} (CPT ${cptCode}):`,
        error
      );
    }
  }
  console.log("--- Repopulation Process Complete ---");
}

repopulateDatabase();

