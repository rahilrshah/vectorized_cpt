#!/usr/bin/env python3

from firebase_utils import init_firestore
from config import cred_path, collection_name
from google.cloud.firestore_v1.base_query import DistanceMeasure
import numpy as np

def diagnose_ready_indexes():
    """Diagnose why ready vector indexes aren't working"""
    print("=" * 80)
    print("DIAGNOSING READY VECTOR INDEXES")
    print("=" * 80)
    
    db = init_firestore(cred_path)
    collection_ref = db.collection(collection_name)
    
    # Get sample data
    docs = list(collection_ref.limit(3).stream())
    print(f"✅ Retrieved {len(docs)} sample documents")
    
    for i, doc in enumerate(docs):
        doc_data = doc.to_dict()
        doc_id = doc.id
        vector_data = doc_data.get('vector', [])
        cpt_code = doc_data.get('CPT Codes', 'N/A')
        
        print(f"\n📋 DOCUMENT {i+1} ANALYSIS:")
        print(f"   ID: {doc_id}")
        print(f"   CPT Code: {cpt_code}")
        print(f"   Vector length: {len(vector_data)}")
        print(f"   Vector type: {type(vector_data)}")
        
        if len(vector_data) > 0:
            print(f"   Vector element type: {type(vector_data[0])}")
            print(f"   Vector range: [{min(vector_data):.6f}, {max(vector_data):.6f}]")
            
            # Check if vector is normalized
            vector_np = np.array(vector_data)
            norm = np.linalg.norm(vector_np)
            print(f"   Vector norm: {norm:.6f}")
            
            # Test vector search with THIS specific vector
            print(f"\n🧪 TESTING VECTOR SEARCH WITH DOCUMENT {i+1}:")
            
            try:
                # Test 1: Exact match search
                exact_query = collection_ref.find_nearest(
                    vector_field='vector',
                    query_vector=vector_data,
                    limit=5,
                    distance_measure=DistanceMeasure.COSINE
                )
                
                exact_results = list(exact_query.get())
                print(f"   Exact match results: {len(exact_results)}")
                
                if len(exact_results) > 0:
                    print(f"   🎉 SUCCESS! Vector search works for this document")
                    
                    # Check if we got the same document back
                    found_self = False
                    for result_doc in exact_results:
                        if result_doc.id == doc_id:
                            found_self = True
                            print(f"   ✅ Found the same document (perfect match)")
                            break
                    
                    if not found_self:
                        print(f"   ⚠️  Didn't find the same document in results")
                        print(f"      This suggests index data might not match document data")
                    
                    # Show all results
                    for j, result_doc in enumerate(exact_results):
                        result_data = result_doc.to_dict()
                        result_cpt = result_data.get('CPT Codes', 'N/A')
                        result_desc = result_data.get('Descriptions', 'N/A')
                        match_marker = "🎯" if result_doc.id == doc_id else "  "
                        print(f"   {match_marker} Result {j+1}: CPT {result_cpt} - {result_desc[:50]}...")
                    
                    return True  # We found working vector search!
                    
                else:
                    print(f"   ❌ No results found for this document's vector")
                    
                    # Try different approaches
                    print(f"   🔍 Trying alternative approaches...")
                    
                    # Try with different distance measures
                    for distance_name, distance_enum in [
                        ("EUCLIDEAN", DistanceMeasure.EUCLIDEAN),
                        ("DOT_PRODUCT", DistanceMeasure.DOT_PRODUCT)
                    ]:
                        try:
                            alt_query = collection_ref.find_nearest(
                                vector_field='vector',
                                query_vector=vector_data,
                                limit=3,
                                distance_measure=distance_enum
                            )
                            alt_results = list(alt_query.get())
                            print(f"      {distance_name}: {len(alt_results)} results")
                            
                            if len(alt_results) > 0:
                                print(f"      🎉 {distance_name} works!")
                                return True
                                
                        except Exception as e:
                            print(f"      {distance_name}: Error - {e}")
                    
                    # Try with modified vector (to see if exact match is the issue)
                    print(f"   🔍 Testing with slightly modified vector...")
                    modified_vector = [x + 0.00001 for x in vector_data]  # Tiny modification
                    
                    try:
                        mod_query = collection_ref.find_nearest(
                            vector_field='vector',
                            query_vector=modified_vector,
                            limit=3,
                            distance_measure=DistanceMeasure.COSINE
                        )
                        mod_results = list(mod_query.get())
                        print(f"      Modified vector: {len(mod_results)} results")
                        
                        if len(mod_results) > 0:
                            print(f"      🤔 Modified vector works but exact doesn't")
                            print(f"         This suggests an issue with exact match handling")
                            return True
                            
                    except Exception as e:
                        print(f"      Modified vector: Error - {e}")
                        
            except Exception as e:
                print(f"   ❌ Vector search failed: {e}")
                print(f"      Error type: {type(e)}")
                
        else:
            print(f"   ❌ No vector data found in document")
    
    print(f"\n" + "=" * 80)
    print(f"CONCLUSION: VECTOR SEARCH IS NOT WORKING FOR ANY DOCUMENT")
    print(f"=" * 80)
    
    print(f"\n💡 RECOMMENDED ACTIONS:")
    print(f"1. Delete the unused 'description_vector' index to eliminate conflicts")
    print(f"2. Consider rebuilding the 'vector' index from scratch")
    print(f"3. Check if Firestore vector search has regional restrictions")
    print(f"4. Verify billing and quotas for vector search operations")
    
    return False

if __name__ == '__main__':
    success = diagnose_ready_indexes()
    
    if not success:
        print(f"\n🚨 VECTOR SEARCH INFRASTRUCTURE ISSUE CONFIRMED")
        print(f"   This requires administrative action in Google Cloud Console")