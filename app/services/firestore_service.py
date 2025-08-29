"""
Firestore Service
Handles all Firestore database operations
Consolidated from existing firebase_utils.py and Firebase function logic
"""

import asyncio
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from google.cloud import firestore

if TYPE_CHECKING:
    from app.billing import Billing


class FirestoreService:
    """Handles all Firestore database operations"""
    
    def __init__(self, parent_billing: 'Billing'):
        """Initialize Firestore service"""
        self.billing = parent_billing
        
        # Configuration
        self.collection_name = parent_billing.config.collection_name
        self.vector_field = parent_billing.config.firestore_vector_field
        
        # Initialize Firestore client
        self._initialize_firestore()
        
        print(f"🗄️ Firestore Service initialized")
        print(f"   Collection: {self.collection_name}")
        print(f"   Vector Field: {self.vector_field}")
    
    def _initialize_firestore(self):
        """Initialize Firestore client with credentials"""
        try:
            import os
            
            # Set credentials path for Firestore
            credentials_path = self.billing.config.get_credentials_path()
            if os.path.exists(credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            # Initialize Firestore client
            self.db = firestore.Client(project=self.billing.config.project_id)
            self.collection = self.db.collection(self.collection_name)
            
            print("✅ Firestore client initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize Firestore client: {e}")
            raise e
    
    def get_collection_ref(self):
        """Get collection reference"""
        return self.collection
    
    async def get_sample_documents(self, limit: int = 5) -> List[Dict]:
        """
        Get sample documents from collection
        Used for debugging and health checks
        """
        try:
            # Convert Firestore query to async
            docs = self.collection.limit(limit).stream()
            
            sample_docs = []
            for doc in docs:
                doc_data = doc.to_dict()
                sample_docs.append(doc_data)
            
            print(f"📄 Retrieved {len(sample_docs)} sample documents")
            return sample_docs
            
        except Exception as e:
            print(f"❌ Error getting sample documents: {e}")
            return []
    
    async def get_all_documents(self) -> List[Dict]:
        """
        Get all documents from collection
        Used for keyword-based search fallback
        """
        try:
            print(f"📄 Retrieving all documents from {self.collection_name}")
            
            # Stream all documents
            docs = self.collection.stream()
            
            all_docs = []
            count = 0
            for doc in docs:
                doc_data = doc.to_dict()
                all_docs.append(doc_data)
                count += 1
                
                # Print progress every 1000 documents
                if count % 1000 == 0:
                    print(f"   Loaded {count} documents...")
            
            print(f"✅ Retrieved {len(all_docs)} total documents")
            return all_docs
            
        except Exception as e:
            print(f"❌ Error getting all documents: {e}")
            return []
    
    async def vector_search(self, embedding: List[float], limit: int = 20) -> List[Dict]:
        """
        Perform vector search in Firestore
        Note: Firestore vector search is currently non-functional in this setup
        """
        try:
            print(f"🔍 Attempting Firestore vector search...")
            print(f"   Vector length: {len(embedding)}")
            print(f"   Limit: {limit}")
            
            # TODO: Implement actual vector search when Firestore supports it properly
            # For now, this will return empty and fall back to keyword search
            
            print("⚠️ Vector search not implemented - falling back to keyword search")
            return []
            
        except Exception as e:
            print(f"❌ Vector search error: {e}")
            return []
    
    async def keyword_search(self, keywords: List[str], limit: int = 20) -> List[Dict]:
        """
        Keyword-based search in document descriptions
        Fallback method when vector search fails
        """
        try:
            print(f"🔍 Performing keyword search for: {keywords}")
            
            results = []
            
            # Get all documents
            all_docs = await self.get_all_documents()
            
            for doc in all_docs:
                description = doc.get("Descriptions", "").lower()
                
                # Count keyword matches
                matches = sum(1 for keyword in keywords if keyword.lower() in description)
                
                if matches > 0:
                    # Calculate similarity score
                    similarity = min(0.9, matches / len(keywords))
                    
                    result = {
                        **doc,  # Include all original fields
                        "similarity": similarity,
                        "matches": matches,
                        "match_keywords": [k for k in keywords if k.lower() in description]
                    }
                    results.append(result)
            
            # Sort by matches and similarity
            results.sort(key=lambda x: (x["matches"], x["similarity"]), reverse=True)
            
            print(f"✅ Keyword search found {len(results)} matches")
            return results[:limit]
            
        except Exception as e:
            print(f"❌ Keyword search error: {e}")
            return []
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics for health checks
        """
        try:
            # Get sample documents to check collection status
            sample_docs = await self.get_sample_documents(10)
            
            stats = {
                "collection_name": self.collection_name,
                "document_count": len(sample_docs),
                "sample_documents": len(sample_docs),
                "has_vector_field": False,
                "vector_dimensions": 0
            }
            
            # Check if documents have vector field
            if sample_docs:
                first_doc = sample_docs[0]
                if self.vector_field in first_doc:
                    stats["has_vector_field"] = True
                    vector = first_doc[self.vector_field]
                    if isinstance(vector, list):
                        stats["vector_dimensions"] = len(vector)
                
                # Add sample field information
                stats["sample_fields"] = list(first_doc.keys())
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting collection stats: {e}")
            return {
                "collection_name": self.collection_name,
                "error": str(e),
                "document_count": 0
            }
    
    async def add_document(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """
        Add a document to the collection
        Used for data uploads or updates
        """
        try:
            doc_ref = self.collection.document(doc_id)
            doc_ref.set(data)
            
            print(f"✅ Added document: {doc_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding document {doc_id}: {e}")
            return False
    
    async def update_document(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a document in the collection
        """
        try:
            doc_ref = self.collection.document(doc_id)
            doc_ref.update(updates)
            
            print(f"✅ Updated document: {doc_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating document {doc_id}: {e}")
            return False
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the collection
        """
        try:
            doc_ref = self.collection.document(doc_id)
            doc_ref.delete()
            
            print(f"✅ Deleted document: {doc_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting document {doc_id}: {e}")
            return False
    
    async def batch_add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Add multiple documents in batch
        Returns number of successfully added documents
        """
        try:
            batch = self.db.batch()
            success_count = 0
            
            for i, doc_data in enumerate(documents):
                doc_id = doc_data.get('id', f'doc_{i}')
                doc_ref = self.collection.document(doc_id)
                batch.set(doc_ref, doc_data)
                success_count += 1
                
                # Commit batch every 500 documents (Firestore limit)
                if success_count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
                    print(f"   Committed batch: {success_count} documents")
            
            # Commit remaining documents
            if success_count % 500 != 0:
                batch.commit()
            
            print(f"✅ Batch added {success_count} documents")
            return success_count
            
        except Exception as e:
            print(f"❌ Batch add error: {e}")
            return 0
    
    def close(self):
        """Close Firestore client connection"""
        try:
            # Firestore client doesn't need explicit closing
            print("🔄 Firestore client closed")
        except Exception as e:
            print(f"⚠️ Error closing Firestore client: {e}")