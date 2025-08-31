"""
CPT Search Service
Wraps existing CPT search functionality for microservice architecture
"""

import time
from typing import Dict, Any, List
import sys
import os

# Add parent directories to path to import existing modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from app.config import BillingConfig
from app.services.cpt_search import CPTSearchService
from app.services.ai_processor import AIProcessorService
from app.services.firestore_service import FirestoreService


class CPTSearchMicroservice:
    """
    CPT search microservice that preserves existing functionality
    Surgically extracted from app.services.cpt_search
    """
    
    def __init__(self):
        """Initialize service with existing configuration"""
        print("🔍 Initializing CPT Search Service...")
        
        # Use existing configuration system
        self.config = BillingConfig()
        
        # Create minimal billing-like object for service compatibility
        self._mock_billing = type('MockBilling', (), {
            'config': self.config,
            'getConfig': lambda: self.config,
            'getFirestoreService': lambda: self.firestore_service
        })()
        
        # Initialize existing services with exact same logic
        self.firestore_service = FirestoreService(self._mock_billing)
        self.cpt_search = CPTSearchService(self._mock_billing)
        self.ai_processor = AIProcessorService(self._mock_billing)
        
        print("✅ CPT Search Service Ready")
    
    async def search_cpt_codes(
        self, 
        procedures: str, 
        max_results: int = 20, 
        similarity_threshold: float = 0.6,
        include_embeddings: bool = False
    ) -> Dict[str, Any]:
        """
        Search CPT codes using existing search logic
        Preserves exact functionality from app.services.cpt_search
        """
        start_time = time.time()
        
        try:
            # Step 1: Generate embedding using existing AI processor
            embedding = await self.ai_processor.generate_embedding_vector(procedures)
            
            # Step 2: Search using existing CPT search service (unchanged)
            results = await self.cpt_search.search_with_vector(embedding, procedures)
            
            # Apply max_results limit
            if len(results) > max_results:
                results = results[:max_results]
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in results 
                if result.get('similarity', 0) >= similarity_threshold
            ]
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "results": filtered_results,
                "total_found": len(filtered_results),
                "processing_time_ms": processing_time_ms,
                "embedding_dimensions": len(embedding) if embedding else None,
                "search_method": "vector_similarity_with_medical_context",
                "success": True,
                "embedding": embedding if include_embeddings else None
            }
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"❌ CPT search error: {e}")
            
            return {
                "results": [],
                "total_found": 0,
                "processing_time_ms": processing_time_ms,
                "search_method": "error",
                "success": False,
                "error": str(e)
            }
    
    async def direct_keyword_search(
        self, 
        query: str, 
        max_results: int = 20, 
        similarity_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Direct keyword search using existing enhanced keyword matching
        Preserves exact functionality from existing system
        """
        start_time = time.time()
        
        try:
            # Use existing keyword search functionality
            results = await self.cpt_search.search_with_keywords([query], max_results)
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in results 
                if result.get('similarity', 0) >= similarity_threshold
            ]
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "results": filtered_results,
                "total_found": len(filtered_results),
                "processing_time_ms": processing_time_ms,
                "search_method": "keyword_matching_with_medical_filtering",
                "success": True
            }
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"❌ Keyword search error: {e}")
            
            return {
                "results": [],
                "total_found": 0,
                "processing_time_ms": processing_time_ms,
                "search_method": "error",
                "success": False,
                "error": str(e)
            }
    
    async def generate_embedding_only(self, text: str) -> Dict[str, Any]:
        """
        Generate embedding vector only
        Uses existing AI processor embedding generation
        """
        start_time = time.time()
        
        try:
            # Use existing embedding generation (unchanged)
            embedding = await self.ai_processor.generate_embedding_vector(text)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "embedding": embedding,
                "dimensions": len(embedding) if embedding else 0,
                "processing_time_ms": processing_time_ms,
                "model_used": self.config.EMBEDDING_MODEL,
                "success": True
            }
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"❌ Embedding generation error: {e}")
            
            return {
                "embedding": [],
                "dimensions": 0,
                "processing_time_ms": processing_time_ms,
                "model_used": "error",
                "success": False,
                "error": str(e)
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            # Test database connection
            sample_docs = await self.firestore_service.get_sample_documents(1)
            db_healthy = len(sample_docs) > 0
            
            # Test embedding generation
            test_embedding = await self.ai_processor.generate_embedding_vector("test")
            ai_healthy = len(test_embedding) > 0
            
            return {
                "status": "healthy" if (db_healthy and ai_healthy) else "unhealthy",
                "service_name": "cpt_search",
                "dependencies": {
                    "firestore": "connected" if db_healthy else "disconnected",
                    "vertex_ai": "connected" if ai_healthy else "disconnected",
                    "embedding_model": self.config.EMBEDDING_MODEL,
                    "database_collection": self.config.COLLECTION_NAME,
                    "vector_field": self.config.FIRESTORE_VECTOR_FIELD
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service_name": "cpt_search",
                "dependencies": {
                    "error": str(e)
                }
            }