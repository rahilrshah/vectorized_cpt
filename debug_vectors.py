#!/usr/bin/env python3
"""
Comprehensive debugging script for vector matching issues.
Run this to identify and fix vector database problems.
"""

import sys
import json
from config import *
from firebase_utils import init_firestore
from vertex_ai_utils import get_vertex_embeddings
import numpy as np

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def debug_firestore_structure():
    """Check the structure of documents in Firestore"""
    print("=== Debugging Firestore Structure ===")
    
    db = init_firestore(cred_path)
    if not db:
        print("✗ Failed to connect to Firestore")
        return False
    
    try:
        # Get a sample document to check structure
        docs = db.collection(collection_name).limit(1).stream()
        doc_data = None
        
        for doc in docs:
            doc_data = doc.to_dict()
            break
        
        if not doc_data:
            print("✗ No documents found in collection:", collection_name)
            return False
        
        print("✓ Connected to Firestore collection:", collection_name)
        print("Document fields found:")
        for key in doc_data.keys():
            if key == 'vector':
                vector_len = len(doc_data[key]) if isinstance(doc_data[key], list) else 'Not a list'
                print(f"  - {key}: {vector_len} dimensions")
            else:
                value_preview = str(doc_data[key])[:50] + "..." if len(str(doc_data[key])) > 50 else str(doc_data[key])
                print(f"  - {key}: {value_preview}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking Firestore: {e}")
        return False

def test_vector_generation():
    """Test vector generation with current config"""
    print("\n=== Testing Vector Generation ===")
    
    test_description = "Open repair of infrarenal aortic aneurysm"
    print(f"Test description: '{test_description}'")
    print(f"Using task type: {vertex_task_type}")
    
    try:
        vectors = get_vertex_embeddings(
            [test_description], 
            vertex_project, 
            vertex_location, 
            vertex_model, 
            vertex_task_type,
            batch_size=1
        )
        
        if vectors and len(vectors) > 0:
            vector = vectors[0]
            print(f"✓ Generated vector with {len(vector)} dimensions")
            
            # Check for expected dimension (768 for text-embedding-004)
            if len(vector) == 768:
                print("✓ Vector dimension is correct (768)")
            else:
                print(f"⚠ Unexpected vector dimension: {len(vector)} (expected 768)")
            
            return vector
        else:
            print("✗ Failed to generate vector")
            return None
            
    except Exception as e:
        print(f"✗ Error generating vector: {e}")
        return None

def simulate_firestore_query(test_vector):
    """Simulate the vector search that would happen in the Cloud Function"""
    print("\n=== Simulating Vector Search ===")
    
    if not test_vector:
        print("✗ No test vector provided")
        return False
    
    db = init_firestore(cred_path)
    if not db:
        print("✗ Failed to connect to Firestore")
        return False
    
    try:
        print("Attempting Firestore vector query...")
        print(f"Collection: {collection_name}")
        print(f"Vector field: vector")
        print(f"Vector dimensions: {len(test_vector)}")
        
        # Note: This is a simulation since we can't easily test findNearest from Python
        # The actual query happens in the Cloud Function
        
        # Instead, let's fetch a few documents and manually check similarity
        docs = db.collection(collection_name).limit(3).stream()
        found_docs = []
        
        for doc in docs:
            doc_data = doc.to_dict()
            found_docs.append(doc_data)
        
        if found_docs:
            print(f"✓ Found {len(found_docs)} documents in collection")
            
            # Check similarity with first document
            first_doc = found_docs[0]
            if 'vector' in first_doc and isinstance(first_doc['vector'], list):
                stored_vector = first_doc['vector']
                if len(stored_vector) == len(test_vector):
                    similarity = cosine_similarity(np.array(test_vector), np.array(stored_vector))
                    print(f"Manual similarity check with first doc: {similarity:.4f}")
                    
                    # Show document details
                    description = first_doc.get('Descriptions', 'No description')
                    cpt_code = first_doc.get('cpt_code', first_doc.get('CPT Codes', 'No code'))
                    print(f"Document CPT Code: {cpt_code}")
                    print(f"Document Description: {description[:100]}...")
                    
                else:
                    print(f"✗ Vector dimension mismatch: stored={len(stored_vector)}, query={len(test_vector)}")
            else:
                print("✗ Document missing 'vector' field or not a list")
        else:
            print("✗ No documents found in collection")
            
        return True
        
    except Exception as e:
        print(f"✗ Error in vector search simulation: {e}")
        return False

def main():
    print("Vector Debugging Script")
    print("=" * 50)
    
    # Step 1: Check Firestore structure
    firestore_ok = debug_firestore_structure()
    
    # Step 2: Test vector generation
    test_vector = test_vector_generation()
    
    # Step 3: Simulate vector search
    if firestore_ok and test_vector:
        simulate_firestore_query(test_vector)
    
    print("\n=== FIXES APPLIED ===")
    print("✓ Changed query task type from RETRIEVAL_QUERY to RETRIEVAL_DOCUMENT")
    print("✓ Ensured consistent field naming (cpt_code)")
    print("✓ Built TypeScript functions")
    
    print("\n=== NEXT STEPS ===")
    print("1. Deploy the updated functions: firebase deploy --only functions")
    print("2. Test with a PDF to verify the fix works")
    print("3. If still no matches, check vector database was built with RETRIEVAL_DOCUMENT")

if __name__ == "__main__":
    main()