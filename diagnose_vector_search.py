#!/usr/bin/env python3
"""
Comprehensive Firestore Vector Search Diagnostic Tool
"""

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
import sys
import traceback

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
        print("🔄 Using existing Firebase app")
    except ValueError:
        # Initialize new app
        cred = credentials.Certificate('cpt-code-vectorized-dataset-firebase-adminsdk-fbsvc-2c5f693340.json')
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized")

def test_exact_vector_match():
    """Test vector search with exact vector match"""
    print('\n🧪 EXACT VECTOR MATCH TEST')
    print('='*50)
    
    db = firestore.client()
    collection_ref = db.collection('Vectorized_CPT_Test')
    
    # Get a test document
    test_doc = collection_ref.limit(1).get()[0]
    test_data = test_doc.to_dict()
    test_vector = test_data['vector']
    
    print(f'🎯 Testing with document: {test_doc.id}')
    print(f'   CPT Code: {test_data.get("CPT Codes")}')
    print(f'   Description: {test_data.get("Descriptions", "")[:100]}...')
    print(f'   Vector dimensions: {len(test_vector)}')
    
    try:
        # Perform vector search
        print(f'\n🔍 Performing vector search...')
        
        vector_query = collection_ref.find_nearest(
            vector_field='vector',
            query_vector=test_vector,
            distance_measure=DistanceMeasure.COSINE,
            limit=5
        )
        
        results = vector_query.get()
        
        print(f'📊 Results found: {len(results)}')
        
        if len(results) > 0:
            print('\n✅ SUCCESS - Vector search is working!')
            for i, doc in enumerate(results):
                data = doc.to_dict()
                print(f'  {i+1}. CPT {data.get("CPT Codes")}: {data.get("Descriptions", "")[:60]}...')
            return True
        else:
            print('\n❌ ZERO RESULTS - Even exact vector match failed!')
            return False
            
    except Exception as e:
        print(f'\n❌ Vector search error: {e}')
        print(f'Error type: {type(e)}')
        traceback.print_exc()
        return False

def test_different_distance_measures():
    """Test vector search with different distance measures"""
    print('\n📐 TESTING DIFFERENT DISTANCE MEASURES')
    print('='*50)
    
    db = firestore.client()
    collection_ref = db.collection('Vectorized_CPT_Test')
    
    # Get a test vector
    test_doc = collection_ref.limit(1).get()[0]
    test_vector = test_doc.to_dict()['vector']
    
    distance_measures = [
        (DistanceMeasure.EUCLIDEAN, "EUCLIDEAN"),
        (DistanceMeasure.COSINE, "COSINE"),
        (DistanceMeasure.DOT_PRODUCT, "DOT_PRODUCT")
    ]
    
    for measure, name in distance_measures:
        try:
            print(f'\n🔍 Testing {name} distance...')
            
            vector_query = collection_ref.find_nearest(
                vector_field='vector',
                query_vector=test_vector,
                distance_measure=measure,
                limit=3
            )
            
            results = vector_query.get()
            print(f'   Results: {len(results)}')
            
        except Exception as e:
            print(f'   ❌ Error with {name}: {e}')

def test_simple_similarity():
    """Test with very different vector to see if any matches occur"""
    print('\n🎲 TESTING WITH RANDOM/SIMPLE VECTOR')
    print('='*50)
    
    db = firestore.client()
    collection_ref = db.collection('Vectorized_CPT_Test')
    
    # Create a simple test vector (all ones, normalized)
    import math
    simple_vector = [1.0] * 768
    # Normalize it
    magnitude = math.sqrt(sum(x*x for x in simple_vector))
    simple_vector = [x/magnitude for x in simple_vector]
    
    print(f'🔍 Testing with normalized vector of ones...')
    print(f'   Vector sample: [{simple_vector[0]:.6f}, {simple_vector[1]:.6f}, ...]')
    
    try:
        vector_query = collection_ref.find_nearest(
            vector_field='vector',
            query_vector=simple_vector,
            distance_measure=DistanceMeasure.COSINE,
            limit=5
        )
        
        results = vector_query.get()
        print(f'📊 Results found: {len(results)}')
        
        if len(results) > 0:
            for i, doc in enumerate(results):
                data = doc.to_dict()
                print(f'  {i+1}. CPT {data.get("CPT Codes")}: {data.get("Descriptions", "")[:60]}...')
        
    except Exception as e:
        print(f'❌ Error: {e}')

def diagnose_vector_search_infrastructure():
    """Check if vector search is properly configured"""
    print('\n🏗️  VECTOR SEARCH INFRASTRUCTURE CHECK')
    print('='*50)
    
    db = firestore.client()
    collection_ref = db.collection('Vectorized_CPT_Test')
    
    try:
        # Test basic collection access
        docs = collection_ref.limit(1).get()
        print(f'✅ Basic collection access: {len(docs)} documents')
        
        # Check if we can access vector field
        if docs:
            data = docs[0].to_dict()
            if 'vector' in data:
                print(f'✅ Vector field accessible: {len(data["vector"])} dimensions')
            else:
                print(f'❌ Vector field not found in document')
        
        # Try to list available fields
        sample_doc = docs[0].to_dict()
        print(f'📋 Available fields: {list(sample_doc.keys())}')
        
    except Exception as e:
        print(f'❌ Infrastructure check failed: {e}')

if __name__ == '__main__':
    print("🚀 COMPREHENSIVE FIRESTORE VECTOR SEARCH DIAGNOSTIC")
    print("="*60)
    
    try:
        initialize_firebase()
        
        # Run all diagnostic tests
        success = test_exact_vector_match()
        
        if not success:
            test_different_distance_measures()
            test_simple_similarity()
            diagnose_vector_search_infrastructure()
        
        print(f"\n🏁 DIAGNOSTIC COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        traceback.print_exc()