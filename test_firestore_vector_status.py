#!/usr/bin/env python3

import sys
from firebase_utils import init_firestore
from config import cred_path, collection_name
from google.cloud.firestore_v1.base_query import DistanceMeasure

def check_firestore_vector_status():
    """Check the status of Firestore vector search functionality"""
    print("=" * 80)
    print("FIRESTORE VECTOR SEARCH STATUS CHECK")
    print("=" * 80)
    
    # Initialize
    db = init_firestore(cred_path)
    if not db:
        print("❌ Failed to initialize Firestore")
        return False
        
    collection_ref = db.collection(collection_name)
    
    # 1. Check basic collection access
    print("\n1. BASIC COLLECTION ACCESS")
    try:
        doc_count = len(list(collection_ref.limit(10).stream()))
        print(f"✅ Collection accessible: {doc_count} documents found")
    except Exception as e:
        print(f"❌ Collection access failed: {e}")
        return False
    
    # 2. Check if find_nearest method exists and works
    print("\n2. VECTOR SEARCH METHOD AVAILABILITY")
    if not hasattr(collection_ref, 'find_nearest'):
        print("❌ find_nearest method not available")
        print("   This indicates Firestore vector search is not enabled")
        return False
    else:
        print("✅ find_nearest method is available")
    
    # 3. Check sample document structure
    print("\n3. DOCUMENT STRUCTURE VALIDATION")
    sample_doc = list(collection_ref.limit(1).stream())[0]
    doc_data = sample_doc.to_dict()
    
    if 'vector' not in doc_data:
        print("❌ No 'vector' field found in documents")
        return False
    
    vector_data = doc_data['vector']
    if not isinstance(vector_data, list) or len(vector_data) != 768:
        print(f"❌ Invalid vector field: type={type(vector_data)}, len={len(vector_data) if isinstance(vector_data, list) else 'N/A'}")
        return False
        
    print(f"✅ Vector field valid: 768-dimensional list")
    
    # 4. Test vector query creation (don't execute yet)
    print("\n4. VECTOR QUERY CREATION TEST")
    try:
        test_vector = vector_data  # Use the exact same vector
        query = collection_ref.find_nearest(
            vector_field='vector',
            query_vector=test_vector,
            limit=1,
            distance_measure=DistanceMeasure.COSINE
        )
        print("✅ Vector query object created successfully")
        
        # 5. Test query execution
        print("\n5. VECTOR QUERY EXECUTION TEST")
        results = list(query.get())
        print(f"✅ Query executed without error")
        print(f"📊 Results returned: {len(results)}")
        
        if len(results) == 0:
            print("⚠️  Query returned 0 results")
            print("   This suggests the vector index is not working properly")
            
            # Try to understand why
            print("\n6. TROUBLESHOOTING ZERO RESULTS")
            
            # Check if this might be a indexing issue
            print("   Possible causes:")
            print("   a) Vector index is still building")
            print("   b) Vector index is not properly configured") 
            print("   c) Vector data type mismatch")
            print("   d) Distance measure not supported")
            
            # Try with different parameters
            print("\n   Testing different distance measures...")
            for dm in [DistanceMeasure.EUCLIDEAN, DistanceMeasure.DOT_PRODUCT]:
                try:
                    alt_query = collection_ref.find_nearest(
                        vector_field='vector',
                        query_vector=test_vector,
                        limit=1,
                        distance_measure=dm
                    )
                    alt_results = list(alt_query.get())
                    print(f"   {dm}: {len(alt_results)} results")
                    if len(alt_results) > 0:
                        print(f"   🎉 {dm} works! This suggests COSINE distance has an issue")
                        return True
                except Exception as e:
                    print(f"   {dm}: Failed - {e}")
            
            # Try with a different limit
            print(f"\n   Testing with different limits...")
            for limit in [1, 5, 10]:
                try:
                    limit_query = collection_ref.find_nearest(
                        vector_field='vector',
                        query_vector=test_vector,
                        limit=limit,
                        distance_measure=DistanceMeasure.COSINE
                    )
                    limit_results = list(limit_query.get())
                    print(f"   Limit {limit}: {len(limit_results)} results")
                except Exception as e:
                    print(f"   Limit {limit}: Failed - {e}")
            
            return False
            
        else:
            print("🎉 Vector search is working!")
            
            # Show the results
            for i, result_doc in enumerate(results):
                result_data = result_doc.to_dict()
                cpt = result_data.get('CPT Codes', 'N/A')
                desc = result_data.get('Descriptions', 'N/A')
                print(f"   Result {i+1}: CPT {cpt} - {desc[:60]}...")
            
            return True
        
    except Exception as e:
        print(f"❌ Vector query failed: {e}")
        print(f"   Error type: {type(e)}")
        print(f"   This indicates a fundamental vector search issue")
        
        # Check if it's a specific error we can diagnose
        error_str = str(e).lower()
        if 'not found' in error_str:
            print("   DIAGNOSIS: Vector field or collection not found")
        elif 'invalid' in error_str:
            print("   DIAGNOSIS: Invalid parameter or configuration")  
        elif 'permission' in error_str:
            print("   DIAGNOSIS: Permission or authentication issue")
        elif 'quota' in error_str:
            print("   DIAGNOSIS: API quota or billing issue")
        else:
            print("   DIAGNOSIS: Unknown vector search error")
            
        return False
    
    print("\n" + "=" * 80)
    print("FIRESTORE VECTOR SEARCH STATUS: COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    success = check_firestore_vector_status()
    
    if success:
        print("\n🎉 VECTOR SEARCH IS WORKING!")
        print("   The issue might be in the Cloud Function implementation")
    else:
        print("\n❌ VECTOR SEARCH IS NOT WORKING")
        print("   Next steps:")
        print("   1. Check Google Cloud Console for vector index status")
        print("   2. Verify Firestore vector search feature is enabled")
        print("   3. Consider rebuilding vector indexes")
        
    sys.exit(0 if success else 1)