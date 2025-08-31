"""
Medical Text Processing API Models
Request/Response models for medical text processing microservice
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MedicalTextRequest(BaseModel):
    """Request model for medical text processing"""
    text: str = Field(..., description="Medical note text content", min_length=1, max_length=100000)
    format: Optional[str] = Field("text", description="Input format: text or pdf")
    extract_structured: Optional[bool] = Field(False, description="Extract structured medical data")


class MedicalTextResponse(BaseModel):
    """Response model for medical text processing"""
    extracted_procedures: str = Field(..., description="AI-extracted procedures and diagnoses")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    success: bool = Field(..., description="Processing success status")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    

class PDFProcessRequest(BaseModel):
    """Request model for PDF processing"""
    pdf_base64: str = Field(..., description="Base64 encoded PDF content")
    extract_structured: Optional[bool] = Field(False, description="Extract structured medical data")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    service_name: str = Field(..., description="Service identifier")
    dependencies: dict = Field(..., description="Dependency status")