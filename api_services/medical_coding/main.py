"""
Medical Coding API
FastAPI microservice for comprehensive medical coding with anesthesia, modifiers, and diagnostics
Preserves all existing functionality from the Billing system
"""

import time
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import (
    ComprehensiveCodingRequest, ComprehensiveCodingResponse,
    QuickCodingRequest, QuickCodingResponse,
    AnesthesiaCode, ModifierCode, RelatedCode, BillingSummary,
    HealthCheckResponse
)
from .service import MedicalCodingMicroservice

# Global service instance
coding_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global coding_service
    
    # Startup
    print("🚀 Starting Medical Coding API...")
    coding_service = MedicalCodingMicroservice()
    print("✅ Medical Coding API ready")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Medical Coding API...")


# Create FastAPI application
app = FastAPI(
    title="Medical Coding API",
    description="Microservice for comprehensive medical coding including anesthesia, modifiers, and diagnostics",
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


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "service": "medical_coding"
        }
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    global coding_service
    
    if not coding_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    health_status = await coding_service.get_health_status()
    
    return HealthCheckResponse(
        status=health_status["status"],
        timestamp=datetime.now(),
        service_name=health_status["service_name"],
        dependencies=health_status["dependencies"]
    )


@app.post("/api/v1/medical/code-complete", response_model=ComprehensiveCodingResponse)
async def comprehensive_medical_coding(request: ComprehensiveCodingRequest):
    """
    Comprehensive medical coding with anesthesia, modifiers, and diagnostics
    Preserves exact functionality from the original Billing system
    """
    global coding_service
    
    if not coding_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Use existing comprehensive coding logic unchanged
        result = await coding_service.detect_comprehensive_codes(
            primary_codes=request.primary_codes,
            medical_text=request.medical_text,
            original_note=request.original_note,
            include_diagnostics=request.include_diagnostics,
            include_anesthesia=request.include_anesthesia,
            include_modifiers=request.include_modifiers
        )
        
        if result["success"]:
            # Convert to proper response format
            anesthesia_codes = [
                AnesthesiaCode(**code) for code in result.get("anesthesia_codes", [])
            ]
            
            modifiers = [
                ModifierCode(**modifier) for modifier in result.get("modifiers", [])
            ]
            
            related_codes = [
                RelatedCode(**code) for code in result.get("related_codes", [])
            ]
            
            billing_summary = BillingSummary(**result.get("billing_summary", {}))
            
            return ComprehensiveCodingResponse(
                primary_codes=result["primary_codes"],
                anesthesia_codes=anesthesia_codes,
                modifiers=modifiers,
                related_codes=related_codes,
                coding_confidence=result["coding_confidence"],
                medical_specialty=result["medical_specialty"],
                billing_summary=billing_summary,
                processing_time_ms=result["processing_time_ms"],
                success=result["success"]
            )
        else:
            return ComprehensiveCodingResponse(
                primary_codes=result["primary_codes"],
                anesthesia_codes=[],
                modifiers=[],
                related_codes=[],
                coding_confidence=result["coding_confidence"],
                medical_specialty=result["medical_specialty"],
                billing_summary=BillingSummary(**result["billing_summary"]),
                processing_time_ms=result["processing_time_ms"],
                success=result["success"],
                error=result.get("error", "Unknown coding error")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comprehensive coding failed: {str(e)}")


@app.post("/api/v1/medical/quick-analysis", response_model=QuickCodingResponse)
async def quick_code_analysis(request: QuickCodingRequest):
    """
    Quick analysis of single CPT code for suggested ancillary codes
    Uses existing medical coding intelligence
    """
    global coding_service
    
    if not coding_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Use existing quick analysis logic
        result = await coding_service.quick_code_analysis(
            cpt_code=request.cpt_code,
            medical_context=request.medical_context
        )
        
        if result["success"]:
            # Convert to proper response format
            suggested_anesthesia = [
                AnesthesiaCode(**code) for code in result["suggested_anesthesia"]
            ]
            
            suggested_modifiers = [
                ModifierCode(**modifier) for modifier in result["suggested_modifiers"]
            ]
            
            suggested_diagnostics = [
                RelatedCode(**code) for code in result["suggested_diagnostics"]
            ]
            
            return QuickCodingResponse(
                cpt_code=result["cpt_code"],
                suggested_anesthesia=suggested_anesthesia,
                suggested_modifiers=suggested_modifiers,
                suggested_diagnostics=suggested_diagnostics,
                confidence=result["confidence"],
                processing_time_ms=result["processing_time_ms"]
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Quick analysis failed"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick analysis failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Medical Coding API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/v1/medical/code-complete",
            "/api/v1/medical/quick-analysis"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)