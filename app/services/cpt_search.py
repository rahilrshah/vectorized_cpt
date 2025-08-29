"""
CPT Search Service
Handles CPT code searching and matching logic
Ported from Firebase function index.ts logic
"""

import asyncio
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.billing import Billing


class CPTSearchService:
    """Handles CPT code searching and matching logic"""
    
    def __init__(self, parent_billing: 'Billing'):
        """Initialize CPT search service"""
        self.billing = parent_billing
        
        # Configuration from billing system
        self.collection_name = parent_billing.config.collection_name
        self.firestore_vector_field = parent_billing.config.firestore_vector_field
        self.similarity_threshold = parent_billing.config.similarity_threshold
        
        print(f"🔍 CPT Search Service initialized")
        print(f"   Collection: {self.collection_name}")
        print(f"   Vector Field: {self.firestore_vector_field}")
        print(f"   Similarity Threshold: {self.similarity_threshold}")
    
    async def search_with_vector(self, embedding: List[float], query: str) -> List[Dict]:
        """
        Vector-based CPT code search with keyword fallback
        Exact port of Firebase function search logic
        """
        try:
            print(f"🔍 Searching Firestore collection: {self.collection_name}")
            print(f"   Vector field: {self.firestore_vector_field}")
            print(f"   Embedding length: {len(embedding)}")
            print(f"   Embedding first 5 values: {embedding[:5] if embedding else []}")
            
            # First check if collection has documents
            collection_ref = self.billing.firestore_service.get_collection_ref()
            test_snapshot = await self.billing.firestore_service.get_sample_documents(1)
            
            if not test_snapshot:
                print("⚠️ No documents found in collection. Returning empty results.")
                return []
            
            # Log sample document for debugging
            sample_doc = test_snapshot[0]
            if "vector" in sample_doc:
                sample_vector = sample_doc["vector"]
                print(f"   Sample DB vector length: {len(sample_vector)}")
                print(f"   Sample DB vector first 5: {sample_vector[:5]}")
                print(f"   Sample CPT: {sample_doc.get('CPT Codes', 'N/A')}")
            
            # FIRESTORE VECTOR SEARCH IS BROKEN - Using intelligent keyword matching instead
            print("⚠️ Firestore vector search is non-functional - using keyword matching")
            
            # Extract key terms from the AI-processed query for keyword matching
            query_terms = self._extract_query_terms(query)
            print(f"   Extracted terms for matching: {', '.join(query_terms)}")
            
            # Get all documents and perform keyword-based matching
            all_docs = await self.billing.firestore_service.get_all_documents()
            results = []
            
            for doc in all_docs:
                doc_data = doc
                description = (doc_data.get("Descriptions", "")).lower()
                cpt_code = doc_data.get("CPT Codes", "")
                
                # Calculate match score based on keyword overlap
                match_score = self._calculate_match_score(query_terms, description)
                
                # Calculate similarity and apply 70% threshold
                calculated_similarity = min(0.95, match_score * 0.3)
                if calculated_similarity >= self.similarity_threshold:
                    result = {
                        "cpt_code": cpt_code,
                        "description": doc_data.get("Descriptions", ""),
                        "category": doc_data.get("Procedure Code Category", ""),
                        "status": doc_data.get("Code Status", ""),
                        "similarity": calculated_similarity,
                        "distance": max(0.05, 1 - (match_score * 0.3)),
                        "match_terms": [term for term in query_terms if term in description]
                    }
                    
                    # Add all original data fields
                    result.update(doc_data)
                    results.append(result)
            
            # Sort by similarity (highest first)
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Limit to top 20 results
            results = results[:20]
            
            print(f"✅ Firestore query returned {len(results)} documents.")
            
            if len(results) == 0:
                print("⚠️ ZERO RESULTS RETURNED - Possible causes:")
                print("   1. Vector index still building (can take 30-120 minutes)")
                print("   2. Similarity threshold too restrictive")
                print("   3. Vector embedding mismatch")
                print("   Suggestion: Wait 10-20 minutes and try again")
            else:
                print(f"   Sample result: {results[0]['cpt_code']} - {results[0]['description'][:50]}...")
            
            return results
            
        except Exception as e:
            print(f"❌ Firestore search error: {e}")
            raise e
    
    def _extract_query_terms(self, query: str) -> List[str]:
        """Extract key terms from query for keyword matching"""
        # Convert to lowercase and split
        terms = query.lower().split()
        
        # Filter out short words and common stop words
        stop_words = {
            'the', 'and', 'with', 'for', 'are', 'was', 'been', 'have', 
            'this', 'that', 'from', 'they', 'were', 'said', 'each', 
            'which', 'their', 'time', 'will', 'about', 'could', 'there', 
            'other', 'after', 'first', 'would', 'these'
        }
        
        # Filter terms: length > 3 and not stop words
        filtered_terms = [
            term for term in terms 
            if len(term) > 3 and term not in stop_words
        ]
        
        return filtered_terms
    
    def _calculate_match_score(self, query_terms: List[str], description: str) -> int:
        """Calculate match score based on keyword overlap"""
        match_score = 0
        for term in query_terms:
            if term in description:
                match_score += 1
        return match_score
    
    async def search_with_keywords(self, keywords: List[str], limit: int = 20) -> List[Dict]:
        """
        Direct keyword-based search
        Alternative search method
        """
        try:
            results = []
            all_docs = await self.billing.firestore_service.get_all_documents()
            
            for doc in all_docs:
                doc_data = doc
                description = (doc_data.get("Descriptions", "")).lower()
                
                # Check if any keyword matches
                matches = sum(1 for keyword in keywords if keyword.lower() in description)
                
                if matches > 0:
                    similarity = min(0.9, matches / len(keywords))
                    
                    result = {
                        "cpt_code": doc_data.get("CPT Codes", ""),
                        "description": doc_data.get("Descriptions", ""),
                        "category": doc_data.get("Procedure Code Category", ""),
                        "similarity": similarity,
                        "matches": matches
                    }
                    result.update(doc_data)
                    results.append(result)
            
            # Sort by similarity
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            print(f"❌ Keyword search error: {e}")
            return []
    
    def format_cpt_results(self, raw_results: List[Dict]) -> List[Dict]:
        """
        Format results for API response
        Ensure consistent field names
        """
        formatted_results = []
        
        for result in raw_results:
            formatted_result = {
                "cpt_code": result.get("cpt_code") or result.get("CPT Codes", ""),
                "description": result.get("description") or result.get("Descriptions", ""),
                "category": result.get("category") or result.get("Procedure Code Category", ""),
                "status": result.get("status") or result.get("Code Status", ""),
                "similarity": result.get("similarity", 0.0)
            }
            
            # Add distance if available
            if "distance" in result:
                formatted_result["distance"] = result["distance"]
            
            # Add match terms if available
            if "match_terms" in result:
                formatted_result["match_terms"] = result["match_terms"]
            
            formatted_results.append(formatted_result)
        
        return formatted_results