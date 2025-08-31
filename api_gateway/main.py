"""
API Gateway Main Application
Unified entry point for all microservices with API key authentication
Preserves complete backward compatibility with original Billing system
"""

import time
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth import api_key_manager
from .routing import service_router
from .models import (
    UnifiedRequest, UnifiedResponse, CompleteWorkflowRequest, CompleteWorkflowResponse,
    HealthCheckResponse, ErrorResponse, APIKeyInfo, UsageStats
)

security = HTTPBearer()

# Global service instances
gateway_start_time = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global gateway_start_time
    
    # Startup
    print("🚀 Starting API Gateway...")
    gateway_start_time = datetime.now()
    print("✅ API Gateway ready")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down API Gateway...")


# Create FastAPI application
app = FastAPI(
    title="Vectorized CPT API Gateway",
    description="Unified API Gateway for medical coding and CPT search services with API key authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> APIKeyInfo:
    """
    Extract and validate API key from Authorization header
    Returns API key info for valid keys, raises HTTPException for invalid keys
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = credentials.credentials
    is_valid, key_info = api_key_manager.validate_api_key(api_key)
    
    if not is_valid or not key_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check rate limit
    within_limit, current_requests = api_key_manager.check_rate_limit(
        key_info.key_id, key_info.rate_limit_per_hour
    )
    
    if not within_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. {current_requests}/{key_info.rate_limit_per_hour} requests this hour",
            headers={"X-RateLimit-Limit": str(key_info.rate_limit_per_hour), "X-RateLimit-Remaining": "0"}
        )
    
    return key_info


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all exceptions"""
    error_id = str(time.time())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "GATEWAY_ERROR",
            "message": str(exc),
            "request_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "service": "api_gateway"
        }
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Gateway and all services health check
    Returns comprehensive health status of the entire system
    """
    try:
        services_status = await service_router.get_all_services_health()
        
        total_services = len(services_status)
        healthy_services = sum(1 for status in services_status.values() if status["status"] == "healthy")
        
        gateway_status = "healthy" if healthy_services == total_services else "partial"
        if healthy_services == 0:
            gateway_status = "unhealthy"
        
        return HealthCheckResponse(
            gateway_status=gateway_status,
            services_status=services_status,
            timestamp=datetime.now(),
            total_services=total_services,
            healthy_services=healthy_services
        )
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.post("/api/v1/process", response_model=CompleteWorkflowResponse)
async def process_medical_note(
    request: CompleteWorkflowRequest,
    key_info: APIKeyInfo = Depends(get_api_key)
):
    """
    Complete medical coding workflow - PRESERVES EXACT FUNCTIONALITY
    This endpoint maintains 100% backward compatibility with Billing.process_medical_note()
    
    Processes medical notes through the complete workflow:
    1. Medical text processing (extract procedures)
    2. CPT code search with similarity matching
    3. Comprehensive medical coding (anesthesia, modifiers, diagnostics)
    """
    start_time = time.time()
    
    try:
        # Execute complete workflow via service router
        result = await service_router.execute_complete_workflow(
            text=request.text,
            api_key_id=key_info.key_id,
            max_results=request.max_results,
            include_comprehensive=request.include_comprehensive,
            pdf_base64=request.pdf_base64
        )
        
        # Log usage
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            endpoint="/api/v1/process",
            service_name="complete_workflow",
            response_time_ms=processing_time,
            success=result["success"],
            error_message=result.get("error")
        )
        
        # Return unified response
        return CompleteWorkflowResponse(**result)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        
        # Log failed usage
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            endpoint="/api/v1/process",
            service_name="complete_workflow",
            response_time_ms=processing_time,
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail=f"Workflow processing failed: {str(e)}")


@app.post("/api/v1/medical/extract", response_model=UnifiedResponse)
async def extract_medical_procedures(
    request: UnifiedRequest,
    key_info: APIKeyInfo = Depends(get_api_key)
):
    """
    Extract medical procedures from text using AI processing
    Routes to Medical Text Processing microservice
    """
    start_time = time.time()
    
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="Text content is required")
        
        # Route to medical processor service
        response = await service_router.route_request(
            service="medical_processor",
            endpoint="/api/v1/medical/extract",
            request_data={
                "text": request.text,
                "extract_structured": request.extract_structured or False
            },
            api_key_id=key_info.key_id
        )
        
        # Log usage
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            endpoint="/api/v1/medical/extract",
            service_name="medical_processor",
            response_time_ms=processing_time,
            success=response.success,
            error_message=response.error
        )
        
        return response
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            endpoint="/api/v1/medical/extract",
            service_name="medical_processor",
            response_time_ms=processing_time,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Medical extraction failed: {str(e)}")


@app.post("/api/v1/cpt/search", response_model=UnifiedResponse)
async def search_cpt_codes(
    request: UnifiedRequest,
    key_info: APIKeyInfo = Depends(get_api_key)
):
    """
    Search CPT codes using vector similarity and medical context
    Routes to CPT Search microservice
    """
    start_time = time.time()
    
    try:
        if not request.procedures and not request.query:
            raise HTTPException(status_code=400, detail="Procedures or query text is required")
        
        # Route to CPT search service
        response = await service_router.route_request(
            service="cpt_search",
            endpoint="/api/v1/cpt/search",
            request_data={
                "procedures": request.procedures or request.query,
                "max_results": request.max_results or 20,
                "similarity_threshold": request.similarity_threshold or 0.6,
                "include_embeddings": request.include_embeddings or False
            },
            api_key_id=key_info.key_id
        )
        
        # Log usage
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            endpoint="/api/v1/cpt/search",
            service_name="cpt_search",
            response_time_ms=processing_time,
            success=response.success,
            error_message=response.error
        )
        
        return response
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            endpoint="/api/v1/cpt/search",
            service_name="cpt_search",
            response_time_ms=processing_time,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"CPT search failed: {str(e)}")


@app.post("/api/v1/medical/code-complete", response_model=UnifiedResponse)
async def comprehensive_medical_coding(
    request: UnifiedRequest,
    key_info: APIKeyInfo = Depends(get_api_key)
):
    """
    Comprehensive medical coding with anesthesia, modifiers, and diagnostics
    Routes to Medical Coding microservice
    """
    start_time = time.time()
    
    try:
        if not request.primary_codes:
            raise HTTPException(status_code=400, detail="Primary codes are required")
        
        # Route to medical coding service
        response = await service_router.route_request(
            service="medical_coding",
            endpoint="/api/v1/medical/code-complete",
            request_data={
                "primary_codes": request.primary_codes,
                "medical_text": request.medical_text,
                "original_note": request.original_note,
                "include_diagnostics": request.include_diagnostics or True,
                "include_anesthesia": request.include_anesthesia or True,
                "include_modifiers": request.include_modifiers or True
            },
            api_key_id=key_info.key_id
        )
        
        # Log usage
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            endpoint="/api/v1/medical/code-complete",
            service_name="medical_coding",
            response_time_ms=processing_time,
            success=response.success,
            error_message=response.error
        )
        
        return response
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            endpoint="/api/v1/medical/code-complete",
            service_name="medical_coding",
            response_time_ms=processing_time,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Medical coding failed: {str(e)}")


@app.get("/api/v1/usage", response_model=UsageStats)
async def get_usage_statistics(key_info: APIKeyInfo = Depends(get_api_key)):
    """Get usage statistics for the authenticated API key"""
    try:
        return api_key_manager.get_usage_stats(key_info.key_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve usage stats: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    uptime_seconds = (datetime.now() - gateway_start_time).total_seconds() if gateway_start_time else 0
    
    return {
        "service": "Vectorized CPT API Gateway",
        "version": "1.0.0",
        "status": "running",
        "uptime_seconds": uptime_seconds,
        "authentication": "API key required (Bearer token)",
        "endpoints": {
            "primary_workflow": "/api/v1/process",
            "medical_extraction": "/api/v1/medical/extract",
            "cpt_search": "/api/v1/cpt/search", 
            "medical_coding": "/api/v1/medical/code-complete",
            "usage_stats": "/api/v1/usage",
            "health_check": "/health"
        },
        "microservices": [
            {"name": "medical_processor", "port": 8001},
            {"name": "cpt_search", "port": 8002},
            {"name": "medical_coding", "port": 8003}
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)