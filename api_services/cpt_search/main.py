"""
CPT Search API
FastAPI microservice for CPT code searching with vector similarity
Preserves all existing functionality from the Billing system
"""

import time
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import (
    CPTSearchRequest, CPTSearchResponse, CPTResult,
    DirectSearchRequest, EmbeddingRequest, EmbeddingResponse,
    HealthCheckResponse
)
from .service import CPTSearchMicroservice

# Global service instance
cpt_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global cpt_service
    
    # Startup
    print("🚀 Starting CPT Search API...")
    cpt_service = CPTSearchMicroservice()
    print("✅ CPT Search API ready")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down CPT Search API...")


# Create FastAPI application
app = FastAPI(
    title="CPT Search API",
    description="Microservice for searching CPT codes using AI-enhanced similarity matching",
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
            "service": "cpt_search"
        }
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    global cpt_service
    
    if not cpt_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    health_status = await cpt_service.get_health_status()
    
    return HealthCheckResponse(
        status=health_status["status"],
        timestamp=datetime.now(),
        service_name=health_status["service_name"],
        dependencies=health_status["dependencies"]
    )


@app.post("/api/v1/cpt/search", response_model=CPTSearchResponse)
async def search_cpt_codes(request: CPTSearchRequest):
    """
    Search CPT codes using AI-enhanced vector similarity
    Preserves exact functionality from the original Billing system
    """
    global cpt_service
    
    if not cpt_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Use existing search logic unchanged
        result = await cpt_service.search_cpt_codes(
            procedures=request.procedures,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold,
            include_embeddings=request.include_embeddings
        )
        
        if result["success"]:
            # Convert results to proper response format
            cpt_results = []
            for res in result["results"]:
                cpt_results.append(CPTResult(
                    cpt_code=res.get("cpt_code", ""),
                    description=res.get("description", ""),
                    category=res.get("category", ""),
                    status=res.get("status", ""),
                    similarity=res.get("similarity", 0.0),
                    distance=res.get("distance"),
                    match_terms=res.get("match_terms", [])
                ))
            
            return CPTSearchResponse(
                results=cpt_results,
                total_found=result["total_found"],
                processing_time_ms=result["processing_time_ms"],
                embedding_dimensions=result["embedding_dimensions"],
                search_method=result["search_method"],
                success=result["success"]
            )
        else:
            return CPTSearchResponse(
                results=[],
                total_found=0,
                processing_time_ms=result["processing_time_ms"],
                search_method=result["search_method"],
                success=result["success"],
                error=result.get("error", "Unknown search error")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/api/v1/cpt/search-direct", response_model=CPTSearchResponse)
async def direct_search(request: DirectSearchRequest):
    """
    Direct keyword-based CPT search
    Preserves exact functionality from existing keyword search
    """
    global cpt_service
    
    if not cpt_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Use existing keyword search logic unchanged
        result = await cpt_service.direct_keyword_search(
            query=request.query,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold
        )
        
        if result["success"]:
            # Convert results to proper response format
            cpt_results = []
            for res in result["results"]:
                cpt_results.append(CPTResult(
                    cpt_code=res.get("cpt_code", ""),
                    description=res.get("description", ""),
                    category=res.get("category", ""),
                    status=res.get("status", ""),
                    similarity=res.get("similarity", 0.0),
                    distance=res.get("distance"),
                    match_terms=res.get("match_terms", [])
                ))
            
            return CPTSearchResponse(
                results=cpt_results,
                total_found=result["total_found"],
                processing_time_ms=result["processing_time_ms"],
                search_method=result["search_method"],
                success=result["success"]
            )
        else:
            return CPTSearchResponse(
                results=[],
                total_found=0,
                processing_time_ms=result["processing_time_ms"],
                search_method=result["search_method"],
                success=result["success"],
                error=result.get("error", "Unknown search error")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Direct search failed: {str(e)}")


@app.post("/api/v1/cpt/embedding", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """
    Generate embedding vector for text
    Uses existing Vertex AI embedding generation
    """
    global cpt_service
    
    if not cpt_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Use existing embedding generation logic unchanged
        result = await cpt_service.generate_embedding_only(request.text)
        
        if result["success"]:
            return EmbeddingResponse(
                embedding=result["embedding"],
                dimensions=result["dimensions"],
                processing_time_ms=result["processing_time_ms"],
                model_used=result["model_used"],
                success=result["success"]
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Embedding generation failed"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CPT Search API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/v1/cpt/search",
            "/api/v1/cpt/search-direct", 
            "/api/v1/cpt/embedding"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)