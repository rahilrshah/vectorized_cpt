"""
Hybrid Billing System
Can operate in either direct mode (original) or API mode (new microservices)
Preserves exact same interface while supporting both architectures
"""

import asyncio
import time
import os
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .services.cpt_search import CPTSearchService
    from .services.ai_processor import AIProcessorService
    from .services.vector_service import VectorService
    from .services.firestore_service import FirestoreService
    from .services.pdf_processor import PDFProcessorService
    from .services.medical_coding_service import MedicalCodingService
    from .config import BillingConfig


class HybridBilling:
    """
    Hybrid Billing System that can operate in two modes:
    1. Direct Mode: Uses original services directly (default)
    2. API Mode: Routes through microservices via API Gateway
    
    Maintains exact same interface as original Billing class
    """
    
    def __init__(self, use_api_mode: bool = False, api_key: Optional[str] = None, gateway_url: str = "http://localhost:8000"):
        """
        Initialize billing system
        
        Args:
            use_api_mode: If True, use API Gateway. If False, use direct services
            api_key: API key for API mode (can also be set via VECTORIZED_CPT_API_KEY env var)
            gateway_url: API Gateway URL for API mode
        """
        print(f"🏥 Initializing Hybrid Medical Billing System (mode: {'API' if use_api_mode else 'Direct'})...")
        
        self.use_api_mode = use_api_mode
        
        if use_api_mode:
            # Initialize API client for microservices
            from .api_client import CompatibilityBilling
            self.api_billing = CompatibilityBilling(api_key, gateway_url)
            self.config = self.api_billing.config
        else:
            # Initialize direct services (original architecture)
            self._init_direct_services()
        
        print("✅ Hybrid Billing System Ready")
    
    def _init_direct_services(self):
        """Initialize direct services (original architecture)"""
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
    
    def get_config(self):
        """Get configuration"""
        return self.config
    
    async def process_medical_note(self, text: str, max_results: int = 20) -> Dict:
        """
        Complete medical note processing pipeline
        Routes to API or direct services based on mode
        PRESERVES EXACT INTERFACE AND RESPONSE FORMAT
        """
        if self.use_api_mode:
            return await self.api_billing.process_medical_note(text, max_results)
        else:
            return await self._process_medical_note_direct(text, max_results)
    
    async def _process_medical_note_direct(self, text: str, max_results: int = 20) -> Dict:
        """
        Direct processing using original services
        Maintains exact original Billing.process_medical_note behavior
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
        Direct CPT code search (skip AI processing)
        Routes to API or direct services based on mode
        """
        if self.use_api_mode:
            return await self.api_billing.search_cpt_codes(query, max_results)
        else:
            return await self._search_cpt_codes_direct(query, max_results)
    
    async def _search_cpt_codes_direct(self, query: str, max_results: int = 20) -> List[Dict]:
        """Direct CPT code search using original services"""
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
        if self.use_api_mode:
            # For API mode, convert PDF to base64 and send to API
            import base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            return await self.api_billing.process_medical_note("", pdf_base64=pdf_base64)
        else:
            return await self._process_pdf_document_direct(pdf_bytes)
    
    async def _process_pdf_document_direct(self, pdf_bytes: bytes) -> Dict:
        """Direct PDF processing using original services"""
        try:
            # Extract text from PDF
            extracted_text = await self.pdf_processor.extract_text_from_pdf(pdf_bytes)
            
            if not extracted_text.strip():
                raise ValueError("No text could be extracted from PDF")
            
            # Process extracted text
            return await self._process_medical_note_direct(extracted_text)
            
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
        """Get system health status"""
        if self.use_api_mode:
            return await self.api_billing.get_system_health()
        else:
            return await self._get_system_health_direct()
    
    async def _get_system_health_direct(self) -> Dict:
        """Direct system health check using original services"""
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {},
            "version": "1.0.0"
        }

        try:
            # Check AI Processor
            health_status["services"]["ai_processor"] = await self._check_ai_processor_health()
            
            # Check Firestore
            health_status["services"]["firestore"] = await self._check_firestore_health()
            
            # Check Vertex AI
            health_status["services"]["vertex_ai"] = await self._check_vertex_ai_health()

            # Overall system status
            failed_services = [key for key, status in health_status["services"].items() if status != "operational"]
            
            if failed_services:
                health_status["status"] = "degraded"
                health_status["failed_services"] = failed_services

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status

    async def _check_ai_processor_health(self) -> str:
        """Check AI processor health"""
        try:
            result = await self.ai_processor.extract_procedures_with_gemini("Patient underwent routine checkup.")
            return "operational" if result else "degraded"
        except:
            return "failed"

    async def _check_firestore_health(self) -> str:
        """Check Firestore health"""
        try:
            stats = await self.firestore_service.get_collection_stats()
            return "operational" if stats.get("document_count", 0) > 0 else "degraded"
        except:
            return "failed"

    async def _check_vertex_ai_health(self) -> str:
        """Check Vertex AI health"""
        try:
            test_embedding = await self.ai_processor.generate_embedding_vector("test")
            return "operational" if len(test_embedding) == 768 else "degraded"
        except:
            return "failed"


# Factory function for easy instantiation
def create_billing_system(mode: str = "direct", api_key: Optional[str] = None, gateway_url: str = "http://localhost:8000") -> HybridBilling:
    """
    Create billing system with specified mode
    
    Args:
        mode: "direct" for original services, "api" for microservices
        api_key: API key for API mode
        gateway_url: Gateway URL for API mode
    
    Returns:
        HybridBilling instance
    """
    use_api_mode = mode.lower() == "api"
    return HybridBilling(use_api_mode, api_key, gateway_url)


# Environment-based auto-configuration
def create_auto_billing_system() -> HybridBilling:
    """
    Auto-create billing system based on environment variables
    
    Environment variables:
        VECTORIZED_CPT_MODE: "direct" or "api" (default: "direct")
        VECTORIZED_CPT_API_KEY: API key (required for API mode)
        VECTORIZED_CPT_GATEWAY_URL: Gateway URL (default: "http://localhost:8000")
    
    Returns:
        HybridBilling instance configured based on environment
    """
    mode = os.getenv("VECTORIZED_CPT_MODE", "direct")
    api_key = os.getenv("VECTORIZED_CPT_API_KEY")
    gateway_url = os.getenv("VECTORIZED_CPT_GATEWAY_URL", "http://localhost:8000")
    
    return create_billing_system(mode, api_key, gateway_url)


# Backward compatibility aliases
Billing = HybridBilling  # For complete backward compatibility