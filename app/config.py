"""
Configuration management for all billing operations
Consolidates all existing config values from config.py and vertex_ai_config.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class BillingConfig:
    """Configuration management for all billing operations"""
    
    def __init__(self):
        """Initialize configuration from existing config files"""
        
        # --- Configuration from config.py ---
        self.default_csv_path = 'CPT_Codes_Raw.csv'
        self.vector_path = 'vectorized.npz'
        self.description_column = 'Descriptions'
        self.collection_name = 'Vectorized_CPT_Test'
        self.cred_path = 'cpt-code-vectorized-dataset-firebase-adminsdk-fbsvc-2c5f693340.json'
        
        # --- Vertex AI config from config.py ---
        self.vertex_project = 'cpt-code-vectorized-dataset'
        self.vertex_location = 'us-central1'
        self.vertex_model = 'text-embedding-004'
        self.vertex_batch_size = 32
        self.vertex_task_type = 'RETRIEVAL_DOCUMENT'
        
        # --- Firebase Function Config (from functions/src/index.ts) ---
        self.project_id = "cpt-code-vectorized-dataset"
        self.location = "us-central1"
        self.embedding_model = "text-embedding-004"
        self.generative_model = "gemini-2.0-flash-exp"
        self.firestore_vector_field = "vector"
        
        # --- Load vertex_ai_config.json ---
        self.vertex_config = self._load_vertex_config()
        
        # --- Derived configuration ---
        self.dimensions = 768  # Standard for text-embedding-004
        self.similarity_threshold = 0.70  # From Firebase function
        self.max_results_default = 20
        
        # --- Uppercase aliases for microservices compatibility ---
        self.PROJECT_ID = self.project_id
        self.LOCATION = self.location
        self.COLLECTION_NAME = self.collection_name
        self.EMBEDDING_MODEL = self.embedding_model
        self.GENERATIVE_MODEL = self.generative_model
        self.DIMENSIONS = self.dimensions
        self.FIRESTORE_VECTOR_FIELD = self.firestore_vector_field
        
        print("📋 Configuration loaded successfully")
        print(f"   Project: {self.project_id}")
        print(f"   Location: {self.location}")
        print(f"   Collection: {self.collection_name}")
        print(f"   Embedding Model: {self.embedding_model}")
        print(f"   Generative Model: {self.generative_model}")
    
    def _load_vertex_config(self) -> Dict:
        """Load vertex_ai_config.json if it exists"""
        try:
            config_path = Path(__file__).parent.parent / "vertex_ai_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                # Return default vertex config if file doesn't exist
                return {
                    "project_id": self.vertex_project,
                    "location": self.vertex_location,
                    "dimensions": 768,
                    "distance_measure": "COSINE_DISTANCE"
                }
        except Exception as e:
            print(f"⚠️ Could not load vertex_ai_config.json: {e}")
            return {}
    
    def get_credentials_path(self) -> str:
        """Get the path to Firebase credentials"""
        # Check if credentials file exists in current directory
        if os.path.exists(self.cred_path):
            return self.cred_path
        
        # Check in parent directory
        parent_cred_path = Path(__file__).parent.parent / self.cred_path
        if parent_cred_path.exists():
            return str(parent_cred_path)
        
        # Return original path (may trigger error if file doesn't exist)
        return self.cred_path
    
    def get_embedding_endpoint_url(self) -> str:
        """Get the Vertex AI embedding endpoint URL"""
        return (
            f"https://{self.location}-aiplatform.googleapis.com/v1"
            f"/projects/{self.project_id}/locations/{self.location}"
            f"/publishers/google/models/{self.embedding_model}:predict"
        )
    
    def get_generative_endpoint_url(self) -> str:
        """Get the Vertex AI generative model endpoint URL (if needed)"""
        return (
            f"https://{self.location}-aiplatform.googleapis.com/v1"
            f"/projects/{self.project_id}/locations/{self.location}"
            f"/publishers/google/models/{self.generative_model}:generateContent"
        )
    
    def validate_config(self) -> bool:
        """Validate that all required configuration is present"""
        required_fields = [
            'project_id', 'location', 'collection_name',
            'embedding_model', 'generative_model'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(self, field, None):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required configuration fields: {missing_fields}")
            return False
        
        print("✅ Configuration validation passed")
        return True
    
    def to_dict(self) -> Dict:
        """Return configuration as dictionary"""
        return {
            'project_id': self.project_id,
            'location': self.location,
            'collection_name': self.collection_name,
            'embedding_model': self.embedding_model,
            'generative_model': self.generative_model,
            'dimensions': self.dimensions,
            'similarity_threshold': self.similarity_threshold,
            'vertex_batch_size': self.vertex_batch_size,
            'vertex_task_type': self.vertex_task_type
        }