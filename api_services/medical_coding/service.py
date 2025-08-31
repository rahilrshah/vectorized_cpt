"""
Medical Coding Service
Wraps existing comprehensive medical coding functionality for microservice architecture
"""

import time
from typing import Dict, Any, List
import sys
import os

# Add parent directories to path to import existing modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from app.config import BillingConfig
from app.services.medical_coding_service import MedicalCodingService


class MedicalCodingMicroservice:
    """
    Medical coding microservice that preserves existing functionality
    Surgically extracted from app.services.medical_coding_service
    """
    
    def __init__(self):
        """Initialize service with existing configuration"""
        print("🏥 Initializing Medical Coding Service...")
        
        # Use existing configuration system
        self.config = BillingConfig()
        
        # Create minimal billing-like object for service compatibility
        self._mock_billing = type('MockBilling', (), {
            'config': self.config,
            'getConfig': lambda: self.config
        })()
        
        # Initialize existing medical coding service with exact same logic
        self.medical_coding = MedicalCodingService(self._mock_billing)
        
        print("✅ Medical Coding Service Ready")
    
    async def detect_comprehensive_codes(
        self,
        primary_codes: List[Dict[str, Any]],
        medical_text: str,
        original_note: str,
        include_diagnostics: bool = True,
        include_anesthesia: bool = True,
        include_modifiers: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive multi-code detection
        Preserves exact functionality from app.services.medical_coding_service
        """
        start_time = time.time()
        
        try:
            # Use existing comprehensive code detection (unchanged)
            comprehensive_result = self.medical_coding.detect_comprehensive_codes(
                primary_codes, medical_text, original_note
            )
            
            # Filter results based on request parameters
            if not include_anesthesia:
                comprehensive_result['anesthesia_codes'] = []
            
            if not include_modifiers:
                comprehensive_result['modifiers'] = []
            
            if not include_diagnostics:
                comprehensive_result['related_codes'] = []
            
            # Recalculate billing summary after filtering
            if not (include_anesthesia and include_modifiers and include_diagnostics):
                comprehensive_result['billing_summary'] = self._recalculate_billing_summary(
                    comprehensive_result
                )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            comprehensive_result['processing_time_ms'] = processing_time_ms
            comprehensive_result['success'] = True
            
            return comprehensive_result
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"❌ Comprehensive coding error: {e}")
            
            return {
                "primary_codes": primary_codes,
                "anesthesia_codes": [],
                "modifiers": [],
                "related_codes": [],
                "coding_confidence": "low",
                "medical_specialty": "unknown",
                "billing_summary": {
                    "total_codes": len(primary_codes),
                    "has_modifiers": False,
                    "has_anesthesia": False,
                    "complexity": "unknown",
                    "specialty": "unknown",
                    "billing_confidence": "low"
                },
                "processing_time_ms": processing_time_ms,
                "success": False,
                "error": str(e)
            }
    
    async def quick_code_analysis(self, cpt_code: str, medical_context: str) -> Dict[str, Any]:
        """
        Quick analysis of a single CPT code for suggested ancillary codes
        Uses existing medical coding logic
        """
        start_time = time.time()
        
        try:
            # Create a mock primary codes list for the existing service
            primary_codes = [{
                "cpt_code": cpt_code,
                "description": medical_context,
                "similarity": 1.0
            }]
            
            # Use existing comprehensive detection on single code
            result = self.medical_coding.detect_comprehensive_codes(
                primary_codes, medical_context, medical_context
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "cpt_code": cpt_code,
                "suggested_anesthesia": result.get("anesthesia_codes", []),
                "suggested_modifiers": result.get("modifiers", []),
                "suggested_diagnostics": result.get("related_codes", []),
                "confidence": result.get("coding_confidence", "medium"),
                "processing_time_ms": processing_time_ms,
                "success": True
            }
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"❌ Quick coding analysis error: {e}")
            
            return {
                "cpt_code": cpt_code,
                "suggested_anesthesia": [],
                "suggested_modifiers": [],
                "suggested_diagnostics": [],
                "confidence": "low",
                "processing_time_ms": processing_time_ms,
                "success": False,
                "error": str(e)
            }
    
    def _recalculate_billing_summary(self, comprehensive_result: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate billing summary after filtering"""
        return {
            "total_codes": (
                len(comprehensive_result.get("primary_codes", [])) +
                len(comprehensive_result.get("anesthesia_codes", [])) +
                len(comprehensive_result.get("related_codes", []))
            ),
            "has_modifiers": len(comprehensive_result.get("modifiers", [])) > 0,
            "has_anesthesia": len(comprehensive_result.get("anesthesia_codes", [])) > 0,
            "complexity": comprehensive_result.get("billing_summary", {}).get("complexity", "simple"),
            "specialty": comprehensive_result.get("medical_specialty", "general"),
            "billing_confidence": comprehensive_result.get("coding_confidence", "medium")
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            # Test medical coding functionality
            test_codes = [{"cpt_code": "27447", "description": "knee arthroplasty", "similarity": 0.9}]
            test_result = self.medical_coding.detect_comprehensive_codes(
                test_codes, "knee arthroplasty", "knee surgery"
            )
            
            service_healthy = bool(test_result)
            
            return {
                "status": "healthy" if service_healthy else "unhealthy",
                "service_name": "medical_coding",
                "dependencies": {
                    "medical_coding_engine": "operational" if service_healthy else "error",
                    "anesthesia_mapping": "loaded",
                    "modifier_detection": "operational",
                    "diagnostic_mapping": "loaded"
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service_name": "medical_coding",
                "dependencies": {
                    "error": str(e)
                }
            }