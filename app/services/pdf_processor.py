"""
PDF Processor Service
Handles PDF processing operations
Server-side PDF text extraction to complement client-side processing
"""

import asyncio
import re
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.billing import Billing


class PDFProcessorService:
    """Handles PDF processing operations"""
    
    def __init__(self, parent_billing: 'Billing'):
        """Initialize PDF processor service"""
        self.billing = parent_billing
        
        # Configuration
        self.max_pdf_size = 50 * 1024 * 1024  # 50MB limit
        self.max_text_length = 100000  # 100K characters limit
        
        print(f"📄 PDF Processor Service initialized")
        print(f"   Max PDF Size: {self.max_pdf_size // (1024*1024)}MB")
        print(f"   Max Text Length: {self.max_text_length} characters")
    
    async def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF (server-side processing)
        Fallback for when client-side PDF.js extraction fails
        """
        try:
            # Validate PDF size
            if not self.validate_pdf_size(pdf_bytes):
                raise ValueError(f"PDF too large. Maximum size: {self.max_pdf_size // (1024*1024)}MB")
            
            # Try using PyPDF2 or similar library for server-side extraction
            try:
                import PyPDF2
                import io
                
                # Create PDF reader
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                
                # Extract text from all pages
                extracted_text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    extracted_text += page_text + "\n\n"
                
                # Clean and validate extracted text
                cleaned_text = self.sanitize_extracted_text(extracted_text)
                
                print(f"✅ Extracted {len(cleaned_text)} characters from PDF ({len(pdf_reader.pages)} pages)")
                return cleaned_text
                
            except ImportError:
                print("⚠️ PyPDF2 not installed, trying alternative method...")
                return await self._extract_with_alternative_method(pdf_bytes)
                
        except Exception as e:
            print(f"❌ PDF extraction failed: {e}")
            raise e
    
    async def _extract_with_alternative_method(self, pdf_bytes: bytes) -> str:
        """
        Alternative PDF extraction method using pdfplumber or other libraries
        """
        try:
            import pdfplumber
            import io
            
            extracted_text = ""
            
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n\n"
            
            cleaned_text = self.sanitize_extracted_text(extracted_text)
            print(f"✅ Alternative extraction successful: {len(cleaned_text)} characters")
            return cleaned_text
            
        except ImportError:
            print("⚠️ pdfplumber not installed, using basic text extraction...")
            # Return basic error message if no PDF libraries available
            raise Exception("Server-side PDF extraction requires PyPDF2 or pdfplumber. Please use client-side extraction.")
        
        except Exception as e:
            print(f"❌ Alternative PDF extraction failed: {e}")
            raise e
    
    def validate_pdf(self, pdf_bytes: bytes) -> bool:
        """Validate PDF format and size"""
        try:
            # Check size
            if not self.validate_pdf_size(pdf_bytes):
                return False
            
            # Check PDF header
            if not pdf_bytes.startswith(b'%PDF-'):
                print("❌ Invalid PDF header")
                return False
            
            # Basic PDF structure validation
            if b'%%EOF' not in pdf_bytes[-1024:]:
                print("❌ Invalid PDF footer")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ PDF validation failed: {e}")
            return False
    
    def validate_pdf_size(self, pdf_bytes: bytes) -> bool:
        """Validate PDF size is within limits"""
        size = len(pdf_bytes)
        if size > self.max_pdf_size:
            print(f"❌ PDF too large: {size // (1024*1024)}MB (max: {self.max_pdf_size // (1024*1024)}MB)")
            return False
        
        if size < 100:  # Minimum reasonable PDF size
            print(f"❌ PDF too small: {size} bytes")
            return False
        
        return True
    
    def sanitize_extracted_text(self, text: str) -> str:
        """Clean and sanitize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Trim whitespace
        text = text.strip()
        
        # Apply length limit
        if len(text) > self.max_text_length:
            text = text[:self.max_text_length] + "... [truncated]"
            print(f"⚠️ Text truncated to {self.max_text_length} characters")
        
        return text
    
    def detect_medical_content(self, text: str) -> Dict[str, any]:
        """
        Detect if text contains medical content
        Basic heuristic analysis
        """
        medical_keywords = [
            'patient', 'diagnosis', 'procedure', 'surgery', 'treatment',
            'symptoms', 'medication', 'doctor', 'physician', 'hospital',
            'medical', 'clinical', 'examination', 'therapy', 'prescription',
            'operative', 'postoperative', 'preoperative', 'anesthesia',
            'discharge', 'admission', 'consultation'
        ]
        
        text_lower = text.lower()
        
        # Count medical keyword occurrences
        keyword_matches = []
        total_matches = 0
        
        for keyword in medical_keywords:
            count = text_lower.count(keyword)
            if count > 0:
                keyword_matches.append({"keyword": keyword, "count": count})
                total_matches += count
        
        # Calculate medical content confidence
        text_length = len(text.split())
        confidence = min(1.0, total_matches / max(1, text_length / 100))
        
        is_medical = confidence > 0.1  # 10% threshold
        
        return {
            "is_medical_content": is_medical,
            "confidence": confidence,
            "total_medical_keywords": total_matches,
            "keyword_matches": keyword_matches[:10],  # Top 10 matches
            "text_length": text_length
        }
    
    def extract_structured_data(self, text: str) -> Dict[str, List[str]]:
        """
        Extract structured medical data from text
        Basic pattern recognition for common medical document elements
        """
        structured_data = {
            "dates": [],
            "procedures": [],
            "diagnoses": [],
            "medications": [],
            "measurements": []
        }
        
        try:
            # Extract dates (basic patterns)
            date_patterns = [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
                r'\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                structured_data["dates"].extend(matches)
            
            # Extract procedure-related text (lines containing procedure keywords)
            procedure_keywords = ['procedure', 'surgery', 'operation', 'performed', 'underwent']
            lines = text.split('\n')
            
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in procedure_keywords):
                    structured_data["procedures"].append(line.strip())
            
            # Extract diagnosis-related text
            diagnosis_keywords = ['diagnosis', 'diagnosed', 'condition', 'findings']
            
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in diagnosis_keywords):
                    structured_data["diagnoses"].append(line.strip())
            
            # Extract measurements (numbers with units)
            measurement_pattern = r'\b\d+(?:\.\d+)?\s*(?:mg|ml|cm|mm|kg|lbs|degrees|%|units)\b'
            measurements = re.findall(measurement_pattern, text, re.IGNORECASE)
            structured_data["measurements"] = measurements
            
            # Limit results to prevent oversized responses
            for key in structured_data:
                if len(structured_data[key]) > 20:
                    structured_data[key] = structured_data[key][:20]
            
            return structured_data
            
        except Exception as e:
            print(f"❌ Structured data extraction failed: {e}")
            return structured_data
    
    async def process_pdf_with_analysis(self, pdf_bytes: bytes) -> Dict:
        """
        Complete PDF processing with content analysis
        Returns extracted text plus analysis
        """
        try:
            # Validate PDF
            if not self.validate_pdf(pdf_bytes):
                raise ValueError("Invalid PDF format or size")
            
            # Extract text
            extracted_text = await self.extract_text_from_pdf(pdf_bytes)
            
            if not extracted_text:
                raise ValueError("No text could be extracted from PDF")
            
            # Analyze content
            medical_analysis = self.detect_medical_content(extracted_text)
            structured_data = self.extract_structured_data(extracted_text)
            
            return {
                "success": True,
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "medical_analysis": medical_analysis,
                "structured_data": structured_data,
                "processing_info": {
                    "pdf_size_bytes": len(pdf_bytes),
                    "extraction_method": "server_side"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "extracted_text": "",
                "text_length": 0
            }