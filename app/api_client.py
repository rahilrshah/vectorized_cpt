"""
API Client for Vectorized CPT Services
Provides backward-compatible interface for existing Billing class
Routes calls to the new microservices architecture through API Gateway
"""

import httpx
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from .models import *


class APIClient:
    """
    API client that routes requests to the microservices through the API Gateway
    Preserves exact interface compatibility with existing Billing system
    """
    
    def __init__(self, api_key: Optional[str] = None, gateway_url: str = "http://localhost:8000"):
        """Initialize API client with authentication"""
        self.api_key = api_key or os.getenv("VECTORIZED_CPT_API_KEY")
        self.gateway_url = gateway_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if not self.api_key:
            raise ValueError("API key is required. Set VECTORIZED_CPT_API_KEY environment variable or pass api_key parameter")
    
    async def process_medical_note(
        self, 
        text: str, 
        max_results: int = 20, 
        include_comprehensive: bool = True,
        pdf_base64: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete medical coding workflow - PRESERVES EXACT FUNCTIONALITY
        This method maintains 100% backward compatibility with Billing.process_medical_note()
        """
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.gateway_url}/api/v1/process",
                headers=self.headers,
                json={
                    "text": text,
                    "max_results": max_results,
                    "include_comprehensive": include_comprehensive,
                    "pdf_base64": pdf_base64
                }
            )
            
            if response.status_code == 401:
                raise ValueError("Invalid API key")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded")
            elif response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            return response.json()
    
    async def extract_procedures_from_text(self, text: str, extract_structured: bool = False) -> Dict[str, Any]:
        """Extract medical procedures from text using AI processing"""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.gateway_url}/api/v1/medical/extract",
                headers=self.headers,
                json={
                    "text": text,
                    "extract_structured": extract_structured
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Procedure extraction failed: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get("data", {})
    
    async def search_cpt_codes(
        self, 
        procedures: str, 
        max_results: int = 20, 
        similarity_threshold: float = 0.6,
        include_embeddings: bool = False
    ) -> Dict[str, Any]:
        """Search CPT codes using vector similarity and medical context"""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.gateway_url}/api/v1/cpt/search",
                headers=self.headers,
                json={
                    "procedures": procedures,
                    "max_results": max_results,
                    "similarity_threshold": similarity_threshold,
                    "include_embeddings": include_embeddings
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"CPT search failed: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get("data", {})
    
    async def comprehensive_medical_coding(
        self,
        primary_codes: List[Dict[str, Any]],
        medical_text: str,
        original_note: str,
        include_diagnostics: bool = True,
        include_anesthesia: bool = True,
        include_modifiers: bool = True
    ) -> Dict[str, Any]:
        """Comprehensive medical coding with anesthesia, modifiers, and diagnostics"""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.gateway_url}/api/v1/medical/code-complete",
                headers=self.headers,
                json={
                    "primary_codes": primary_codes,
                    "medical_text": medical_text,
                    "original_note": original_note,
                    "include_diagnostics": include_diagnostics,
                    "include_anesthesia": include_anesthesia,
                    "include_modifiers": include_modifiers
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Medical coding failed: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get("data", {})
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all services"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.gateway_url}/health",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Health check failed: {response.status_code} - {response.text}")
            
            return response.json()
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for the API key"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.gateway_url}/api/v1/usage",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Usage stats failed: {response.status_code} - {response.text}")
            
            return response.json()


class CompatibilityBilling:
    """
    Backward-compatible Billing class that uses the new API-based architecture
    Preserves exact same interface as original Billing class
    """
    
    def __init__(self, api_key: Optional[str] = None, gateway_url: str = "http://localhost:8000"):
        """Initialize with API client"""
        self.api_client = APIClient(api_key, gateway_url)
        self.config = self._create_mock_config()
    
    def _create_mock_config(self):
        """Create mock config object for backward compatibility"""
        class MockConfig:
            PROJECT_ID = "cpt-code-vectorized-dataset"
            LOCATION = "us-central1"
            COLLECTION_NAME = "cpt_codes"
            EMBEDDING_MODEL = "textembedding-gecko@003"
            GENERATIVE_MODEL = "gemini-1.5-flash-002"
            DIMENSIONS = 768
        
        return MockConfig()
    
    def get_config(self):
        """Get configuration (mock for compatibility)"""
        return self.config
    
    async def process_medical_note(self, text: str, max_results: int = 20) -> Dict[str, Any]:
        """
        PRESERVED EXACT FUNCTIONALITY: Process medical note through complete workflow
        Maintains exact same response format as original Billing.process_medical_note()
        """
        try:
            result = await self.api_client.process_medical_note(
                text=text,
                max_results=max_results,
                include_comprehensive=True
            )
            
            # Convert API response back to original Billing format for 100% compatibility
            return {
                "step1_extracted_text": result.get("step1_extracted_text", ""),
                "step2_extracted_procedures": result.get("step2_extracted_procedures", ""),
                "step3_cpt_results": result.get("step3_cpt_results", []),
                "step4_comprehensive_codes": result.get("step4_comprehensive_codes"),
                "results": result.get("step3_cpt_results", []),  # Legacy compatibility
                "success": result.get("success", False),
                "processing_time_ms": result.get("total_processing_time_ms", 0),
                "services_used": result.get("services_used", []),
                "api_key_id": result.get("api_key_id"),
                "request_id": result.get("request_id"),
                "timestamp": result.get("timestamp")
            }
            
        except Exception as e:
            # Return error response in original format
            return {
                "step1_extracted_text": text[:1000] + ("..." if len(text) > 1000 else ""),
                "step2_extracted_procedures": "",
                "step3_cpt_results": [],
                "step4_comprehensive_codes": None,
                "results": [],
                "success": False,
                "error": str(e),
                "processing_time_ms": 0
            }
    
    async def search_cpt_codes(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Direct CPT code search (backward compatible)"""
        try:
            result = await self.api_client.search_cpt_codes(
                procedures=query,
                max_results=max_results
            )
            return result.get("results", [])
            
        except Exception as e:
            print(f"CPT search error: {e}")
            return []
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health status (backward compatible)"""
        try:
            return await self.api_client.get_health_status()
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().timestamp(),
                "services": {},
                "version": "1.0.0",
                "error": str(e)
            }


# Global instance for backward compatibility
_default_billing_instance = None


def get_billing_instance(api_key: Optional[str] = None, gateway_url: str = "http://localhost:8000") -> CompatibilityBilling:
    """Get or create default billing instance"""
    global _default_billing_instance
    
    if _default_billing_instance is None:
        _default_billing_instance = CompatibilityBilling(api_key, gateway_url)
    
    return _default_billing_instance


# Synchronous wrappers for backward compatibility
def process_medical_note_sync(text: str, max_results: int = 20, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Synchronous wrapper for backward compatibility"""
    billing = get_billing_instance(api_key)
    return asyncio.run(billing.process_medical_note(text, max_results))


def search_cpt_codes_sync(query: str, max_results: int = 20, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """Synchronous wrapper for backward compatibility"""
    billing = get_billing_instance(api_key)
    return asyncio.run(billing.search_cpt_codes(query, max_results))