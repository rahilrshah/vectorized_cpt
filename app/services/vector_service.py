"""
Vector Service
Handles vector operations and similarity calculations
Based on existing vertex_ai_utils.py and vector processing logic
"""

import asyncio
import numpy as np
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from app.billing import Billing


class VectorService:
    """Handles vector operations and similarity calculations"""
    
    def __init__(self, parent_billing: 'Billing'):
        """Initialize vector service"""
        self.billing = parent_billing
        
        # Configuration
        self.dimensions = parent_billing.config.dimensions
        self.project_id = parent_billing.config.project_id
        self.location = parent_billing.config.location
        self.embedding_model = parent_billing.config.embedding_model
        
        print(f"🧮 Vector Service initialized")
        print(f"   Dimensions: {self.dimensions}")
        print(f"   Embedding Model: {self.embedding_model}")
    
    async def create_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Create embedding vector
        Delegates to AI processor for consistency
        """
        try:
            # Use the AI processor's embedding generation method
            embedding = await self.billing.ai_processor.generate_embedding_vector(text)
            
            # Validate embedding
            if not self.validate_vector_dimensions(embedding):
                raise ValueError(f"Invalid embedding dimensions: {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            print(f"❌ Embedding creation failed: {e}")
            raise e
    
    def calculate_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        """
        try:
            # Validate inputs
            if len(vector1) != len(vector2):
                raise ValueError(f"Vector dimension mismatch: {len(vector1)} vs {len(vector2)}")
            
            if len(vector1) == 0:
                return 0.0
            
            # Convert to numpy arrays for efficient computation
            v1 = np.array(vector1, dtype=np.float32)
            v2 = np.array(vector2, dtype=np.float32)
            
            # Calculate cosine similarity
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            # Avoid division by zero
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            
            similarity = dot_product / (norm_v1 * norm_v2)
            
            # Clamp to [0, 1] range
            similarity = max(0.0, min(1.0, similarity))
            
            return float(similarity)
            
        except Exception as e:
            print(f"❌ Similarity calculation failed: {e}")
            return 0.0
    
    def calculate_euclidean_distance(self, vector1: List[float], vector2: List[float]) -> float:
        """
        Calculate Euclidean distance between two vectors
        """
        try:
            if len(vector1) != len(vector2):
                raise ValueError(f"Vector dimension mismatch: {len(vector1)} vs {len(vector2)}")
            
            # Convert to numpy arrays
            v1 = np.array(vector1, dtype=np.float32)
            v2 = np.array(vector2, dtype=np.float32)
            
            # Calculate Euclidean distance
            distance = np.linalg.norm(v1 - v2)
            
            return float(distance)
            
        except Exception as e:
            print(f"❌ Distance calculation failed: {e}")
            return float('inf')
    
    def validate_vector_dimensions(self, vector: List[float]) -> bool:
        """Validate vector has correct dimensions"""
        if not isinstance(vector, list):
            print(f"❌ Vector is not a list: {type(vector)}")
            return False
        
        if len(vector) != self.dimensions:
            print(f"❌ Invalid vector dimensions: {len(vector)} (expected {self.dimensions})")
            return False
        
        # Check if all values are numbers
        if not all(isinstance(x, (int, float)) for x in vector):
            print("❌ Invalid vector values: not all numeric")
            return False
        
        # Check for NaN or infinite values
        if any(np.isnan(x) or np.isinf(x) for x in vector):
            print("❌ Invalid vector values: contains NaN or infinity")
            return False
        
        return True
    
    def normalize_vector(self, vector: List[float]) -> List[float]:
        """
        Normalize vector to unit length
        """
        try:
            v = np.array(vector, dtype=np.float32)
            norm = np.linalg.norm(v)
            
            if norm == 0:
                return vector  # Return original if zero vector
            
            normalized = v / norm
            return normalized.tolist()
            
        except Exception as e:
            print(f"❌ Vector normalization failed: {e}")
            return vector
    
    def batch_similarity_search(self, query_vector: List[float], 
                               database_vectors: List[List[float]],
                               top_k: int = 20) -> List[Tuple[int, float]]:
        """
        Perform batch similarity search against multiple vectors
        Returns list of (index, similarity) tuples sorted by similarity
        """
        try:
            if not self.validate_vector_dimensions(query_vector):
                raise ValueError("Invalid query vector")
            
            similarities = []
            
            for i, db_vector in enumerate(database_vectors):
                if self.validate_vector_dimensions(db_vector):
                    similarity = self.calculate_similarity(query_vector, db_vector)
                    similarities.append((i, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top k results
            return similarities[:top_k]
            
        except Exception as e:
            print(f"❌ Batch similarity search failed: {e}")
            return []
    
    def vector_statistics(self, vectors: List[List[float]]) -> Dict:
        """
        Calculate statistics for a collection of vectors
        """
        try:
            if not vectors:
                return {"error": "No vectors provided"}
            
            # Convert to numpy array
            vector_array = np.array(vectors, dtype=np.float32)
            
            stats = {
                "count": len(vectors),
                "dimensions": len(vectors[0]) if vectors else 0,
                "mean_norm": float(np.mean(np.linalg.norm(vector_array, axis=1))),
                "std_norm": float(np.std(np.linalg.norm(vector_array, axis=1))),
                "min_norm": float(np.min(np.linalg.norm(vector_array, axis=1))),
                "max_norm": float(np.max(np.linalg.norm(vector_array, axis=1))),
                "mean_values": np.mean(vector_array, axis=0).tolist()[:5],  # First 5 dimensions
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Vector statistics calculation failed: {e}")
            return {"error": str(e)}
    
    def find_similar_vectors(self, query_vector: List[float],
                           database_vectors: List[Dict],
                           similarity_threshold: float = 0.7,
                           top_k: int = 20) -> List[Dict]:
        """
        Find similar vectors in database with metadata
        Each database_vector should be a dict with 'vector' and metadata fields
        """
        try:
            if not self.validate_vector_dimensions(query_vector):
                raise ValueError("Invalid query vector")
            
            results = []
            
            for i, item in enumerate(database_vectors):
                if 'vector' not in item:
                    continue
                
                db_vector = item['vector']
                if not self.validate_vector_dimensions(db_vector):
                    continue
                
                similarity = self.calculate_similarity(query_vector, db_vector)
                
                if similarity >= similarity_threshold:
                    result = {
                        **item,  # Include all metadata
                        'similarity': similarity,
                        'distance': 1.0 - similarity,
                        'index': i
                    }
                    results.append(result)
            
            # Sort by similarity (descending)
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            print(f"❌ Similar vector search failed: {e}")
            return []
    
    async def create_batch_embeddings(self, texts: List[str], 
                                    batch_size: int = 32) -> List[List[float]]:
        """
        Create embeddings for multiple texts in batches
        """
        try:
            embeddings = []
            total_texts = len(texts)
            
            print(f"🧮 Creating embeddings for {total_texts} texts in batches of {batch_size}")
            
            for i in range(0, total_texts, batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_texts + batch_size - 1) // batch_size
                
                print(f"   Processing batch {batch_num}/{total_batches} ({len(batch_texts)} texts)...")
                
                # Create embeddings for this batch
                batch_embeddings = []
                for text in batch_texts:
                    embedding = await self.create_embedding(text)
                    batch_embeddings.append(embedding)
                
                embeddings.extend(batch_embeddings)
                
                # Small delay to avoid rate limiting
                if batch_num < total_batches:
                    await asyncio.sleep(0.5)
            
            print(f"✅ Created {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            print(f"❌ Batch embedding creation failed: {e}")
            return []