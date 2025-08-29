"""
Main FastAPI Application
Medical Billing API using the Billing class architecture
"""

import time
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

from app.billing import Billing
from app.models import (
    MedicalNoteRequest, MedicalNoteResponse,
    DirectTextRequest, DirectSearchResponse,
    HealthCheckResponse, ErrorResponse,
    LegacySearchRequest, LegacySearchResponse
)

# Global billing system instance
billing_system = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global billing_system
    
    # Startup
    print("🚀 Starting Medical Billing API...")
    billing_system = Billing()
    print("✅ Billing system initialized")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down Medical Billing API...")
    if billing_system and hasattr(billing_system, 'firestore_service'):
        billing_system.firestore_service.close()
    print("✅ Billing system closed")


# Create FastAPI app
app = FastAPI(
    title="Medical Billing API",
    description="CPT code search and medical note processing API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware for existing frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (existing frontend)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # Directory doesn't exist, create placeholder
    import os
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle request validation errors"""
    return JSONResponse(
        status_code=400,
        content={
            "error": "Invalid request format",
            "details": exc.errors(),
            "message": "Please check your request parameters"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


# API Routes

@app.post("/api/v1/cpt-search/medical-note", response_model=MedicalNoteResponse)
async def process_medical_note(request: MedicalNoteRequest):
    """
    Main endpoint - processes medical note text and returns CPT codes
    Replaces Firebase Cloud Function functionality
    """
    try:
        if not billing_system:
            raise HTTPException(status_code=503, detail="Billing system not initialized")
        
        start_time = time.time()
        
        # Process medical note using Billing class
        result = await billing_system.process_medical_note(
            text=request.text,
            max_results=request.max_results
        )
        
        # Add processing time
        processing_time = int((time.time() - start_time) * 1000)
        result["processing_time_ms"] = processing_time
        
        return MedicalNoteResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/v1/cpt-search/text", response_model=DirectSearchResponse)
async def search_cpt_codes_direct(request: DirectTextRequest):
    """
    Direct CPT code search (skip Gemini processing)
    For already-processed medical summaries
    """
    try:
        if not billing_system:
            raise HTTPException(status_code=503, detail="Billing system not initialized")
        
        start_time = time.time()
        
        # Direct search using Billing class
        results = await billing_system.search_cpt_codes(
            query=request.text,
            max_results=request.max_results
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return DirectSearchResponse(
            results=results,
            success=True,
            query=request.text,
            processing_time_ms=processing_time,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/v1/health", response_model=HealthCheckResponse)
async def health_check():
    """Comprehensive system health check"""
    try:
        if not billing_system:
            return HealthCheckResponse(
                status="unhealthy",
                timestamp=time.time(),
                version="1.0.0",
                services={},
                error="Billing system not initialized"
            )
        
        # Get health status from Billing class
        health_status = await billing_system.get_system_health()
        
        return HealthCheckResponse(**health_status)
        
    except Exception as e:
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=time.time(),
            version="1.0.0",
            services={},
            error=str(e)
        )


@app.get("/api/v1/status")
async def service_status():
    """Simple service status check"""
    try:
        if not billing_system:
            return {
                "status": "unhealthy",
                "message": "Billing system not initialized",
                "timestamp": time.time()
            }
        
        # Quick status check
        return {
            "status": "operational",
            "message": "All services running",
            "timestamp": time.time(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": time.time()
        }


# Backward compatibility endpoints

@app.post("/search", response_model=LegacySearchResponse)
async def legacy_search_endpoint(request: LegacySearchRequest):
    """
    Legacy endpoint for existing frontend compatibility
    Maintains exact same interface as current system
    """
    try:
        if not billing_system:
            raise HTTPException(status_code=503, detail="System not ready")
        
        # Convert to new format and process
        result = await billing_system.process_medical_note(request.text)
        
        # Convert back to legacy format
        legacy_response = LegacySearchResponse(
            step1_extractedText=result["step1_extractedText"],
            step2_extractedProcedures=result["step2_extractedProcedures"], 
            step3_embeddingVector=result["step3_embeddingVector"],
            step4_cptResults=result["step4_cptResults"],
            results=result["results"],
            success=result["success"],
            processing_time_ms=result.get("processing_time_ms"),
            error=result.get("error"),
            status="completed" if result["success"] else "failed",
            message="Processing completed successfully" if result["success"] else result.get("error")
        )
        
        return legacy_response
        
    except Exception as e:
        return LegacySearchResponse(
            step1_extractedText="",
            step2_extractedProcedures="",
            step3_embeddingVector=[],
            step4_cptResults=[],
            results=[],
            success=False,
            error=str(e),
            status="failed",
            message=str(e)
        )


@app.get("/")
async def serve_frontend():
    """Serve existing HTML frontend"""
    try:
        return FileResponse("static/index.html")
    except FileNotFoundError:
        # If no static frontend, return API info
        return {
            "message": "Medical Billing API",
            "version": "1.0.0",
            "docs": "/api/docs",
            "health": "/api/v1/health",
            "endpoints": {
                "process_note": "POST /api/v1/cpt-search/medical-note",
                "direct_search": "POST /api/v1/cpt-search/text",
                "legacy_search": "POST /search"
            }
        }


# PDF Processing endpoint (future enhancement)

@app.post("/api/v1/cpt-search/pdf")
async def process_pdf_document(file: UploadFile = File(...)):
    """
    Process PDF document and extract CPT codes
    """
    try:
        if not billing_system:
            raise HTTPException(status_code=503, detail="System not ready")
        
        # Validate file type
        if not file.content_type == "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read PDF content
        pdf_content = await file.read()
        
        # Process PDF using Billing class
        result = await billing_system.process_pdf_document(pdf_content)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")


# Development and debugging endpoints

@app.get("/api/v1/debug/config")
async def debug_config():
    """Get current configuration (for debugging)"""
    try:
        if not billing_system:
            return {"error": "System not initialized"}
        
        config_dict = billing_system.config.to_dict()
        
        # Remove sensitive information
        if "credentials" in config_dict:
            config_dict["credentials"] = "[REDACTED]"
        
        return config_dict
        
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/debug/services")
async def debug_services():
    """Get service information (for debugging)"""
    try:
        if not billing_system:
            return {"error": "System not initialized"}
        
        return {
            "billing_system": "initialized",
            "services": {
                "cpt_search": "initialized",
                "ai_processor": "initialized", 
                "vector_service": "initialized",
                "firestore_service": "initialized",
                "pdf_processor": "initialized"
            },
            "config": {
                "collection_name": billing_system.config.collection_name,
                "embedding_model": billing_system.config.embedding_model,
                "generative_model": billing_system.config.generative_model
            }
        }
        
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Medical Billing API Server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )