/**
 * Firestore Service
 * Handles all Firestore database operations
 */

import * as admin from "firebase-admin";
import { Billing } from '../index';

export class FirestoreService {
  private billing: Billing;
  private db: admin.firestore.Firestore;
  private collection: admin.firestore.CollectionReference;

  constructor(billing: Billing) {
    this.billing = billing;
    
    const config = this.billing.getConfig();
    
    // Initialize Firestore
    this.db = admin.firestore();
    this.collection = this.db.collection(config.COLLECTION_NAME);
    
    console.log(`🗄️ Firestore Service initialized`);
    console.log(`   Collection: ${config.COLLECTION_NAME}`);
    console.log(`   Vector Field: ${config.FIRESTORE_VECTOR_FIELD}`);
  }

  /**
   * Get sample documents from collection
   * Used for debugging and health checks
   */
  public async getSampleDocuments(limit: number = 5): Promise<any[]> {
    try {
      const snapshot = await this.collection.limit(limit).get();
      
      const sampleDocs: any[] = [];
      snapshot.forEach(doc => {
        sampleDocs.push({ id: doc.id, ...doc.data() });
      });

      console.log(`📄 Retrieved ${sampleDocs.length} sample documents`);
      return sampleDocs;

    } catch (error: any) {
      console.error(`❌ Error getting sample documents: ${error.message}`);
      return [];
    }
  }

  /**
   * Get all documents from collection
   * Used for keyword-based search fallback
   */
  public async getAllDocuments(): Promise<any[]> {
    try {
      const config = this.billing.getConfig();
      console.log(`📄 Retrieving all documents from ${config.COLLECTION_NAME}`);
      
      const snapshot = await this.collection.get();
      
      const allDocs: any[] = [];
      let count = 0;
      
      snapshot.forEach(doc => {
        allDocs.push({ id: doc.id, ...doc.data() });
        count++;
        
        // Print progress every 1000 documents
        if (count % 1000 === 0) {
          console.log(`   Loaded ${count} documents...`);
        }
      });

      console.log(`✅ Retrieved ${allDocs.length} total documents`);
      return allDocs;

    } catch (error: any) {
      console.error(`❌ Error getting all documents: ${error.message}`);
      return [];
    }
  }

  /**
   * Perform vector search in Firestore
   * Note: Firestore vector search is currently non-functional in this setup
   */
  public async vectorSearch(embedding: number[], limit: number = 20): Promise<any[]> {
    try {
      console.log(`🔍 Attempting Firestore vector search...`);
      console.log(`   Vector length: ${embedding.length}`);
      console.log(`   Limit: ${limit}`);

      // TODO: Implement actual vector search when Firestore supports it properly
      // For now, this will return empty and fall back to keyword search

      console.log("⚠️ Vector search not implemented - falling back to keyword search");
      return [];

    } catch (error: any) {
      console.error(`❌ Vector search error: ${error.message}`);
      return [];
    }
  }

  /**
   * Keyword-based search in document descriptions
   * Fallback method when vector search fails
   */
  public async keywordSearch(keywords: string[], limit: number = 20): Promise<any[]> {
    try {
      console.log(`🔍 Performing keyword search for: ${keywords}`);

      const results: any[] = [];

      // Get all documents
      const allDocs = await this.getAllDocuments();

      for (const doc of allDocs) {
        const description = (doc["Descriptions"] || "").toLowerCase();

        // Count keyword matches
        const matches = keywords.filter(keyword => 
          description.includes(keyword.toLowerCase())
        ).length;

        if (matches > 0) {
          // Calculate similarity score
          const similarity = Math.min(0.9, matches / keywords.length);

          const result = {
            ...doc,  // Include all original fields
            similarity: similarity,
            matches: matches,
            match_keywords: keywords.filter(k => 
              description.includes(k.toLowerCase())
            )
          };
          results.push(result);
        }
      }

      // Sort by matches and similarity
      results.sort((a, b) => {
        if (b.matches !== a.matches) return b.matches - a.matches;
        return b.similarity - a.similarity;
      });

      const limitedResults = results.slice(0, limit);
      console.log(`✅ Keyword search found ${limitedResults.length} matches`);
      return limitedResults;

    } catch (error: any) {
      console.error(`❌ Keyword search error: ${error.message}`);
      return [];
    }
  }

  /**
   * Get collection statistics for health checks
   */
  public async getCollectionStats(): Promise<any> {
    try {
      // Get sample documents to check collection status
      const sampleDocs = await this.getSampleDocuments(10);
      const config = this.billing.getConfig();

      const stats = {
        collection_name: config.COLLECTION_NAME,
        document_count: sampleDocs.length,
        sample_documents: sampleDocs.length,
        has_vector_field: false,
        vector_dimensions: 0,
        sample_fields: [] as string[]
      };

      // Check if documents have vector field
      if (sampleDocs.length > 0) {
        const firstDoc = sampleDocs[0];
        if (firstDoc[config.FIRESTORE_VECTOR_FIELD]) {
          stats.has_vector_field = true;
          const vector = firstDoc[config.FIRESTORE_VECTOR_FIELD];
          if (Array.isArray(vector)) {
            stats.vector_dimensions = vector.length;
          }
        }

        // Add sample field information
        stats.sample_fields = Object.keys(firstDoc);
      }

      return stats;

    } catch (error: any) {
      console.error(`❌ Error getting collection stats: ${error.message}`);
      return {
        collection_name: this.billing.getConfig().COLLECTION_NAME,
        error: error.message,
        document_count: 0
      };
    }
  }

  /**
   * Add a document to the collection
   */
  public async addDocument(docId: string, data: any): Promise<boolean> {
    try {
      const docRef = this.collection.doc(docId);
      await docRef.set(data);

      console.log(`✅ Added document: ${docId}`);
      return true;

    } catch (error: any) {
      console.error(`❌ Error adding document ${docId}: ${error.message}`);
      return false;
    }
  }

  /**
   * Update a document in the collection
   */
  public async updateDocument(docId: string, updates: any): Promise<boolean> {
    try {
      const docRef = this.collection.doc(docId);
      await docRef.update(updates);

      console.log(`✅ Updated document: ${docId}`);
      return true;

    } catch (error: any) {
      console.error(`❌ Error updating document ${docId}: ${error.message}`);
      return false;
    }
  }
}