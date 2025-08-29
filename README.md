# Medical Billing API - CPT Code Search System

A comprehensive API system for medical billing and CPT code search using AI/ML technology. Built with the **Billing class architecture** that consolidates all functionality into a clean, organized structure.

## 🏗️ Architecture Overview

### Billing Class Structure
```
Billing (Main Orchestrator)
├── BillingConfig          # Configuration management
├── CPTSearchService       # CPT code search logic
├── AIProcessorService     # Gemini AI + embeddings
├── VectorService          # Vector operations
├── FirestoreService       # Database operations
└── PDFProcessorService    # PDF text extraction
```

### API Endpoints
```
/api/v1/cpt-search/medical-note    # Process medical note → CPT codes
/api/v1/cpt-search/text           # Direct text search
/api/v1/health                    # System health check
/search                           # Legacy endpoint (backward compatibility)
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test the System
- **API Documentation**: http://localhost:8000/api/docs
- **Web Interface**: http://localhost:8000 (existing frontend)
- **Health Check**: http://localhost:8000/api/v1/health

## 📋 API Usage Examples

### Process Medical Note
```bash
curl -X POST "http://localhost:8000/api/v1/cpt-search/medical-note" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Patient underwent arthroscopic knee surgery for meniscal tear repair",
       "max_results": 10,
       "similarity_threshold": 0.7
     }'
```

### Direct Text Search
```bash
curl -X POST "http://localhost:8000/api/v1/cpt-search/text" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "knee arthroscopy meniscus",
       "max_results": 5
     }'
```

### Health Check
```bash
curl "http://localhost:8000/api/v1/health"
```

## 🔧 Configuration

### Environment Setup
The system uses existing configuration files:
- `config.py` - Basic configuration
- `vertex_ai_config.json` - Vertex AI settings
- Firebase credentials JSON file

### Key Configuration Values
```python
PROJECT_ID = "cpt-code-vectorized-dataset"
COLLECTION_NAME = "Vectorized_CPT_Test"
EMBEDDING_MODEL = "text-embedding-004"
GENERATIVE_MODEL = "gemini-2.0-flash-exp"
```

## 🏥 Medical Note Processing Pipeline

### Step-by-Step Process
1. **Text Extraction**: Raw medical note input
2. **AI Processing**: Gemini extracts procedures and diagnoses
3. **Embedding Generation**: Convert to 768-dimensional vector
4. **CPT Search**: Find matching codes using vector similarity
5. **Results Formatting**: Return structured CPT code matches

### Response Format
```json
{
  "step1_extractedText": "Patient underwent arthroscopic...",
  "step2_extractedProcedures": "Arthroscopic meniscal repair, knee surgery",
  "step3_embeddingVector": [0.1234, -0.5678, ...],
  "step4_cptResults": [
    {
      "cpt_code": "29881",
      "description": "Arthroscopy, knee; with meniscectomy",
      "similarity": 0.89,
      "category": "Surgery"
    }
  ],
  "results": [...],
  "success": true,
  "processing_time_ms": 1250
}
```

## 📊 System Components

### Billing Class (Main Orchestrator)
- **Purpose**: Central coordination of all services
- **Methods**: 
  - `process_medical_note()` - Complete pipeline
  - `search_cpt_codes()` - Direct search
  - `get_system_health()` - Health monitoring

### Service Classes

#### CPTSearchService
- Vector-based CPT code searching
- Keyword fallback when vector search fails
- Result formatting and scoring

#### AIProcessorService  
- Gemini AI for medical text processing
- Vertex AI embedding generation
- REST API integration with Google Cloud

#### FirestoreService
- Database operations and queries
- Document retrieval and caching
- Collection management

#### VectorService
- Vector similarity calculations
- Embedding validation
- Batch processing operations

#### PDFProcessorService
- Server-side PDF text extraction
- Medical content analysis
- Structured data extraction

## 🔍 Backward Compatibility

### Existing Frontend Support
- All existing HTML/JS/CSS files work unchanged
- Legacy `/search` endpoint maintains exact same interface
- Same response format as Firebase Cloud Functions

### Migration Path
- Current system: Firebase Functions + Flask server
- New system: Unified Billing API with FastAPI
- **Zero breaking changes** for existing clients

## 🛠️ Development

### Project Structure
```
project/
├── app/
│   ├── billing.py              # Main Billing class
│   ├── config.py               # Configuration
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Pydantic models
│   └── services/
│       ├── cpt_search.py       # CPT search logic
│       ├── ai_processor.py     # AI/ML operations
│       ├── firestore_service.py # Database operations
│       ├── vector_service.py   # Vector operations
│       └── pdf_processor.py    # PDF processing
├── static/                     # Frontend files
├── requirements.txt            # Dependencies
└── README.md                  # This file
```

### Testing
```bash
# Structure test (no dependencies needed)
python simple_test.py

# Full system test (requires dependencies)
python test_billing_system.py
```

### Development Server
```bash
# Development mode with auto-reload
python -m uvicorn app.main:app --reload --log-level debug

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📈 Performance Features

### Optimizations
- **Async Processing**: All I/O operations are asynchronous
- **Connection Pooling**: Reuse connections to Google Cloud APIs
- **Error Handling**: Comprehensive error catching and recovery
- **Logging**: Detailed logging for debugging and monitoring

### Scalability
- **Stateless Design**: No shared state between requests
- **Service Isolation**: Clean separation of concerns
- **Resource Management**: Proper cleanup and connection handling

## 🔐 Security Features

### Current Implementation
- **Input Validation**: Pydantic models with strict validation
- **Error Sanitization**: Safe error messages without data leakage
- **CORS Configuration**: Configurable cross-origin settings

### Production Recommendations
- Add API key authentication
- Implement rate limiting
- Add request logging and monitoring
- Use HTTPS in production

## 📝 API Response Models

All API responses use strongly-typed Pydantic models:
- `MedicalNoteResponse` - Complete pipeline results
- `DirectSearchResponse` - Direct search results  
- `HealthCheckResponse` - System health status
- `ErrorResponse` - Standardized error format

## 🎯 Success Criteria

✅ **Functionality Preserved**: All existing features work identically
✅ **Performance Maintained**: Same or better response times  
✅ **Backward Compatible**: Existing frontend works unchanged
✅ **Clean Architecture**: Well-organized, maintainable code
✅ **Type Safety**: Full Pydantic validation
✅ **Documentation**: Auto-generated OpenAPI docs

## 🔄 Deployment Options

### Local Development
```bash
python -m uvicorn app.main:app --reload
```

### Docker (Future)
```bash
docker build -t medical-billing-api .
docker run -p 8000:8000 medical-billing-api
```

### Cloud Deployment
- Google Cloud Run
- AWS Lambda with FastAPI
- Azure Container Instances

## 📞 Support

For issues or questions:
1. Check the API documentation at `/api/docs`
2. Review logs for error details
3. Test individual services using the health check endpoints

---

**🏥 Medical Billing API v1.0.0** - Powered by the Billing Class Architecture