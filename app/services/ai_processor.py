"""
AI Processor Service
Handles all AI/ML operations (Gemini, embeddings)
Ported from Firebase function logic and vertex_ai_utils.py
"""

import asyncio
import json
import aiohttp
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.billing import Billing


class AIProcessorService:
    """Handles all AI/ML operations (Gemini, embeddings)"""
    
    def __init__(self, parent_billing: 'Billing'):
        """Initialize AI processor service"""
        self.billing = parent_billing
        
        # Configuration
        self.project_id = parent_billing.config.project_id
        self.location = parent_billing.config.location
        self.embedding_model = parent_billing.config.embedding_model
        self.generative_model = parent_billing.config.generative_model
        self.task_type = parent_billing.config.vertex_task_type
        
        print(f"🤖 AI Processor Service initialized")
        print(f"   Embedding Model: {self.embedding_model}")
        print(f"   Generative Model: {self.generative_model}")
        print(f"   Task Type: {self.task_type}")
    
    async def extract_procedures_with_gemini(self, medical_text: str) -> str:
        """
        Extract procedures using Gemini
        Exact port from Firebase function logic
        """
        try:
            print("🤖 Initializing Vertex AI with project:", self.project_id, "location:", self.location)
            
            # Import VertexAI (using REST API instead of SDK for compatibility)
            prompt = self._create_medical_extraction_prompt(medical_text)
            
            print("🤖 Calling Gemini model with prompt length:", len(prompt))
            
            # Use REST API call to Gemini (similar to embedding approach)
            extracted_summary = await self._call_gemini_api(prompt)
            
            if not extracted_summary:
                print("❌ Empty summary from Gemini response")
                raise Exception("LLM failed to generate a summary.")
            
            print("✅ LLM-extracted query:", extracted_summary)
            return extracted_summary
            
        except Exception as e:
            print(f"❌ Detailed Gemini error: {e}")
            raise Exception(f"Failed to summarize text with the LLM: {str(e)}")
    
    def _create_medical_extraction_prompt(self, medical_text: str) -> str:
        """Create the exact prompt used in Firebase function"""
        return f"""You are an expert medical coding assistant. Analyze the
following medical note and extract a concise summary of the primary
procedures performed and the final postoperative diagnosis. Your
summary should be optimized for a semantic search to find a billing
code. Do not include patient history, component names, or surgical
narrative. Focus only on the performed actions and final diagnoses.

Medical Note:
"{medical_text}"

Summary:"""
    
    async def _call_gemini_api(self, prompt: str) -> str:
        """
        Call Gemini API using REST endpoint
        Similar to embedding API approach
        """
        try:
            # Get access token
            access_token = await self._get_access_token()
            
            # Construct endpoint URL
            endpoint_url = (
                f"https://{self.location}-aiplatform.googleapis.com/v1"
                f"/projects/{self.project_id}/locations/{self.location}"
                f"/publishers/google/models/{self.generative_model}:generateContent"
            )
            
            # Prepare request payload
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ],
                "generation_config": {
                    "temperature": 0.2,
                    "max_output_tokens": 1000
                }
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint_url, 
                                      headers=headers, 
                                      json=payload,
                                      timeout=aiohttp.ClientTimeout(total=60)) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
                    
                    data = await response.json()
                    
                    # Extract response text
                    candidates = data.get("candidates", [])
                    if candidates and len(candidates) > 0:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        if parts and len(parts) > 0:
                            return parts[0].get("text", "")
                    
                    raise Exception("No valid response from Gemini API")
                    
        except Exception as e:
            print(f"❌ Gemini API call failed: {e}")
            raise e
    
    async def generate_embedding_vector(self, text: str) -> List[float]:
        """
        Generate embedding using Vertex AI
        Exact port from Firebase function embedding logic
        """
        try:
            # Use the same REST API format as Firebase function for compatibility
            endpoint_url = (
                f"https://{self.location}-aiplatform.googleapis.com/v1"
                f"/projects/{self.project_id}/locations/{self.location}"
                f"/publishers/google/models/{self.embedding_model}:predict"
            )
            
            # Get access token from credentials
            access_token = await self._get_access_token()
            
            # Use same task type as database creation for compatibility
            payload = {
                "instances": [
                    {
                        "content": text,
                        "task_type": self.task_type,
                    }
                ]
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint_url,
                                      headers=headers,
                                      json=payload,
                                      timeout=aiohttp.ClientTimeout(total=60)) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
                    
                    data = await response.json()
                    prediction = data.get("predictions", [{}])[0]
                    
                    # Use same response parsing as Firebase function
                    embedding = prediction.get("embeddings", {}).get("values", [])
                    
                    print(f"✅ Generated embedding using REST API: {len(embedding)} dimensions")
                    return embedding
                    
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            raise Exception("Failed to generate text embedding.")
    
    async def _get_access_token(self) -> str:
        """
        Get access token for Google Cloud API calls
        Uses service account credentials
        """
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
            import os
            
            # Load service account credentials
            credentials_path = self.billing.config.get_credentials_path()
            
            if not os.path.exists(credentials_path):
                raise Exception(f"Service account credentials not found at: {credentials_path}")
            
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            
            # Refresh to get access token
            request = Request()
            credentials.refresh(request)
            
            return credentials.token
            
        except Exception as e:
            print(f"❌ Failed to get access token: {e}")
            raise e
    
    async def summarize_medical_note(self, text: str) -> str:
        """
        Alternative summarization method
        Can be used for different summarization needs
        """
        try:
            prompt = f"""Summarize the following medical note focusing on procedures and diagnoses:

{text}

Summary:"""
            
            return await self._call_gemini_api(prompt)
            
        except Exception as e:
            print(f"❌ Summarization failed: {e}")
            return text[:500]  # Fallback to truncated original text
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate embedding vector has correct dimensions"""
        expected_dimensions = self.billing.config.dimensions
        
        if len(embedding) != expected_dimensions:
            print(f"❌ Invalid embedding dimensions: {len(embedding)} (expected {expected_dimensions})")
            return False
        
        # Check if all values are numbers
        if not all(isinstance(x, (int, float)) for x in embedding):
            print("❌ Invalid embedding values: not all numeric")
            return False
        
        return True