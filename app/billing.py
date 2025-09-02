"""
Main Medical Billing System
Orchestrates all CPT code search and medical note processing operations
"""

import asyncio
import time
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .services.cpt_search import CPTSearchService
    from .services.ai_processor import AIProcessorService
    from .services.vector_service import VectorService
    from .services.firestore_service import FirestoreService
    from .services.pdf_processor import PDFProcessorService
    from .services.medical_coding_service import MedicalCodingService
    from .config import BillingConfig


class Billing:
    """
    Main Medical Billing System
    Orchestrates all CPT code search and medical note processing operations
    """
    
    def __init__(self):
        """Initialize all billing system components"""
        print("🏥 Initializing Medical Billing System...")
        
        # Import here to avoid circular imports
        from app.config import BillingConfig
        from app.services.cpt_search import CPTSearchService
        from app.services.ai_processor import AIProcessorService
        from app.services.vector_service import VectorService
        from app.services.firestore_service import FirestoreService
        from app.services.pdf_processor import PDFProcessorService
        from app.services.medical_coding_service import MedicalCodingService
        
        # Load configuration
        self.config = BillingConfig()
        
        # Initialize all services
        self.cpt_search: 'CPTSearchService' = CPTSearchService(self)
        self.ai_processor: 'AIProcessorService' = AIProcessorService(self)
        self.vector_service: 'VectorService' = VectorService(self)
        self.firestore_service: 'FirestoreService' = FirestoreService(self)
        self.pdf_processor: 'PDFProcessorService' = PDFProcessorService(self)
        self.medical_coding: 'MedicalCodingService' = MedicalCodingService(self)
        
        print("✅ Billing System Ready")
    
    async def process_medical_note(self, text: str, max_results: int = 20) -> Dict:
        """
        Complete medical note processing pipeline
        Replicates exact Firebase function behavior
        """
        start_time = time.time()
        
        # Initialize response structure (same as Firebase function)
        pipeline_response = {
            "step1_extractedText": text[:1000] + ("..." if len(text) > 1000 else ""),
            "step2_extractedProcedures": "",
            "step3_embeddingVector": [],
            "step4_cptResults": [],
            "results": [],
            "success": True
        }
        
        try:
            # Step 2: Extract procedures with Gemini AI
            print("🤖 Step 2: Extracting procedures with AI...")
            procedures = await self.ai_processor.extract_procedures_with_gemini(text)
            pipeline_response["step2_extractedProcedures"] = procedures
            
            # Step 3: Generate embedding vector
            print("🧮 Step 3: Generating embedding vector...")
            embedding = await self.ai_processor.generate_embedding_vector(procedures)
            pipeline_response["step3_embeddingVector"] = embedding
            
            # Step 4: Search CPT codes
            print("🔍 Step 4: Searching CPT codes...")
            primary_results = await self.cpt_search.search_with_vector(embedding, procedures)
            
            # Apply max_results limit to primary results
            if len(primary_results) > max_results:
                primary_results = primary_results[:max_results]
            
            # Step 5: Comprehensive multi-code detection (NEW ENHANCEMENT)
            print("🏥 Step 5: Multi-code detection...")
            comprehensive_codes = self.medical_coding.detect_comprehensive_codes(
                primary_results, procedures, text
            )
            
            pipeline_response["step4_cptResults"] = primary_results  # Maintain backward compatibility
            pipeline_response["results"] = primary_results           # Legacy format
            pipeline_response["comprehensive_codes"] = comprehensive_codes  # NEW: Enhanced results
            
            # Add processing time
            processing_time = int((time.time() - start_time) * 1000)
            pipeline_response["processing_time_ms"] = processing_time
            
            print(f"✅ Processing complete: {len(primary_results)} results in {processing_time}ms")
            return pipeline_response
            
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            pipeline_response["success"] = False
            pipeline_response["error"] = str(e)
            return pipeline_response
    
    async def search_cpt_codes(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Direct CPT code search (skip Gemini processing)
        For already-processed queries
        """
        try:
            # Generate embedding directly from query
            embedding = await self.ai_processor.generate_embedding_vector(query)
            
            # Search with vector
            results = await self.cpt_search.search_with_vector(embedding, query)
            
            return results[:max_results] if len(results) > max_results else results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    async def process_pdf_document(self, pdf_bytes: bytes) -> Dict:
        """
        Process PDF document and extract CPT codes
        Combines PDF processing with medical note processing
        """
        try:
            # Extract text from PDF
            extracted_text = await self.pdf_processor.extract_text_from_pdf(pdf_bytes)
            
            if not extracted_text.strip():
                raise ValueError("No text could be extracted from PDF")
            
            # Process extracted text
            return await self.process_medical_note(extracted_text)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF processing failed: {str(e)}",
                "step1_extractedText": "",
                "step2_extractedProcedures": "",
                "step3_embeddingVector": [],
                "step4_cptResults": [],
                "results": []
            }
    
    async def get_system_health(self) -> Dict:
        """
        Comprehensive system health check
        Tests all components and services
        """
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {},
            "version": "1.0.0"
        }
        
        try:
            # Check Vertex AI
            health_status["services"]["vertex_ai"] = await self._check_vertex_ai_health()
            
            # Check Firestore
            health_status["services"]["firestore"] = await self._check_firestore_health()
            
            # Check AI Processor
            health_status["services"]["ai_processor"] = await self._check_ai_processor_health()
            
            # Overall system status
            failed_services = [k for k, v in health_status["services"].items() if v != "operational"]
            if failed_services:
                health_status["status"] = "degraded"
                health_status["failed_services"] = failed_services
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    async def _check_vertex_ai_health(self) -> str:
        """Check Vertex AI service health"""
        try:
            # Test embedding generation with simple text
            test_embedding = await self.ai_processor.generate_embedding_vector("test")
            return "operational" if len(test_embedding) == 768 else "degraded"
        except:
            return "failed"
    
    async def _check_firestore_health(self) -> str:
        """Check Firestore service health"""
        try:
            stats = await self.firestore_service.get_collection_stats()
            return "operational" if stats.get("document_count", 0) > 0 else "degraded"
        except:
            return "failed"
    
    async def _check_ai_processor_health(self) -> str:
        """Check AI processor health"""
        try:
            # Test Gemini with simple medical text
            result = await self.ai_processor.extract_procedures_with_gemini("Patient underwent routine checkup.")
            return "operational" if result else "degraded"
        except:
            return "failed"