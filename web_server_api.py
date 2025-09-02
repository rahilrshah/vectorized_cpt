#!/usr/bin/env python3
"""
Web Server for Vectorized CPT API Gateway
FastAPI-based web server that provides testing interface for the API Gateway
Serves the static web testing dashboard
"""

import os
import asyncio
import base64
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

class WebAPIClient:
    """Web-specific API client for API Gateway communication"""
    
    def __init__(self, api_key: Optional[str] = None, gateway_url: str = None):
        self.api_key = api_key or os.getenv("VECTORIZED_CPT_API_KEY")
        # Use Railway environment variable or fallback to localhost
        self.gateway_url = (gateway_url or 
                           os.getenv("API_GATEWAY_URL", "http://localhost:8000")).rstrip("/")
    
    def is_configured(self) -> bool:
        """Check if API client is properly configured"""
        return self.api_key is not None
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API Gateway connection"""
        if not self.is_configured():
            return {"success": False, "error": "API key not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.gateway_url}/health")
                if response.status_code == 200:
                    return {"success": True, "status": "connected", "data": response.json()}
                else:
                    return {"success": False, "error": f"Gateway returned {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def complete_workflow(self, text: str, max_results: int = 20, pdf_base64: Optional[str] = None) -> Dict[str, Any]:
        """Execute complete medical coding workflow via API Gateway"""
        if not self.is_configured():
            return {"success": False, "error": "API key not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                payload = {
                    "text": text,
                    "max_results": max_results,
                    "include_comprehensive": True
                }
                if pdf_base64:
                    payload["pdf_base64"] = pdf_base64
                
                response = await client.post(
                    f"{self.gateway_url}/api/v1/billing/process-note",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"API returned {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract_procedures(self, text: str) -> Dict[str, Any]:
        """Test medical text processing via API Gateway"""
        if not self.is_configured():
            return {"success": False, "error": "API key not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.gateway_url}/api/v1/billing/extract-procedures",
                    json={"text": text},
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"API returned {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def search_cpt_codes(self, procedures: str, max_results: int = 20) -> Dict[str, Any]:
        """Test CPT search via API Gateway"""
        if not self.is_configured():
            return {"success": False, "error": "API key not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.gateway_url}/api/v1/billing/search-cpt",
                    json={"procedures": procedures, "max_results": max_results},
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"API returned {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def comprehensive_coding(self, primary_codes: list, medical_text: str, original_note: str) -> Dict[str, Any]:
        """Test comprehensive medical coding via API Gateway"""
        if not self.is_configured():
            return {"success": False, "error": "API key not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.gateway_url}/api/v1/billing/comprehensive-coding",
                    json={
                        "primary_codes": primary_codes,
                        "medical_text": medical_text,
                        "original_note": original_note
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"API returned {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        if not self.is_configured():
            return {"success": False, "error": "API key not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.gateway_url}/health",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"API returned {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        if not self.is_configured():
            return {"success": False, "error": "API key not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.gateway_url}/api/v1/admin/usage",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"API returned {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Request/Response Models
class WorkflowRequest(BaseModel):
    text: str
    max_results: Optional[int] = 20
    api_key: Optional[str] = None

class ServiceTestRequest(BaseModel):
    text: str
    api_key: Optional[str] = None
    max_results: Optional[int] = 20

class APIKeyUpdateRequest(BaseModel):
    api_key: str


# Initialize FastAPI app
app = FastAPI(
    title="Vectorized CPT Web Interface",
    description="Web interface for testing the microservices architecture",
    version="1.0.0"
)

# Global API client
web_client = WebAPIClient()

# Setup static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    """Main web interface - serve the HTML dashboard"""
    try:
        with open("static/web_tester.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Web Tester Not Found</h1><p>static/web_tester.html not found</p>",
            status_code=404
        )


@app.post("/api/configure")
async def configure_api_key(request: APIKeyUpdateRequest):
    """Configure API key for the web interface"""
    global web_client
    
    try:
        # Update the global web client
        web_client = WebAPIClient(request.api_key)
        
        # Test the connection
        test_result = await web_client.test_connection()
        
        if test_result["success"]:
            return {
                "success": True,
                "message": "API key configured successfully",
                "gateway_status": test_result.get("data", {})
            }
        else:
            return {
                "success": False,
                "error": f"API key test failed: {test_result['error']}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Configuration failed: {str(e)}"
        }


@app.post("/api/workflow")
async def complete_workflow(request: WorkflowRequest):
    """Execute complete medical coding workflow"""
    global web_client
    
    # Use provided API key if different from current
    client = web_client
    if request.api_key and request.api_key != web_client.api_key:
        client = WebAPIClient(request.api_key)
    
    if not client.is_configured():
        raise HTTPException(status_code=400, detail="API key not configured")
    
    result = await client.complete_workflow(
        text=request.text,
        max_results=request.max_results
    )
    
    return result


@app.post("/api/workflow/pdf")
async def complete_workflow_pdf(
    text: str = Form(""),
    max_results: int = Form(20),
    api_key: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None)
):
    """Execute complete workflow with PDF upload"""
    global web_client
    
    # Use provided API key if different from current
    client = web_client
    if api_key and api_key != web_client.api_key:
        client = WebAPIClient(api_key)
    
    if not client.is_configured():
        raise HTTPException(status_code=400, detail="API key not configured")
    
    pdf_base64 = None
    if pdf_file:
        try:
            pdf_content = await pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF processing failed: {str(e)}")
    
    result = await client.complete_workflow(
        text=text,
        max_results=max_results,
        pdf_base64=pdf_base64
    )
    
    return result


@app.post("/api/test/extract")
async def test_extract_procedures(request: ServiceTestRequest):
    """Test medical text processing service"""
    global web_client
    
    client = web_client
    if request.api_key and request.api_key != web_client.api_key:
        client = WebAPIClient(request.api_key)
    
    if not client.is_configured():
        raise HTTPException(status_code=400, detail="API key not configured")
    
    return await client.extract_procedures(request.text)


@app.post("/api/test/search")
async def test_cpt_search(request: ServiceTestRequest):
    """Test CPT search service"""
    global web_client
    
    client = web_client
    if request.api_key and request.api_key != web_client.api_key:
        client = WebAPIClient(request.api_key)
    
    if not client.is_configured():
        raise HTTPException(status_code=400, detail="API key not configured")
    
    return await client.search_cpt_codes(request.text, request.max_results)


@app.post("/api/test/coding")
async def test_comprehensive_coding(
    primary_codes: str = Form(...),  # JSON string
    medical_text: str = Form(...),
    original_note: str = Form(...),
    api_key: Optional[str] = Form(None)
):
    """Test comprehensive medical coding service"""
    global web_client
    
    client = web_client
    if api_key and api_key != web_client.api_key:
        client = WebAPIClient(api_key)
    
    if not client.is_configured():
        raise HTTPException(status_code=400, detail="API key not configured")
    
    try:
        import json
        codes = json.loads(primary_codes)
        return await client.comprehensive_coding(codes, medical_text, original_note)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid primary_codes JSON format")


@app.get("/api/health")
async def get_health_status():
    """Get comprehensive health status of all services"""
    global web_client
    
    if not web_client.is_configured():
        return {
            "success": False,
            "error": "API key not configured",
            "gateway_configured": False
        }
    
    result = await web_client.get_health_status()
    result["gateway_configured"] = True
    return result


@app.get("/api/usage")
async def get_usage_statistics():
    """Get API usage statistics"""
    global web_client
    
    if not web_client.is_configured():
        raise HTTPException(status_code=400, detail="API key not configured")
    
    return await web_client.get_usage_stats()


@app.get("/api/status")
async def get_interface_status():
    """Get web interface status"""
    global web_client
    
    status = {
        "web_interface": "operational",
        "api_configured": web_client.is_configured(),
        "timestamp": datetime.now().isoformat()
    }
    
    if web_client.is_configured():
        # Test gateway connection
        gateway_test = await web_client.test_connection()
        status["gateway_connection"] = gateway_test["success"]
        status["gateway_error"] = gateway_test.get("error") if not gateway_test["success"] else None
    else:
        status["gateway_connection"] = False
        status["gateway_error"] = "API key not configured"
    
    return status


@app.get("/api/teams")
async def list_teams():
    """Get list of available teams (requires admin API key)"""
    global web_client
    
    if not web_client.is_configured():
        raise HTTPException(status_code=400, detail="API key not configured")
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{web_client.gateway_url}/api/v1/admin/teams",
                headers={"Authorization": f"Bearer {web_client.api_key}"}
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"API returned {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/validate-key/{api_key}")
async def validate_api_key(api_key: str):
    """Validate an API key and return team information"""
    try:
        test_client = WebAPIClient(api_key, web_client.gateway_url)
        result = await test_client.test_connection()
        
        if result["success"]:
            return {
                "valid": True,
                "message": "API key is valid",
                "gateway_status": result.get("data", {})
            }
        else:
            return {
                "valid": False,
                "error": result["error"]
            }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


@app.post("/api/quick-test")
async def quick_test_endpoint(request: dict):
    """Quick test endpoint for the dashboard"""
    api_key = request.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key required")
    
    test_client = WebAPIClient(api_key, web_client.gateway_url)
    
    # Test with a simple medical note
    test_text = "Patient underwent coronary angioplasty with drug eluting stent placement"
    
    result = await test_client.complete_workflow(test_text, max_results=5)
    
    if result["success"]:
        return {
            "success": True,
            "message": "Quick test completed successfully",
            "results": result["data"]
        }
    else:
        return {
            "success": False,
            "error": result["error"]
        }


# Legacy endpoint compatibility with original web server
@app.post("/search")
async def legacy_search(request: Request):
    """Legacy search endpoint for backward compatibility"""
    try:
        data = await request.json()
        query_text = data.get('text', '').strip()
        
        if not query_text:
            return {
                'success': False,
                'error': 'Please provide a medical procedure description'
            }
        
        global web_client
        if not web_client.is_configured():
            return {
                'success': False,
                'error': 'API key not configured. Please configure an API key first.'
            }
        
        # Use CPT search service for legacy compatibility
        result = await web_client.search_cpt_codes(query_text, 20)
        
        if result["success"]:
            cpt_results = result["data"].get("results", [])
            
            # Format for legacy frontend
            formatted_results = []
            for result in cpt_results:
                formatted_results.append({
                    'cpt_code': result.get('cpt_code', 'N/A'),
                    'description': result.get('description', 'No description available'),
                    'category': result.get('category', ''),
                    'similarity': result.get('similarity_score', 0),
                    'status': result.get('status', '')
                })
            
            return {
                'success': True,
                'results': formatted_results,
                'query': query_text
            }
        else:
            return {
                'success': False,
                'error': result["error"]
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Search failed: {str(e)}'
        }


@app.get("/status")
async def legacy_status():
    """Legacy status endpoint"""
    status_result = await get_interface_status()
    
    return {
        'success': status_result["gateway_connection"],
        'vertex_ai': {
            'status': 'ready' if status_result["gateway_connection"] else 'error',
            'message': 'API Gateway connected' if status_result["gateway_connection"] else status_result.get("gateway_error", "Unknown error")
        },
        'system': 'operational' if status_result["api_configured"] else 'configuration_required'
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("🚀 STARTING VECTORIZED CPT WEB INTERFACE")
    print("=" * 80)
    
    # Check if API key is configured
    if web_client.is_configured():
        print(f"✅ API key configured: {web_client.api_key[:20]}...")
        print(f"🔗 Gateway URL: {web_client.gateway_url}")
    else:
        print("⚠️  API key not configured")
        print("💡 Set VECTORIZED_CPT_API_KEY environment variable or configure via web interface")
    
    port = int(os.environ.get('PORT', 8080))
    host = '0.0.0.0'
    
    print(f"\n🌐 Web interface starting on http://{host}:{port}")
    print(f"📱 Access the interface at: http://localhost:{port}")
    print(f"🔍 Complete workflow: http://localhost:{port}/#workflow")
    print(f"🧪 Service testing: http://localhost:{port}/#testing")
    print(f"📊 Health dashboard: http://localhost:{port}/#health")
    
    print("\n💡 Features available:")
    print("   - Complete medical coding workflow")
    print("   - Individual service testing")
    print("   - PDF document processing")
    print("   - Service health monitoring")
    print("   - API usage analytics")
    print("   - API key management")
    
    uvicorn.run(app, host=host, port=port, log_level="info")