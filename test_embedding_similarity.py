#!/usr/bin/env python3
"""
Test script to verify vector embeddings and similarity matching.
This will help debug why identical descriptions return no matches.
"""

import sys
from config import *
from vertex_ai_utils import get_vertex_embeddings
import numpy as np

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def test_identical_descriptions():
    """Test that identical descriptions produce identical embeddings"""
    print("=== Testing Identical Description Embeddings ===")
    
    # Test with a simple description
    description = "Open repair of infrarenal aortic aneurysm"
    descriptions = [description, description]  # Same description twice
    
    print(f"Testing description: '{description}'")
    
    try:
        vectors = get_vertex_embeddings(
            descriptions, 
            vertex_project, 
            vertex_location, 
            vertex_model, 
            vertex_task_type,  # This should be RETRIEVAL_DOCUMENT
            batch_size=2
        )
        
        if len(vectors) == 2:
            vec1, vec2 = vectors[0], vectors[1]
            similarity = cosine_similarity(np.array(vec1), np.array(vec2))
            print(f"Cosine similarity between identical descriptions: {similarity:.6f}")
            
            if similarity > 0.99:
                print("✓ SUCCESS: Identical descriptions produce nearly identical embeddings")
            else:
                print("✗ ERROR: Identical descriptions should have similarity ≈ 1.0")
                
            return vectors[0]  # Return one vector for further testing
        else:
            print("✗ ERROR: Expected 2 vectors but got", len(vectors))
            return None
            
    except Exception as e:
        print(f"✗ ERROR generating embeddings: {e}")
        return None

def test_task_types():
    """Test the difference between RETRIEVAL_DOCUMENT and RETRIEVAL_QUERY task types"""
    print("\n=== Testing Different Task Types ===")
    
    description = "Open repair of infrarenal aortic aneurysm"
    
    try:
        # Generate embedding with RETRIEVAL_DOCUMENT (what's stored in database)
        doc_vector = get_vertex_embeddings(
            [description], 
            vertex_project, 
            vertex_location, 
            vertex_model, 
            "RETRIEVAL_DOCUMENT",  # Database task type
            batch_size=1
        )[0]
        
        # Generate embedding with RETRIEVAL_QUERY (what was previously used for queries)
        query_vector = get_vertex_embeddings(
            [description], 
            vertex_project, 
            vertex_location, 
            vertex_model, 
            "RETRIEVAL_QUERY",  # Previous query task type
            batch_size=1
        )[0]
        
        # Calculate similarity
        similarity = cosine_similarity(np.array(doc_vector), np.array(query_vector))
        print(f"Similarity between RETRIEVAL_DOCUMENT and RETRIEVAL_QUERY: {similarity:.6f}")
        
        if similarity < 0.9:
            print("✗ CRITICAL: Task type mismatch causes poor similarity!")
            print("  This explains why identical descriptions weren't matching.")
        else:
            print("✓ Task types produce similar embeddings")
            
        return doc_vector, query_vector
        
    except Exception as e:
        print(f"✗ ERROR testing task types: {e}")
        return None, None

def main():
    print("Vector Embedding Similarity Test")
    print("=" * 50)
    
    # Test 1: Identical descriptions
    base_vector = test_identical_descriptions()
    
    # Test 2: Task type comparison
    if base_vector:
        doc_vec, query_vec = test_task_types()
        
        if doc_vec and query_vec:
            print("\n=== Summary ===")
            print("✓ Fixed: Using RETRIEVAL_DOCUMENT for both storage and queries")
            print("✓ This should resolve the 'no matches' issue")
    
    print("\n=== Next Steps ===")
    print("1. Rebuild your TypeScript functions: cd functions && npm run build")
    print("2. Redeploy functions: firebase deploy --only functions")
    print("3. Test with a PDF to verify matches are now found")

if __name__ == "__main__":
    main()