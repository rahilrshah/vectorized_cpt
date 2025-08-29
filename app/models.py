"""
Pydantic models for API request/response validation
Matches existing Firebase function response format
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class MedicalNoteRequest(BaseModel):
    """Request model for medical note processing"""
    text: str = Field(..., description="Medical note text content", min_length=1, max_length=100000)
    max_results: Optional[int] = Field(20, description="Maximum number of CPT codes to return", ge=1, le=100)
    similarity_threshold: Optional[float] = Field(0.7, description="Minimum similarity score", ge=0.0, le=1.0)
    include_explanations: Optional[bool] = Field(False, description="Include match explanations")


class DirectTextRequest(BaseModel):
    """Request model for direct text search (skip AI processing)"""
    text: str = Field(..., description="Pre-processed search query", min_length=1, max_length=10000)
    max_results: Optional[int] = Field(20, description="Maximum number of results", ge=1, le=100)
    similarity_threshold: Optional[float] = Field(0.7, description="Minimum similarity score", ge=0.0, le=1.0)


class CPTResult(BaseModel):
    """CPT code search result"""
    cpt_code: str = Field(..., description="CPT procedure code")
    description: str = Field(..., description="Procedure description")
    category: Optional[str] = Field("", description="Procedure category")
    status: Optional[str] = Field("", description="Code status")
    similarity: float = Field(..., description="Similarity score", ge=0.0, le=1.0)
    distance: Optional[float] = Field(None, description="Vector distance")
    match_terms: Optional[List[str]] = Field(None, description="Matched keywords")


class MedicalNoteResponse(BaseModel):
    """Response model for medical note processing - matches Firebase function format"""
    step1_extractedText: str = Field(..., description="Extracted text from input")
    step2_extractedProcedures: str = Field(..., description="AI-extracted procedures and diagnoses")
    step3_embeddingVector: List[float] = Field(..., description="Generated embedding vector")
    step4_cptResults: List[CPTResult] = Field(..., description="CPT code search results")
    results: List[CPTResult] = Field(..., description="CPT code results (alias for step4)")
    success: bool = Field(..., description="Processing success status")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class DirectSearchResponse(BaseModel):
    """Response model for direct text search"""
    results: List[CPTResult] = Field(..., description="CPT code search results")
    success: bool = Field(..., description="Search success status")
    query: str = Field(..., description="Original search query")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    total_results: int = Field(..., description="Total number of results found")


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Overall system status")
    timestamp: float = Field(..., description="Response timestamp")
    version: str = Field(..., description="API version")
    services: Dict[str, str] = Field(..., description="Individual service statuses")
    failed_services: Optional[List[str]] = Field(None, description="List of failed services")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class ServiceStatus(BaseModel):
    """Individual service status"""
    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status (operational/degraded/failed)")
    last_check: datetime = Field(..., description="Last status check time")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional status details")


class PDFUploadRequest(BaseModel):
    """PDF upload request (for future use)"""
    filename: Optional[str] = Field(None, description="Original filename")
    max_results: Optional[int] = Field(20, description="Maximum CPT codes to return", ge=1, le=100)
    similarity_threshold: Optional[float] = Field(0.7, description="Minimum similarity score", ge=0.0, le=1.0)
    extract_structured_data: Optional[bool] = Field(False, description="Extract structured medical data")


class PDFProcessingResponse(BaseModel):
    """PDF processing response"""
    success: bool = Field(..., description="Processing success status")
    extracted_text: str = Field(..., description="Extracted text from PDF")
    text_length: int = Field(..., description="Length of extracted text")
    medical_analysis: Optional[Dict[str, Any]] = Field(None, description="Medical content analysis")
    structured_data: Optional[Dict[str, List[str]]] = Field(None, description="Extracted structured data")
    processing_info: Optional[Dict[str, Any]] = Field(None, description="Processing metadata")
    cpt_results: Optional[List[CPTResult]] = Field(None, description="CPT code results if processed")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class BulkProcessingRequest(BaseModel):
    """Bulk processing request for multiple medical notes"""
    notes: List[str] = Field(..., description="List of medical notes to process", min_items=1, max_items=50)
    max_results_per_note: Optional[int] = Field(20, description="Max results per note", ge=1, le=100)
    similarity_threshold: Optional[float] = Field(0.7, description="Minimum similarity score", ge=0.0, le=1.0)


class BulkProcessingResponse(BaseModel):
    """Bulk processing response"""
    total_notes: int = Field(..., description="Total number of notes processed")
    successful_notes: int = Field(..., description="Number of successfully processed notes")
    failed_notes: int = Field(..., description="Number of failed notes")
    results: List[MedicalNoteResponse] = Field(..., description="Results for each note")
    processing_time_ms: int = Field(..., description="Total processing time")
    errors: Optional[List[str]] = Field(None, description="Error messages for failed notes")


class SystemMetricsResponse(BaseModel):
    """System metrics response"""
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    total_requests: int = Field(..., description="Total requests processed")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")
    average_processing_time_ms: float = Field(..., description="Average processing time")
    cache_hit_rate: Optional[float] = Field(None, description="Cache hit rate")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")


# Legacy compatibility models (for existing frontend)
class LegacySearchRequest(BaseModel):
    """Legacy search request format for backward compatibility"""
    text: str = Field(..., description="Medical note text")


class LegacySearchResponse(BaseModel):
    """Legacy response format matching current Firebase function exactly"""
    step1_extractedText: str
    step2_extractedProcedures: str 
    step3_embeddingVector: List[float]
    step4_cptResults: List[Dict[str, Any]]  # Raw format from Firebase function
    results: List[Dict[str, Any]]          # Raw format
    success: bool
    processing_time_ms: Optional[int] = None
    error: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None