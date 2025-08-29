#!/usr/bin/env python3
"""
Vertex AI Vector Search utility functions for CPT code search
"""

import json
import os
import numpy as np
from typing import List, Dict, Any, Optional
from google.cloud import aiplatform
from vertex_ai_utils import get_vertex_embeddings
from config import vertex_project, vertex_location, vertex_model, cred_path

class VertexVectorSearch:
    def __init__(self):
        """Initialize Vertex AI Vector Search client"""
        # Set up authentication
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
        
        # Load configuration
        with open('vertex_ai_config.json', 'r') as f:
            self.config = json.load(f)
        
        # Initialize Vertex AI
        aiplatform.init(
            project=self.config['project_id'],
            location=self.config['location']
        )
        
        # Initialize endpoint (will be used once deployment is complete)
        self.endpoint = None
        self.deployed_index_id = self.config.get('deployed_index_id', 'cpt_deployed_index')
        
        print(f"✅ Initialized Vertex Vector Search")
        print(f"   Project: {self.config['project_id']}")
        print(f"   Location: {self.config['location']}")
        print(f"   Deployed Index ID: {self.deployed_index_id}")

    def _get_endpoint(self):
        """Lazy load the endpoint"""
        if self.endpoint is None:
            try:
                endpoint_name = self.config['endpoint_resource_name']
                self.endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
                print(f"✅ Connected to endpoint: {self.endpoint.display_name}")
            except Exception as e:
                print(f"❌ Error connecting to endpoint: {e}")
                return None
        return self.endpoint

    def search_similar_vectors(
        self, 
        query_text: str, 
        num_neighbors: int = 20,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar CPT codes using text query
        
        Args:
            query_text: The medical procedure text to search for
            num_neighbors: Number of similar results to return
            include_metadata: Whether to include full metadata in results
            
        Returns:
            List of matching CPT codes with metadata and similarity scores
        """
        try:
            # Get the endpoint
            endpoint = self._get_endpoint()
            if not endpoint:
                return []

            print(f"🔍 Searching for: '{query_text[:60]}...'")
            
            # Generate embedding for the query text
            print("  Generating query embedding...")
            query_embeddings = get_vertex_embeddings(
                descriptions=[query_text],
                project=vertex_project,
                location=vertex_location,
                model=vertex_model,
                task_type='RETRIEVAL_QUERY',  # Use QUERY for search queries
                batch_size=1
            )
            
            if not query_embeddings or len(query_embeddings) == 0:
                print("❌ Failed to generate query embedding")
                return []
                
            query_vector = query_embeddings[0]
            print(f"  ✅ Generated {len(query_vector)}-dimensional embedding")
            
            # Perform vector search
            print(f"  Searching for {num_neighbors} nearest neighbors...")
            response = endpoint.find_neighbors(
                deployed_index_id=self.deployed_index_id,
                queries=[query_vector],
                num_neighbors=num_neighbors
            )
            
            if not response or len(response) == 0:
                print("⚠️  No results returned from vector search")
                return []
            
            # Process results
            neighbors = response[0]  # First (and only) query result
            results = []
            
            print(f"  ✅ Found {len(neighbors)} results")
            
            for i, neighbor in enumerate(neighbors):
                # Extract data from the neighbor result
                result = {
                    'id': neighbor.id,
                    'distance': float(neighbor.distance),
                    'similarity': 1.0 - float(neighbor.distance),  # Convert distance to similarity
                }
                
                # Parse the ID to get CPT code
                if neighbor.id.startswith('cpt_'):
                    result['cpt_code'] = neighbor.id[4:]  # Remove 'cpt_' prefix
                else:
                    result['cpt_code'] = neighbor.id
                
                # Add metadata if available and requested
                if include_metadata and hasattr(neighbor, 'restricts'):
                    # Extract metadata from restricts or other fields
                    # This depends on how the data was indexed
                    pass
                
                results.append(result)
            
            # Sort by similarity (highest first)
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results
            
        except Exception as e:
            print(f"❌ Error in vector search: {e}")
            print(f"   Error type: {type(e)}")
            return []

    def search_with_metadata_filter(
        self,
        query_text: str,
        category_filter: Optional[str] = None,
        num_neighbors: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search with optional category filtering
        
        Args:
            query_text: The medical procedure text to search for
            category_filter: Optional procedure category to filter by
            num_neighbors: Number of results to return
            
        Returns:
            List of filtered results
        """
        # For now, just do basic search and filter after
        # Later can be enhanced with proper metadata filtering
        results = self.search_similar_vectors(query_text, num_neighbors * 2)
        
        if category_filter:
            # Filter results by category (this would need metadata in the index)
            filtered_results = [r for r in results if r.get('category', '').lower() == category_filter.lower()]
            return filtered_results[:num_neighbors]
        
        return results[:num_neighbors]

    def get_cpt_details_from_firestore(self, cpt_codes: List[str]) -> Dict[str, Dict]:
        """
        Get full CPT code details from Firestore for the matched codes
        
        Args:
            cpt_codes: List of CPT codes to get details for
            
        Returns:
            Dictionary mapping CPT codes to their full details
        """
        try:
            from firebase_utils import init_firestore
            from config import collection_name
            
            db = init_firestore(cred_path)
            if not db:
                return {}
            
            collection_ref = db.collection(collection_name)
            details = {}
            
            # Get details for each CPT code
            for cpt_code in cpt_codes:
                try:
                    # Query by CPT code
                    docs = list(collection_ref.where('CPT Codes', '==', cpt_code).limit(1).stream())
                    
                    if docs:
                        doc_data = docs[0].to_dict()
                        details[cpt_code] = {
                            'cpt_code': doc_data.get('CPT Codes', cpt_code),
                            'description': doc_data.get('Descriptions', ''),
                            'category': doc_data.get('Procedure Code Category', ''),
                            'status': doc_data.get('Code Status', ''),
                            'firestore_id': docs[0].id
                        }
                except Exception as e:
                    print(f"⚠️  Error getting details for CPT {cpt_code}: {e}")
                    continue
            
            return details
            
        except Exception as e:
            print(f"❌ Error getting CPT details from Firestore: {e}")
            return {}

    def search_cpt_codes(self, query_text: str, num_results: int = 20) -> List[Dict[str, Any]]:
        """
        Complete CPT code search with full details
        
        Args:
            query_text: Medical procedure description to search for
            num_results: Number of results to return
            
        Returns:
            List of CPT codes with full details and similarity scores
        """
        try:
            print(f"🔍 Complete CPT search for: '{query_text[:60]}...'")
            
            # Step 1: Vector search
            vector_results = self.search_similar_vectors(query_text, num_results)
            
            if not vector_results:
                print("⚠️  No vector search results found")
                return []
            
            # Step 2: Get CPT codes from results
            cpt_codes = [result['cpt_code'] for result in vector_results]
            print(f"  📋 Getting details for {len(cpt_codes)} CPT codes...")
            
            # Step 3: Get full details from Firestore
            cpt_details = self.get_cpt_details_from_firestore(cpt_codes)
            
            # Step 4: Combine vector results with full details
            final_results = []
            for vector_result in vector_results:
                cpt_code = vector_result['cpt_code']
                
                if cpt_code in cpt_details:
                    combined_result = {
                        **cpt_details[cpt_code],  # Full CPT details
                        'similarity': vector_result['similarity'],
                        'distance': vector_result['distance'],
                        'search_id': vector_result['id']
                    }
                    final_results.append(combined_result)
                else:
                    # Fallback if details not found
                    final_results.append({
                        'cpt_code': cpt_code,
                        'description': 'Details not found',
                        'similarity': vector_result['similarity'],
                        'distance': vector_result['distance'],
                        'search_id': vector_result['id']
                    })
            
            print(f"  ✅ Retrieved complete details for {len(final_results)} results")
            return final_results
            
        except Exception as e:
            print(f"❌ Error in complete CPT search: {e}")
            return []

    def check_deployment_status(self) -> Dict[str, Any]:
        """Check if the index deployment is ready"""
        try:
            endpoint = self._get_endpoint()
            if not endpoint:
                return {"status": "error", "message": "Cannot connect to endpoint"}
            
            # Try a simple search to test if deployment is ready
            try:
                test_vector = [0.1] * 768  # Simple test vector
                response = endpoint.find_neighbors(
                    deployed_index_id=self.deployed_index_id,
                    queries=[test_vector],
                    num_neighbors=1
                )
                
                return {
                    "status": "ready", 
                    "message": "Vector search is operational",
                    "endpoint": endpoint.display_name,
                    "deployed_index_id": self.deployed_index_id
                }
                
            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    return {
                        "status": "deploying", 
                        "message": "Index is still deploying (30-45 minutes typical)",
                        "error": error_msg
                    }
                else:
                    return {
                        "status": "error", 
                        "message": f"Deployment error: {error_msg}",
                        "error": error_msg
                    }
                    
        except Exception as e:
            return {"status": "error", "message": f"Status check failed: {e}"}


# Convenience functions for easy usage
def search_cpt_codes(query_text: str, num_results: int = 20) -> List[Dict[str, Any]]:
    """Convenience function for CPT code search"""
    searcher = VertexVectorSearch()
    return searcher.search_cpt_codes(query_text, num_results)

def check_vertex_status() -> Dict[str, Any]:
    """Convenience function to check deployment status"""
    searcher = VertexVectorSearch()
    return searcher.check_deployment_status()


if __name__ == '__main__':
    # Test the search functionality
    print("=" * 80)
    print("VERTEX AI VECTOR SEARCH TEST")
    print("=" * 80)
    
    # Check status
    status = check_vertex_status()
    print(f"📊 Deployment Status: {status}")
    
    if status['status'] == 'ready':
        # Test search
        test_query = "knee surgery arthroscopy"
        print(f"\n🔍 Testing search with: '{test_query}'")
        
        results = search_cpt_codes(test_query, num_results=5)
        
        print(f"\n📋 Results ({len(results)} found):")
        for i, result in enumerate(results, 1):
            print(f"  {i}. CPT {result['cpt_code']} (similarity: {result['similarity']:.4f})")
            print(f"     {result['description'][:100]}...")
            
    elif status['status'] == 'deploying':
        print(f"\n⏱️  {status['message']}")
        print(f"   Try again in 15-20 minutes")
    else:
        print(f"\n❌ {status['message']}")