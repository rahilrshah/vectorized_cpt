"""
API Gateway Main Application
Unified entry point for all microservices with API key authentication
Preserves complete backward compatibility with original Billing system
"""

import time
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles

from .auth import api_key_manager
from .billing_router import billing_router
from .models import (
    UnifiedRequest, UnifiedResponse, CompleteWorkflowRequest, CompleteWorkflowResponse,
    HealthCheckResponse, ErrorResponse, APIKeyInfo, UsageStats, TeamUsageStats,
    CreateTeamRequest, CreateAPIKeyRequest, CreateAPIKeyResponse, TeamInfo, FeatureFlag
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

# Mount static files
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


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
    Gateway and monolithic billing system health check
    Returns comprehensive health status of the system
    """
    try:
        # Get health status from monolithic billing system
        billing_health = await billing_router.get_health_status()
        
        services_status = {
            "billing_monolith": billing_health,
            "api_gateway": {
                "status": "healthy",
                "service_type": "api_gateway",
                "uptime_seconds": (datetime.now() - gateway_start_time).total_seconds() if gateway_start_time else 0
            }
        }
        
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
    Now uses direct monolithic billing system calls for optimal performance
    
    Processes medical notes through the complete workflow:
    1. Medical text processing (extract procedures)
    2. CPT code search with similarity matching  
    3. Comprehensive medical coding (anesthesia, modifiers, diagnostics)
    """
    start_time = time.time()
    
    try:
        # Execute complete workflow via direct billing system
        result = await billing_router.execute_complete_workflow(
            text=request.text,
            api_key_info=key_info,
            max_results=request.max_results or 20,
            include_comprehensive=request.include_comprehensive,
            pdf_base64=request.pdf_base64
        )
        
        # Log usage with team information
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            team_id=key_info.team_id,
            endpoint="/api/v1/process",
            service_name="complete_workflow_monolith",
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
            team_id=key_info.team_id,
            endpoint="/api/v1/process",
            service_name="complete_workflow_monolith",
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
    Now uses direct monolithic billing system calls
    """
    start_time = time.time()
    
    try:
        if not request.text and not request.pdf_base64:
            raise HTTPException(status_code=400, detail="Text content or PDF is required")
        
        # Direct call to monolithic billing system
        response = await billing_router.extract_medical_procedures(
            text=request.text or "",
            api_key_info=key_info,
            extract_structured=request.extract_structured or False,
            pdf_base64=request.pdf_base64
        )
        
        # Log usage with team information
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            team_id=key_info.team_id,
            endpoint="/api/v1/medical/extract",
            service_name="medical_extract_monolith",
            response_time_ms=processing_time,
            success=response.success,
            error_message=response.error
        )
        
        return response
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            team_id=key_info.team_id,
            endpoint="/api/v1/medical/extract",
            service_name="medical_extract_monolith",
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
    Now uses direct monolithic billing system calls
    """
    start_time = time.time()
    
    try:
        if not request.procedures and not request.query:
            raise HTTPException(status_code=400, detail="Procedures or query text is required")
        
        # Direct call to monolithic billing system
        response = await billing_router.search_cpt_codes(
            procedures=request.procedures or request.query,
            api_key_info=key_info,
            max_results=request.max_results or 20,
            similarity_threshold=request.similarity_threshold or 0.6,
            include_embeddings=request.include_embeddings or False
        )
        
        # Log usage with team information
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            team_id=key_info.team_id,
            endpoint="/api/v1/cpt/search",
            service_name="cpt_search_monolith",
            response_time_ms=processing_time,
            success=response.success,
            error_message=response.error
        )
        
        return response
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            team_id=key_info.team_id,
            endpoint="/api/v1/cpt/search",
            service_name="cpt_search_monolith",
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
    Now uses direct monolithic billing system calls
    """
    start_time = time.time()
    
    try:
        if not request.primary_codes:
            raise HTTPException(status_code=400, detail="Primary codes are required")
        
        # Direct call to monolithic billing system
        response = await billing_router.comprehensive_medical_coding(
            primary_codes=request.primary_codes,
            medical_text=request.medical_text or "",
            api_key_info=key_info,
            original_note=request.original_note,
            include_diagnostics=request.include_diagnostics or True,
            include_anesthesia=request.include_anesthesia or True,
            include_modifiers=request.include_modifiers or True
        )
        
        # Log usage with team information
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            team_id=key_info.team_id,
            endpoint="/api/v1/medical/code-complete",
            service_name="medical_coding_monolith",
            response_time_ms=processing_time,
            success=response.success,
            error_message=response.error
        )
        
        return response
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            team_id=key_info.team_id,
            endpoint="/api/v1/medical/code-complete",
            service_name="medical_coding_monolith",
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


@app.get("/", response_class=HTMLResponse)
async def web_interface():
    """Serve the web testing interface"""
    try:
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
        html_file = os.path.join(static_dir, "web_tester.html")
        
        if os.path.exists(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return HTMLResponse("""
            <html><body>
                <h1>Vectorized CPT API Gateway</h1>
                <p>Web interface not found. Please ensure static files are properly deployed.</p>
                <p><a href="/api/info">API Information</a></p>
            </body></html>
            """)
    except Exception as e:
        return HTMLResponse(f"""
        <html><body>
            <h1>Vectorized CPT API Gateway</h1>
            <p>Error loading web interface: {str(e)}</p>
            <p><a href="/api/info">API Information</a></p>
        </body></html>
        """)

@app.get("/api/info")
async def api_info():
    """API information endpoint (JSON)"""
    uptime_seconds = (datetime.now() - gateway_start_time).total_seconds() if gateway_start_time else 0
    
    return {
        "service": "Vectorized CPT API Gateway",
        "version": "2.0.0",
        "architecture": "API Gateway + Monolithic Billing System",
        "status": "running",
        "uptime_seconds": uptime_seconds,
        "authentication": "API key required (Bearer token)",
        "features": ["Team-based access control", "Feature flags", "Rate limiting", "Usage analytics"],
        "endpoints": {
            "web_interface": "/",
            "primary_workflow": "/api/v1/process",
            "medical_extraction": "/api/v1/medical/extract",
            "cpt_search": "/api/v1/cpt/search", 
            "medical_coding": "/api/v1/medical/code-complete",
            "usage_stats": "/api/v1/usage",
            "team_usage": "/api/v1/teams/{team_id}/usage",
            "team_features": "/api/v1/teams/{team_id}/features",
            "health_check": "/health"
        },
        "backend": {
            "type": "monolithic_billing_system",
            "components": ["AI Processing", "CPT Search", "Medical Coding", "Vector Service", "PDF Processing"],
            "performance": "Direct method calls - no HTTP overhead"
        }
    }


# Team Management Endpoints (Admin/Internal Only)

@app.post("/api/v1/admin/teams", response_model=TeamInfo)
async def create_team(
    request: CreateTeamRequest,
    key_info: APIKeyInfo = Depends(get_api_key)
):
    """
    Create a new team (Admin endpoint - requires internal tier)
    """
    try:
        # Check admin access
        if not key_info.team_info or key_info.team_info.tier != "internal":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Create team
        team_id = api_key_manager.create_team(
            team_name=request.team_name,
            tier=request.tier,
            contact_email=request.contact_email,
            enabled_features=request.enabled_features,
            max_results_limit=request.max_results_limit or 50,
            rate_limit_multiplier=request.rate_limit_multiplier or 1.0
        )
        
        # Return created team info
        team_info = api_key_manager.get_team_info(team_id)
        return team_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")


@app.post("/api/v1/admin/api-keys", response_model=CreateAPIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    key_info: APIKeyInfo = Depends(get_api_key)
):
    """
    Create a new API key for a team (Admin endpoint - requires internal tier)
    """
    try:
        # Check admin access
        if not key_info.team_info or key_info.team_info.tier != "internal":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Verify team exists
        team_info = api_key_manager.get_team_info(request.team_id)
        if not team_info:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Create API key
        api_key, key_id = api_key_manager.generate_api_key(
            team_id=request.team_id,
            user_id=request.user_id,
            rate_limit_per_hour=request.rate_limit_per_hour or 1000,
            expires_days=request.expires_days
        )
        
        # Return response (API key shown only once!)
        return CreateAPIKeyResponse(
            api_key=api_key,
            key_id=key_id,
            team_id=request.team_id,
            user_id=request.user_id,
            rate_limit_per_hour=request.rate_limit_per_hour or 1000,
            expires_at=None  # TODO: Calculate expiration if expires_days provided
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}")


@app.get("/api/v1/teams/{team_id}/usage", response_model=TeamUsageStats)
async def get_team_usage_stats(
    team_id: str,
    key_info: APIKeyInfo = Depends(get_api_key)
):
    """
    Get usage statistics for a specific team
    """
    try:
        # Check access - team members can see their own stats, internal can see all
        if key_info.team_id != team_id and key_info.team_info.tier != "internal":
            raise HTTPException(status_code=403, detail="Access denied to team usage stats")
        
        return api_key_manager.get_team_usage_stats(team_id)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve team usage stats: {str(e)}")


@app.get("/api/v1/teams/{team_id}/features", response_model=List[FeatureFlag])
async def get_team_features(
    team_id: str,
    key_info: APIKeyInfo = Depends(get_api_key)
):
    """
    Get available features for a specific team
    """
    try:
        # Check access - team members can see their own features, internal can see all
        if key_info.team_id != team_id and key_info.team_info.tier != "internal":
            raise HTTPException(status_code=403, detail="Access denied to team features")
        
        team_info = api_key_manager.get_team_info(team_id)
        if not team_info:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return api_key_manager.get_available_features(team_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve team features: {str(e)}")


@app.get("/api/v1/admin/teams", response_model=List[TeamInfo])
async def list_all_teams(key_info: APIKeyInfo = Depends(get_api_key)):
    """
    List all teams (Admin endpoint - requires internal tier)
    """
    try:
        # Check admin access
        if not key_info.team_info or key_info.team_info.tier != "internal":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        return api_key_manager.list_all_teams()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list teams: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)