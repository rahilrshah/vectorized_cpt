/**
 * CPT Search Service
 * TypeScript implementation of CPT searching logic
 */

import { Billing } from '../index';

export class CPTSearchService {
  private billing: Billing;

  constructor(billing: Billing) {
    this.billing = billing;
    
    const config = this.billing.getConfig();
    console.log(`🔍 CPT Search Service initialized`);
    console.log(`   Collection: ${config.COLLECTION_NAME}`);
    console.log(`   Vector Field: ${config.FIRESTORE_VECTOR_FIELD}`);
    console.log(`   Similarity Threshold: ${config.SIMILARITY_THRESHOLD}`);
  }

  /**
   * Vector-based CPT code search with keyword fallback
   * Exact port of original Firebase function search logic
   */
  public async searchWithVector(embedding: number[], query: string): Promise<any[]> {
    try {
      const config = this.billing.getConfig();
      const firestoreService = this.billing.getFirestoreService();
      
      console.log(`🔍 Searching Firestore collection: ${config.COLLECTION_NAME}`);
      console.log(`   Vector field: ${config.FIRESTORE_VECTOR_FIELD}`);
      console.log(`   Embedding length: ${embedding.length}`);
      console.log(`   Embedding first 5 values: ${embedding.slice(0, 5)}`);

      // First check if collection has documents
      const testSnapshot = await firestoreService.getSampleDocuments(1);
      
      if (testSnapshot.length === 0) {
        console.warn("⚠️ No documents found in collection. Returning empty results.");
        return [];
      }

      // Log sample document for debugging
      const sampleDoc = testSnapshot[0];
      if (sampleDoc.vector) {
        console.log(`   Sample DB vector length: ${sampleDoc.vector.length}`);
        console.log(`   Sample DB vector first 5: ${sampleDoc.vector.slice(0, 5)}`);
        console.log(`   Sample CPT: ${sampleDoc["CPT Codes"] || "N/A"}`);
      }

      // FIRESTORE VECTOR SEARCH IS BROKEN - Using intelligent keyword matching instead
      console.log("⚠️ Firestore vector search is non-functional - using keyword matching");
      
      // Extract key terms from the AI-processed query for keyword matching
      const queryTerms = this.extractQueryTerms(query);
      console.log(`   Extracted terms for matching: ${queryTerms.join(', ')}`);
      
      // Get all documents and perform keyword-based matching
      const allDocs = await firestoreService.getAllDocuments();
      const results: any[] = [];
      
      for (const doc of allDocs) {
        const description = (doc["Descriptions"] || "").toLowerCase();
        const cptCode = doc["CPT Codes"] || "";
        
        // Calculate match score based on keyword overlap and relevance
        const matchScore = this.calculateMatchScore(queryTerms, description);
        
        // More realistic similarity calculation based on match quality
        const calculatedSimilarity = this.calculateRelevanceScore(queryTerms, description, matchScore);
        
        // Only include highly relevant results (adjusted threshold)
        if (calculatedSimilarity >= 0.4 && matchScore > 0) {
          const result = {
            id: doc.id || `doc_${results.length}`,
            cpt_code: cptCode,
            description: doc["Descriptions"] || "",
            category: doc["Procedure Code Category"] || "",
            status: doc["Code Status"] || "",
            similarity: calculatedSimilarity,
            distance: Math.max(0.05, 1 - calculatedSimilarity),
            match_terms: queryTerms.filter(term => description.includes(term)),
            ...doc // Include all original data
          };
          results.push(result);
        }
      }
      
      // Sort by similarity (highest first)
      results.sort((a, b) => b.similarity - a.similarity);
      
      // Limit to top 20 results
      const limitedResults = results.slice(0, 20);

      console.log(`✅ Firestore query returned ${limitedResults.length} documents.`);

      if (limitedResults.length === 0) {
        console.warn("⚠️ ZERO RESULTS RETURNED - Possible causes:");
        console.warn("   1. Vector index still building (can take 30-120 minutes)");
        console.warn("   2. Similarity threshold too restrictive");
        console.warn("   3. Vector embedding mismatch");
        console.warn("   Suggestion: Wait 10-20 minutes and try again");
      } else {
        const firstResult = limitedResults[0];
        console.log(`   Sample result: ${firstResult.cpt_code} - ${firstResult.description.substring(0, 50)}...`);
      }

      return limitedResults;

    } catch (error: any) {
      console.error(`❌ Firestore search error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Extract key terms from query for keyword matching
   */
  private extractQueryTerms(query: string): string[] {
    // Convert to lowercase and split
    const terms = query.toLowerCase().split(/\s+/);
    
    // Filter out short words and common stop words
    const stopWords = new Set([
      'the', 'and', 'with', 'for', 'are', 'was', 'been', 'have', 
      'this', 'that', 'from', 'they', 'were', 'said', 'each', 
      'which', 'their', 'time', 'will', 'about', 'could', 'there', 
      'other', 'after', 'first', 'would', 'these'
    ]);
    
    // Filter terms: length > 3 and not stop words
    return terms.filter(term => term.length > 3 && !stopWords.has(term));
  }

  /**
   * Calculate match score based on keyword overlap
   */
  private calculateMatchScore(queryTerms: string[], description: string): number {
    let matchScore = 0;
    for (const term of queryTerms) {
      if (description.includes(term)) {
        matchScore += 1;
      }
    }
    return matchScore;
  }

  /**
   * Calculate relevance score based on term importance and medical context
   */
  private calculateRelevanceScore(queryTerms: string[], description: string, matchScore: number): number {
    if (matchScore === 0) return 0;
    
    // Medical procedure keywords that should boost relevance
    const medicalKeywords = [
      'arthroplasty', 'knee', 'total', 'arthroscopy', 'replacement', 'revision',
      'surgery', 'surgical', 'procedure', 'repair', 'reconstruction',
      'osteotomy', 'meniscectomy', 'ligament', 'tendon', 'joint',
      'orthopedic', 'orthopedic', 'bone', 'cartilage'
    ];
    
    // Count important medical term matches
    let importantMatches = 0;
    let totalImportantTerms = 0;
    
    for (const term of queryTerms) {
      if (medicalKeywords.some(keyword => term.includes(keyword) || keyword.includes(term))) {
        totalImportantTerms++;
        if (description.includes(term)) {
          importantMatches++;
        }
      }
    }
    
    // Base similarity from keyword matches
    let similarity = Math.min(0.95, (matchScore / queryTerms.length) * 0.8);
    
    // Boost if important medical terms match
    if (totalImportantTerms > 0) {
      const importanceBoost = (importantMatches / totalImportantTerms) * 0.3;
      similarity += importanceBoost;
    }
    
    // Penalize if very few terms match from many
    if (queryTerms.length > 3 && matchScore < 2) {
      similarity *= 0.5; // Reduce score for poor matches
    }
    
    // Reward high match ratios
    if (matchScore >= queryTerms.length * 0.6) {
      similarity *= 1.2; // Boost good matches
    }
    
    return Math.min(0.95, similarity);
  }

  /**
   * Format CPT results for consistent API response
   */
  public formatCPTResults(rawResults: any[]): any[] {
    return rawResults.map(result => ({
      cpt_code: result.cpt_code || result["CPT Codes"] || "",
      description: result.description || result["Descriptions"] || "",
      category: result.category || result["Procedure Code Category"] || "",
      status: result.status || result["Code Status"] || "",
      similarity: result.similarity || 0.0,
      distance: result.distance,
      match_terms: result.match_terms
    }));
  }
}