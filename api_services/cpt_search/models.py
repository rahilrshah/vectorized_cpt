"""
CPT Search API Models
Request/Response models for CPT code search microservice
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class CPTSearchRequest(BaseModel):
    """Request model for CPT code search"""
    procedures: str = Field(..., description="AI-extracted procedures text", min_length=1)
    max_results: Optional[int] = Field(20, description="Maximum number of results", ge=1, le=100)
    similarity_threshold: Optional[float] = Field(0.6, description="Minimum similarity score", ge=0.0, le=1.0)
    include_embeddings: Optional[bool] = Field(False, description="Include embedding vectors in response")


class DirectSearchRequest(BaseModel):
    """Request model for direct keyword search"""
    query: str = Field(..., description="Search query text", min_length=1)
    max_results: Optional[int] = Field(20, description="Maximum number of results", ge=1, le=100)
    similarity_threshold: Optional[float] = Field(0.6, description="Minimum similarity score", ge=0.0, le=1.0)


class CPTResult(BaseModel):
    """CPT code search result"""
    cpt_code: str = Field(..., description="CPT procedure code")
    description: str = Field(..., description="Procedure description")
    category: Optional[str] = Field("", description="Procedure category")
    status: Optional[str] = Field("", description="Code status")
    similarity: float = Field(..., description="Similarity score", ge=0.0, le=1.0)
    distance: Optional[float] = Field(None, description="Vector distance")
    match_terms: Optional[List[str]] = Field(None, description="Matched keywords")


class CPTSearchResponse(BaseModel):
    """Response model for CPT search"""
    results: List[CPTResult] = Field(..., description="CPT search results")
    total_found: int = Field(..., description="Total number of matches found")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    embedding_dimensions: Optional[int] = Field(None, description="Embedding vector dimensions")
    search_method: str = Field(..., description="Search method used")
    success: bool = Field(..., description="Search success status")
    error: Optional[str] = Field(None, description="Error message if search failed")


class EmbeddingRequest(BaseModel):
    """Request model for embedding generation"""
    text: str = Field(..., description="Text to generate embedding for", min_length=1)


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation"""
    embedding: List[float] = Field(..., description="Generated embedding vector")
    dimensions: int = Field(..., description="Number of dimensions")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    model_used: str = Field(..., description="Embedding model identifier")
    success: bool = Field(..., description="Generation success status")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    service_name: str = Field(..., description="Service identifier")
    dependencies: Dict[str, Any] = Field(..., description="Dependency status")