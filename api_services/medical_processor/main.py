"""
Medical Text Processing API
FastAPI microservice for medical text and PDF processing
Preserves all existing functionality from the Billing system
"""

import time
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import (
    MedicalTextRequest, MedicalTextResponse,
    PDFProcessRequest, HealthCheckResponse
)
from .service import MedicalTextProcessingService

# Global service instance
medical_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global medical_service
    
    # Startup
    print("🚀 Starting Medical Text Processing API...")
    medical_service = MedicalTextProcessingService()
    print("✅ Medical Text Processing API ready")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Medical Text Processing API...")


# Create FastAPI application
app = FastAPI(
    title="Medical Text Processing API",
    description="Microservice for processing medical notes and extracting procedures using AI",
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
            "service": "medical_text_processor"
        }
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    global medical_service
    
    if not medical_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    health_status = await medical_service.get_health_status()
    
    return HealthCheckResponse(
        status=health_status["status"],
        timestamp=datetime.now(),
        service_name=health_status["service_name"],
        dependencies=health_status["dependencies"]
    )


@app.post("/api/v1/medical/extract", response_model=MedicalTextResponse)
async def extract_medical_procedures(request: MedicalTextRequest):
    """
    Extract medical procedures from text using AI
    Preserves exact functionality from the original Billing system
    """
    global medical_service
    
    if not medical_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Use existing service logic unchanged
        result = await medical_service.extract_procedures_from_text(
            text=request.text,
            extract_structured=request.extract_structured
        )
        
        if result["success"]:
            return MedicalTextResponse(
                extracted_procedures=result["extracted_procedures"],
                processing_time_ms=result["processing_time_ms"],
                success=result["success"]
            )
        else:
            return MedicalTextResponse(
                extracted_procedures="",
                processing_time_ms=result["processing_time_ms"],
                success=result["success"],
                error=result.get("error", "Unknown processing error")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/v1/medical/extract-pdf")
async def extract_from_pdf(request: PDFProcessRequest):
    """
    Extract medical procedures from PDF document
    Preserves exact functionality from the original PDF processor
    """
    global medical_service
    
    if not medical_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Use existing PDF processing logic unchanged
        result = await medical_service.process_pdf_document(
            pdf_base64=request.pdf_base64,
            extract_structured=request.extract_structured
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Medical Text Processing API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/v1/medical/extract",
            "/api/v1/medical/extract-pdf"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)