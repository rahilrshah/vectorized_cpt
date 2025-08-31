"""
Medical Text Processing Service
Wraps existing AI processing functionality for microservice architecture
"""

import time
import base64
import io
from typing import Dict, Any
import sys
import os

# Add parent directories to path to import existing modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from app.config import BillingConfig
from app.services.ai_processor import AIProcessorService
from app.services.pdf_processor import PDFProcessorService


class MedicalTextProcessingService:
    """
    Medical text processing service that preserves existing functionality
    Surgically extracted from app.services.ai_processor
    """
    
    def __init__(self):
        """Initialize service with existing configuration"""
        print("🤖 Initializing Medical Text Processing Service...")
        
        # Use existing configuration system
        self.config = BillingConfig()
        
        # Create minimal billing-like object for service compatibility
        self._mock_billing = type('MockBilling', (), {
            'config': self.config,
            'getConfig': lambda: self.config
        })()
        
        # Initialize existing services with exact same logic
        self.ai_processor = AIProcessorService(self._mock_billing)
        self.pdf_processor = PDFProcessorService(self._mock_billing)
        
        print("✅ Medical Text Processing Service Ready")
    
    async def extract_procedures_from_text(self, text: str, extract_structured: bool = False) -> Dict[str, Any]:
        """
        Extract medical procedures from text using existing AI logic
        Preserves exact functionality from app.services.ai_processor
        """
        start_time = time.time()
        
        try:
            # Use existing extract_procedures_with_gemini method unchanged
            extracted_procedures = await self.ai_processor.extract_procedures_with_gemini(text)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "extracted_procedures": extracted_procedures,
                "processing_time_ms": processing_time_ms,
                "success": True,
                "original_text_length": len(text),
                "service_version": "medical_processor_v1"
            }
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"❌ Medical text processing error: {e}")
            
            return {
                "extracted_procedures": "",
                "processing_time_ms": processing_time_ms,
                "success": False,
                "error": str(e)
            }
    
    async def process_pdf_document(self, pdf_base64: str, extract_structured: bool = False) -> Dict[str, Any]:
        """
        Process PDF document using existing PDF processing logic
        Preserves exact functionality from app.services.pdf_processor
        """
        start_time = time.time()
        
        try:
            # Decode base64 PDF
            pdf_bytes = base64.b64decode(pdf_base64)
            pdf_file = io.BytesIO(pdf_bytes)
            
            # Use existing PDF processing method unchanged
            extracted_text = await self.pdf_processor.extract_text_from_pdf(pdf_file)
            
            # Process extracted text with AI
            if extracted_text.strip():
                ai_result = await self.extract_procedures_from_text(extracted_text, extract_structured)
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                return {
                    "extracted_procedures": ai_result["extracted_procedures"],
                    "extracted_text": extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else ""),
                    "processing_time_ms": processing_time_ms,
                    "success": True,
                    "pdf_pages": "auto-detected",
                    "service_version": "medical_processor_v1"
                }
            else:
                raise Exception("Could not extract text from PDF")
                
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"❌ PDF processing error: {e}")
            
            return {
                "extracted_procedures": "",
                "processing_time_ms": processing_time_ms,
                "success": False,
                "error": str(e)
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            # Test AI processor functionality
            test_result = await self.ai_processor.extract_procedures_with_gemini("Test medical note")
            ai_healthy = bool(test_result)
            
            return {
                "status": "healthy" if ai_healthy else "unhealthy",
                "service_name": "medical_text_processor",
                "dependencies": {
                    "vertex_ai": "connected" if ai_healthy else "disconnected",
                    "configuration": "loaded",
                    "gemini_model": self.config.GENERATIVE_MODEL,
                    "embedding_model": self.config.EMBEDDING_MODEL
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service_name": "medical_text_processor",
                "dependencies": {
                    "vertex_ai": "error",
                    "error": str(e)
                }
            }