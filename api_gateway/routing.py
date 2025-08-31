"""
API Gateway Service Routing
Routes requests to appropriate microservices
"""

import asyncio
import httpx
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from .models import ServiceName, UnifiedRequest, UnifiedResponse


class ServiceRouter:
    """
    Routes API requests to appropriate microservices
    Handles service discovery, load balancing, and error handling
    """
    
    def __init__(self):
        """Initialize service router with service endpoints"""
        # Service endpoint configuration
        self.service_endpoints = {
            ServiceName.medical_processor: "http://localhost:8001",
            ServiceName.cpt_search: "http://localhost:8002", 
            ServiceName.medical_coding: "http://localhost:8003"
        }
        
        # Service health status cache
        self.service_health = {}
        self.health_check_interval = 60  # seconds
        self.last_health_check = {}
    
    async def route_request(
        self, 
        service: ServiceName, 
        endpoint: str, 
        request_data: Dict[str, Any],
        api_key_id: str,
        timeout: int = 30
    ) -> UnifiedResponse:
        """
        Route request to specified microservice
        """
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Get service endpoint
            service_url = self.service_endpoints.get(service)
            if not service_url:
                raise Exception(f"Unknown service: {service}")
            
            # Check service health
            if not await self._is_service_healthy(service):
                raise Exception(f"Service {service} is unhealthy")
            
            # Make request to microservice
            full_url = f"{service_url}{endpoint}"
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(full_url, json=request_data)
                response.raise_for_status()
                
                response_data = response.json()
                processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
                
                return UnifiedResponse(
                    success=True,
                    data=response_data,
                    processing_time_ms=processing_time,
                    service_used=service.value,
                    api_key_id=api_key_id,
                    request_id=request_id,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return UnifiedResponse(
                success=False,
                error=str(e),
                processing_time_ms=processing_time,
                service_used=service.value,
                api_key_id=api_key_id,
                request_id=request_id,
                timestamp=datetime.now()
            )
    
    async def execute_complete_workflow(
        self, 
        text: str, 
        api_key_id: str,
        max_results: int = 20,
        include_comprehensive: bool = True,
        pdf_base64: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute complete medical coding workflow across all services
        Preserves exact functionality of original Billing.process_medical_note
        """
        workflow_start = datetime.now()
        request_id = str(uuid.uuid4())
        services_used = []
        
        try:
            # Step 1: Medical text processing (extract procedures)
            if pdf_base64:
                # Process PDF first
                pdf_request = {"pdf_base64": pdf_base64, "extract_structured": False}
                pdf_response = await self.route_request(
                    ServiceName.medical_processor, 
                    "/api/v1/medical/extract-pdf",
                    pdf_request,
                    api_key_id
                )
                
                if not pdf_response.success:
                    raise Exception(f"PDF processing failed: {pdf_response.error}")
                
                # Extract text from PDF response
                text = pdf_response.data.get("extracted_text", text)
                services_used.append("medical_processor_pdf")
            
            # Extract medical procedures from text
            extract_request = {"text": text, "extract_structured": False}
            extract_response = await self.route_request(
                ServiceName.medical_processor,
                "/api/v1/medical/extract",
                extract_request,
                api_key_id
            )
            
            if not extract_response.success:
                raise Exception(f"Medical text processing failed: {extract_response.error}")
            
            extracted_procedures = extract_response.data.get("extracted_procedures", "")
            services_used.append("medical_processor")
            
            # Step 2: CPT code search
            search_request = {
                "procedures": extracted_procedures,
                "max_results": max_results,
                "similarity_threshold": 0.6,
                "include_embeddings": False
            }
            
            search_response = await self.route_request(
                ServiceName.cpt_search,
                "/api/v1/cpt/search",
                search_request,
                api_key_id
            )
            
            if not search_response.success:
                raise Exception(f"CPT search failed: {search_response.error}")
            
            cpt_results = search_response.data.get("results", [])
            services_used.append("cpt_search")
            
            # Step 3: Comprehensive medical coding (if requested)
            comprehensive_codes = None
            if include_comprehensive and cpt_results:
                coding_request = {
                    "primary_codes": cpt_results,
                    "medical_text": extracted_procedures,
                    "original_note": text,
                    "include_diagnostics": True,
                    "include_anesthesia": True,
                    "include_modifiers": True
                }
                
                coding_response = await self.route_request(
                    ServiceName.medical_coding,
                    "/api/v1/medical/code-complete",
                    coding_request,
                    api_key_id
                )
                
                if coding_response.success:
                    comprehensive_codes = coding_response.data
                    services_used.append("medical_coding")
            
            # Calculate total processing time
            total_time = int((datetime.now() - workflow_start).total_seconds() * 1000)
            
            return {
                "step1_extracted_text": text[:1000] + ("..." if len(text) > 1000 else ""),
                "step2_extracted_procedures": extracted_procedures,
                "step3_cpt_results": cpt_results,
                "step4_comprehensive_codes": comprehensive_codes,
                "total_processing_time_ms": total_time,
                "services_used": services_used,
                "success": True,
                "api_key_id": api_key_id,
                "request_id": request_id,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            total_time = int((datetime.now() - workflow_start).total_seconds() * 1000)
            
            return {
                "step1_extracted_text": "",
                "step2_extracted_procedures": "",
                "step3_cpt_results": [],
                "step4_comprehensive_codes": None,
                "total_processing_time_ms": total_time,
                "services_used": services_used,
                "success": False,
                "error": str(e),
                "api_key_id": api_key_id,
                "request_id": request_id,
                "timestamp": datetime.now()
            }
    
    async def _is_service_healthy(self, service: ServiceName) -> bool:
        """Check if a service is healthy (cached for performance)"""
        now = datetime.now()
        last_check = self.last_health_check.get(service)
        
        # Use cached result if recent
        if last_check and (now - last_check).seconds < self.health_check_interval:
            return self.service_health.get(service, False)
        
        # Perform health check
        try:
            service_url = self.service_endpoints.get(service)
            if not service_url:
                return False
            
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{service_url}/health")
                is_healthy = response.status_code == 200
                
                self.service_health[service] = is_healthy
                self.last_health_check[service] = now
                
                return is_healthy
                
        except Exception:
            self.service_health[service] = False
            self.last_health_check[service] = now
            return False
    
    async def get_all_services_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all services"""
        health_status = {}
        
        for service in ServiceName:
            try:
                service_url = self.service_endpoints.get(service)
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"{service_url}/health")
                    if response.status_code == 200:
                        health_data = response.json()
                        health_status[service.value] = {
                            "status": "healthy",
                            "details": health_data,
                            "endpoint": service_url
                        }
                    else:
                        health_status[service.value] = {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status_code}",
                            "endpoint": service_url
                        }
                        
            except Exception as e:
                health_status[service.value] = {
                    "status": "unreachable",
                    "error": str(e),
                    "endpoint": service_url
                }
        
        return health_status


# Global service router instance
service_router = ServiceRouter()