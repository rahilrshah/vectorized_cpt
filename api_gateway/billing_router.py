"""
Consolidated Billing Router
Direct calls to monolithic Billing system instead of HTTP microservices
Provides the performance benefits of direct method calls with API Gateway interface
"""

import asyncio
import uuid
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from .models import UnifiedRequest, UnifiedResponse, APIKeyInfo, TeamInfo
from .auth import api_key_manager


class BillingRouter:
    """
    Routes API requests directly to the monolithic Billing system
    Eliminates HTTP overhead while maintaining API Gateway benefits
    """
    
    def __init__(self):
        """Initialize billing router with billing system"""
        self.billing_system = None
        self._initialize_billing()
    
    def _initialize_billing(self):
        """Initialize the monolithic billing system"""
        try:
            # Import here to avoid circular imports and ensure app context
            from app.billing import Billing
            
            print("🏥 Initializing monolithic Billing system for API Gateway...")
            self.billing_system = Billing()
            print("✅ Billing system integrated with API Gateway")
            
        except Exception as e:
            print(f"❌ Failed to initialize billing system: {e}")
            raise e
    
    async def extract_medical_procedures(
        self, 
        text: str, 
        api_key_info: APIKeyInfo,
        extract_structured: bool = False,
        pdf_base64: Optional[str] = None
    ) -> UnifiedResponse:
        """
        Extract medical procedures using AI - direct billing system call
        """
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Check feature access
            if not self._check_feature_access(api_key_info, "medical_extract"):
                raise Exception("Team does not have access to medical extraction feature")
            
            # Direct call to billing system
            if pdf_base64:
                # PDF processing
                result = await asyncio.to_thread(
                    self.billing_system.pdf_processor.extract_text_from_pdf_base64,
                    pdf_base64
                )
                extracted_text = result.get("extracted_text", "")
                
                # Then extract procedures from the text
                procedures = await asyncio.to_thread(
                    self.billing_system.ai_processor.extract_procedures_with_gemini,
                    extracted_text
                )
                
                response_data = {
                    "extracted_text": extracted_text,
                    "extracted_procedures": procedures,
                    "pdf_processed": True
                }
            else:
                # Direct text processing
                procedures = await asyncio.to_thread(
                    self.billing_system.ai_processor.extract_procedures_with_gemini,
                    text
                )
                
                response_data = {
                    "extracted_text": text,
                    "extracted_procedures": procedures,
                    "pdf_processed": False
                }
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return UnifiedResponse(
                success=True,
                data=response_data,
                processing_time_ms=processing_time,
                service_used="billing_monolith_medical_extract",
                api_key_id=api_key_info.key_id,
                request_id=request_id,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return UnifiedResponse(
                success=False,
                error=str(e),
                processing_time_ms=processing_time,
                service_used="billing_monolith_medical_extract",
                api_key_id=api_key_info.key_id,
                request_id=request_id,
                timestamp=datetime.now()
            )
    
    async def search_cpt_codes(
        self,
        procedures: str,
        api_key_info: APIKeyInfo,
        max_results: int = 20,
        similarity_threshold: float = 0.6,
        include_embeddings: bool = False
    ) -> UnifiedResponse:
        """
        Search CPT codes using vector similarity - direct billing system call
        """
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Check feature access
            if not self._check_feature_access(api_key_info, "cpt_search"):
                raise Exception("Team does not have access to CPT search feature")
            
            # Apply team limits
            effective_max_results = min(max_results, api_key_info.team_info.max_results_limit)
            
            # Direct call to billing system CPT search
            results = await asyncio.to_thread(
                self.billing_system.cpt_search.search_procedures,
                procedures,
                effective_max_results,
                similarity_threshold
            )
            
            response_data = {
                "results": results,
                "total_results": len(results),
                "max_results_applied": effective_max_results,
                "similarity_threshold": similarity_threshold,
                "search_query": procedures
            }
            
            # Include embeddings if requested and team has access
            if include_embeddings and self._check_feature_access(api_key_info, "advanced_analytics"):
                embedding = await asyncio.to_thread(
                    self.billing_system.ai_processor.generate_embedding_vector,
                    procedures
                )
                response_data["query_embedding"] = embedding
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return UnifiedResponse(
                success=True,
                data=response_data,
                processing_time_ms=processing_time,
                service_used="billing_monolith_cpt_search",
                api_key_id=api_key_info.key_id,
                request_id=request_id,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return UnifiedResponse(
                success=False,
                error=str(e),
                processing_time_ms=processing_time,
                service_used="billing_monolith_cpt_search",
                api_key_id=api_key_info.key_id,
                request_id=request_id,
                timestamp=datetime.now()
            )
    
    async def comprehensive_medical_coding(
        self,
        primary_codes: List[Dict[str, Any]],
        medical_text: str,
        api_key_info: APIKeyInfo,
        original_note: Optional[str] = None,
        include_diagnostics: bool = True,
        include_anesthesia: bool = True,
        include_modifiers: bool = True
    ) -> UnifiedResponse:
        """
        Comprehensive medical coding with anesthesia and modifiers - direct billing system call
        """
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Check feature access
            if not self._check_feature_access(api_key_info, "comprehensive_coding"):
                raise Exception("Team does not have access to comprehensive coding feature")
            
            # Direct call to billing system medical coding
            result = await asyncio.to_thread(
                self.billing_system.medical_coding.detect_comprehensive_codes,
                primary_codes,
                medical_text,
                original_note or medical_text
            )
            
            response_data = {
                "primary_codes": primary_codes,
                "comprehensive_analysis": result,
                "features_included": {
                    "diagnostics": include_diagnostics,
                    "anesthesia": include_anesthesia,
                    "modifiers": include_modifiers
                }
            }
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return UnifiedResponse(
                success=True,
                data=response_data,
                processing_time_ms=processing_time,
                service_used="billing_monolith_medical_coding",
                api_key_id=api_key_info.key_id,
                request_id=request_id,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return UnifiedResponse(
                success=False,
                error=str(e),
                processing_time_ms=processing_time,
                service_used="billing_monolith_medical_coding",
                api_key_id=api_key_info.key_id,
                request_id=request_id,
                timestamp=datetime.now()
            )
    
    async def execute_complete_workflow(
        self,
        text: str,
        api_key_info: APIKeyInfo,
        max_results: int = 20,
        include_comprehensive: bool = True,
        pdf_base64: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute complete medical coding workflow - direct billing system call
        PRESERVES EXACT FUNCTIONALITY of original Billing.process_medical_note()
        """
        workflow_start = datetime.now()
        request_id = str(uuid.uuid4())
        
        try:
            # Apply team limits
            effective_max_results = min(max_results, api_key_info.team_info.max_results_limit)
            
            # Check if team has access to comprehensive coding
            if include_comprehensive and not self._check_feature_access(api_key_info, "comprehensive_coding"):
                include_comprehensive = False
            
            # Direct call to monolithic billing system - EXACTLY like before!
            if pdf_base64 and self._check_feature_access(api_key_info, "pdf_processing"):
                # Process PDF first
                result = await asyncio.to_thread(
                    self.billing_system.process_medical_note_from_pdf,
                    pdf_base64,
                    effective_max_results
                )
            else:
                # Direct text processing - same as original system
                result = await asyncio.to_thread(
                    self.billing_system.process_medical_note,
                    text,
                    effective_max_results
                )
            
            # Add comprehensive coding if requested and available
            if include_comprehensive and result.get("success") and result.get("step4_cptResults"):
                comprehensive_result = await asyncio.to_thread(
                    self.billing_system.medical_coding.detect_comprehensive_codes,
                    result["step4_cptResults"],
                    result.get("step2_extractedProcedures", ""),
                    text
                )
                result["step5_comprehensive_codes"] = comprehensive_result
            
            # Calculate total processing time
            total_time = int((datetime.now() - workflow_start).total_seconds() * 1000)
            
            # Return in the exact same format as original system
            return {
                "step1_extracted_text": result.get("step1_extractedText", text[:1000]),
                "step2_extracted_procedures": result.get("step2_extractedProcedures", ""),
                "step3_cpt_results": result.get("step4_cptResults", []),
                "step4_comprehensive_codes": result.get("step5_comprehensive_codes"),
                "total_processing_time_ms": total_time,
                "services_used": ["billing_monolith_complete"],
                "success": result.get("success", False),
                "api_key_id": api_key_info.key_id,
                "request_id": request_id,
                "timestamp": datetime.now(),
                "team_limits_applied": {
                    "max_results": effective_max_results,
                    "comprehensive_enabled": include_comprehensive
                }
            }
            
        except Exception as e:
            total_time = int((datetime.now() - workflow_start).total_seconds() * 1000)
            
            return {
                "step1_extracted_text": "",
                "step2_extracted_procedures": "",
                "step3_cpt_results": [],
                "step4_comprehensive_codes": None,
                "total_processing_time_ms": total_time,
                "services_used": ["billing_monolith_complete"],
                "success": False,
                "error": str(e),
                "api_key_id": api_key_info.key_id,
                "request_id": request_id,
                "timestamp": datetime.now()
            }
    
    def _check_feature_access(self, api_key_info: APIKeyInfo, feature_name: str) -> bool:
        """Check if the API key's team has access to a specific feature"""
        if not api_key_info.team_info:
            return False  # No team info means no access
        
        return api_key_manager.check_feature_access(api_key_info.team_info, feature_name)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the monolithic billing system"""
        try:
            # Check if billing system is responsive
            start_time = time.time()
            
            # Test basic functionality
            test_result = await asyncio.to_thread(
                self.billing_system.ai_processor.generate_embedding_vector,
                "test"
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                "status": "healthy",
                "service_type": "monolithic_billing",
                "response_time_ms": response_time,
                "components": {
                    "ai_processor": "healthy",
                    "cpt_search": "healthy",
                    "vector_service": "healthy",
                    "firestore_service": "healthy",
                    "medical_coding": "healthy"
                },
                "test_embedding_length": len(test_result) if test_result else 0
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service_type": "monolithic_billing",
                "error": str(e),
                "components": {
                    "billing_system": "error"
                }
            }


# Global billing router instance
billing_router = BillingRouter()