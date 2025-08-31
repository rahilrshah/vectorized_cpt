"""
Medical Coding API Models
Request/Response models for comprehensive medical coding microservice
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AnesthesiaCode(BaseModel):
    """Anesthesia code result"""
    code: str = Field(..., description="Anesthesia code")
    description: str = Field(..., description="Anesthesia description")
    type: str = Field(..., description="Code type")
    similarity: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    reason: str = Field(..., description="Reason for inclusion")


class ModifierCode(BaseModel):
    """Modifier code result"""
    code: str = Field(..., description="Modifier code")
    description: str = Field(..., description="Modifier description")
    type: str = Field(..., description="Modifier type")
    reason: str = Field(..., description="Reason for modifier")


class RelatedCode(BaseModel):
    """Related diagnostic or ancillary code"""
    code: str = Field(..., description="Related code")
    description: str = Field(..., description="Code description")
    type: str = Field(..., description="Code type (diagnosis, status, etc)")
    similarity: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    reason: str = Field(..., description="Reason for inclusion")


class BillingSummary(BaseModel):
    """Billing summary statistics"""
    total_codes: int = Field(..., description="Total number of codes")
    has_modifiers: bool = Field(..., description="Whether modifiers are present")
    has_anesthesia: bool = Field(..., description="Whether anesthesia codes are present")
    complexity: str = Field(..., description="Billing complexity level")
    specialty: str = Field(..., description="Medical specialty")
    billing_confidence: str = Field(..., description="Overall confidence level")


class ComprehensiveCodingRequest(BaseModel):
    """Request model for comprehensive medical coding"""
    primary_codes: List[Dict[str, Any]] = Field(..., description="Primary CPT codes with similarity scores")
    medical_text: str = Field(..., description="AI-extracted medical procedures")
    original_note: str = Field(..., description="Original medical note text")
    include_diagnostics: Optional[bool] = Field(True, description="Include related diagnostic codes")
    include_anesthesia: Optional[bool] = Field(True, description="Include anesthesia codes")
    include_modifiers: Optional[bool] = Field(True, description="Include billing modifiers")


class ComprehensiveCodingResponse(BaseModel):
    """Response model for comprehensive medical coding"""
    primary_codes: List[Dict[str, Any]] = Field(..., description="Primary CPT codes")
    anesthesia_codes: List[AnesthesiaCode] = Field(..., description="Anesthesia codes")
    modifiers: List[ModifierCode] = Field(..., description="Anatomical and procedural modifiers")
    related_codes: List[RelatedCode] = Field(..., description="Related diagnostic codes")
    coding_confidence: str = Field(..., description="Overall coding confidence")
    medical_specialty: str = Field(..., description="Detected medical specialty")
    billing_summary: BillingSummary = Field(..., description="Billing summary")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    success: bool = Field(..., description="Processing success status")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class QuickCodingRequest(BaseModel):
    """Request model for quick single-code analysis"""
    cpt_code: str = Field(..., description="Primary CPT code to analyze")
    medical_context: str = Field(..., description="Medical context or procedure description")


class QuickCodingResponse(BaseModel):
    """Response model for quick coding analysis"""
    cpt_code: str = Field(..., description="Analyzed CPT code")
    suggested_anesthesia: List[AnesthesiaCode] = Field(..., description="Suggested anesthesia codes")
    suggested_modifiers: List[ModifierCode] = Field(..., description="Suggested modifiers")
    suggested_diagnostics: List[RelatedCode] = Field(..., description="Suggested diagnostic codes")
    confidence: str = Field(..., description="Suggestion confidence")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    service_name: str = Field(..., description="Service identifier")
    dependencies: Dict[str, Any] = Field(..., description="Dependency status")