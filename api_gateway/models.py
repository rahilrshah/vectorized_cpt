"""
API Gateway Models
Request/Response models for the API Gateway with authentication
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class APIKeyStatus(str, Enum):
    """API Key status enumeration"""
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    expired = "expired"


class ServiceName(str, Enum):
    """Available microservice names"""
    medical_processor = "medical_processor"
    cpt_search = "cpt_search"
    medical_coding = "medical_coding"


class APIKeyInfo(BaseModel):
    """API Key information"""
    key_id: str = Field(..., description="API key identifier")
    user_id: str = Field(..., description="User identifier")
    status: APIKeyStatus = Field(..., description="Key status")
    rate_limit_per_hour: int = Field(..., description="Hourly rate limit")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")


class UsageStats(BaseModel):
    """Usage statistics"""
    total_requests: int = Field(..., description="Total requests made")
    requests_this_hour: int = Field(..., description="Requests in current hour")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")
    average_response_time_ms: float = Field(..., description="Average response time")


class UnifiedRequest(BaseModel):
    """Unified request model for all services"""
    text: Optional[str] = Field(None, description="Text content for processing")
    procedures: Optional[str] = Field(None, description="Medical procedures text")
    query: Optional[str] = Field(None, description="Search query")
    primary_codes: Optional[List[Dict[str, Any]]] = Field(None, description="Primary CPT codes")
    medical_text: Optional[str] = Field(None, description="Medical text content")
    original_note: Optional[str] = Field(None, description="Original medical note")
    cpt_code: Optional[str] = Field(None, description="CPT code for analysis")
    medical_context: Optional[str] = Field(None, description="Medical context")
    pdf_base64: Optional[str] = Field(None, description="Base64 encoded PDF")
    max_results: Optional[int] = Field(20, description="Maximum results")
    similarity_threshold: Optional[float] = Field(0.6, description="Similarity threshold")
    include_diagnostics: Optional[bool] = Field(True, description="Include diagnostics")
    include_anesthesia: Optional[bool] = Field(True, description="Include anesthesia")
    include_modifiers: Optional[bool] = Field(True, description="Include modifiers")
    extract_structured: Optional[bool] = Field(False, description="Extract structured data")
    include_embeddings: Optional[bool] = Field(False, description="Include embeddings")


class UnifiedResponse(BaseModel):
    """Unified response model"""
    success: bool = Field(..., description="Request success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    processing_time_ms: int = Field(..., description="Processing time")
    service_used: str = Field(..., description="Service that processed the request")
    api_key_id: str = Field(..., description="API key used")
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(..., description="Response timestamp")


class CompleteWorkflowRequest(BaseModel):
    """Complete workflow request (all services in sequence)"""
    text: str = Field(..., description="Medical note text", min_length=1)
    max_results: Optional[int] = Field(20, description="Maximum CPT results")
    include_comprehensive: Optional[bool] = Field(True, description="Include comprehensive coding")
    pdf_base64: Optional[str] = Field(None, description="PDF content if processing PDF")


class CompleteWorkflowResponse(BaseModel):
    """Complete workflow response"""
    step1_extracted_text: str = Field(..., description="Extracted text")
    step2_extracted_procedures: str = Field(..., description="AI extracted procedures")
    step3_cpt_results: List[Dict[str, Any]] = Field(..., description="CPT search results")
    step4_comprehensive_codes: Optional[Dict[str, Any]] = Field(None, description="Comprehensive coding")
    total_processing_time_ms: int = Field(..., description="Total processing time")
    services_used: List[str] = Field(..., description="Services called")
    success: bool = Field(..., description="Overall success")
    api_key_id: str = Field(..., description="API key used")
    request_id: str = Field(..., description="Request identifier")


class HealthCheckResponse(BaseModel):
    """Gateway health check response"""
    gateway_status: str = Field(..., description="Gateway status")
    services_status: Dict[str, Dict[str, Any]] = Field(..., description="Individual service statuses")
    timestamp: datetime = Field(..., description="Check timestamp")
    total_services: int = Field(..., description="Total number of services")
    healthy_services: int = Field(..., description="Number of healthy services")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: str = Field(..., description="Request identifier")
    timestamp: datetime = Field(..., description="Error timestamp")