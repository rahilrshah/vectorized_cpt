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


class TeamTier(str, Enum):
    """Team tier enumeration for access levels"""
    basic = "basic"
    premium = "premium"
    enterprise = "enterprise"
    internal = "internal"


class ServiceName(str, Enum):
    """Available microservice names"""
    medical_processor = "medical_processor"
    cpt_search = "cpt_search"
    medical_coding = "medical_coding"


class TeamInfo(BaseModel):
    """Team information"""
    team_id: str = Field(..., description="Team identifier")
    team_name: str = Field(..., description="Team display name")
    tier: TeamTier = Field(..., description="Team access tier")
    enabled_features: List[str] = Field(default_factory=list, description="Enabled feature flags")
    max_results_limit: int = Field(50, description="Maximum results per request")
    rate_limit_multiplier: float = Field(1.0, description="Rate limit multiplier")
    created_at: datetime = Field(..., description="Team creation timestamp")
    contact_email: Optional[str] = Field(None, description="Team contact email")


class APIKeyInfo(BaseModel):
    """API Key information"""
    key_id: str = Field(..., description="API key identifier")
    user_id: str = Field(..., description="User identifier")
    team_id: str = Field(..., description="Team identifier")
    status: APIKeyStatus = Field(..., description="Key status")
    rate_limit_per_hour: int = Field(..., description="Hourly rate limit")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    # Team information (populated during validation)
    team_info: Optional[TeamInfo] = Field(None, description="Associated team information")


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


class CreateTeamRequest(BaseModel):
    """Request to create a new team"""
    team_name: str = Field(..., description="Team display name", min_length=1)
    tier: TeamTier = Field(..., description="Team access tier")
    contact_email: Optional[str] = Field(None, description="Team contact email")
    enabled_features: Optional[List[str]] = Field(default_factory=list, description="Initial feature flags")
    max_results_limit: Optional[int] = Field(50, description="Maximum results per request")
    rate_limit_multiplier: Optional[float] = Field(1.0, description="Rate limit multiplier")


class CreateAPIKeyRequest(BaseModel):
    """Request to create a new API key"""
    team_id: str = Field(..., description="Team identifier")
    user_id: str = Field(..., description="User identifier")
    rate_limit_per_hour: Optional[int] = Field(1000, description="Hourly rate limit")
    expires_days: Optional[int] = Field(None, description="Expiration in days")


class CreateAPIKeyResponse(BaseModel):
    """Response for API key creation"""
    api_key: str = Field(..., description="Generated API key (only shown once)")
    key_id: str = Field(..., description="API key identifier")
    team_id: str = Field(..., description="Team identifier")
    user_id: str = Field(..., description="User identifier")
    rate_limit_per_hour: int = Field(..., description="Hourly rate limit")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class TeamUsageStats(BaseModel):
    """Team-level usage statistics"""
    team_id: str = Field(..., description="Team identifier")
    team_name: str = Field(..., description="Team display name")
    total_requests: int = Field(..., description="Total requests by team")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")
    requests_this_hour: int = Field(..., description="Requests in current hour")
    average_response_time_ms: float = Field(..., description="Average response time")
    active_api_keys: int = Field(..., description="Number of active API keys")
    most_used_endpoints: List[Dict[str, Any]] = Field(default_factory=list, description="Most used endpoints")


class FeatureFlag(BaseModel):
    """Feature flag definition"""
    flag_name: str = Field(..., description="Feature flag name")
    description: str = Field(..., description="Feature description")
    default_enabled: bool = Field(False, description="Default enabled state")
    required_tier: Optional[TeamTier] = Field(None, description="Minimum required tier")