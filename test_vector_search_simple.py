#!/usr/bin/env python3

from firebase_utils import init_firestore
from config import cred_path, collection_name
from vertex_ai_utils import get_vertex_embeddings
from config import vertex_project, vertex_location, vertex_model
from google.cloud.firestore_v1.base_query import DistanceMeasure

def simple_vector_search_test():
    """Simple test to isolate vector search issues"""
    print("=" * 60)
    print("SIMPLE VECTOR SEARCH TEST")
    print("=" * 60)
    
    # Initialize Firestore
    db = init_firestore(cred_path)
    if not db:
        print("❌ Failed to initialize Firestore")
        return
    
    collection_ref = db.collection(collection_name)
    print(f"✅ Connected to collection: {collection_name}")
    
    # Check collection has documents
    test_docs = list(collection_ref.limit(3).stream())
    print(f"✅ Collection has {len(test_docs)} documents (showing first 3)")
    
    if len(test_docs) == 0:
        print("❌ Collection is empty!")
        return
    
    # Show sample documents
    for i, doc in enumerate(test_docs):
        doc_data = doc.to_dict()
        cpt = doc_data.get('CPT Codes', 'N/A')
        desc = doc_data.get('Descriptions', 'N/A')
        has_vector = 'vector' in doc_data
        vector_len = len(doc_data['vector']) if has_vector else 0
        print(f"  {i+1}. CPT {cpt}: {desc[:60]}... [vector: {vector_len} dims]")
    
    # Test 1: Query with exact same vector from database (should return perfect match)
    print(f"\n🧪 TEST 1: Query with exact database vector")
    
    sample_doc = test_docs[0].to_dict()
    exact_vector = sample_doc['vector']
    sample_cpt = sample_doc.get('CPT Codes', 'N/A')
    sample_desc = sample_doc.get('Descriptions', 'N/A')
    
    print(f"Using vector from: CPT {sample_cpt}")
    print(f"Description: {sample_desc[:80]}...")
    
    try:
        exact_query = collection_ref.find_nearest(
            vector_field='vector',
            query_vector=exact_vector,
            limit=5,
            distance_measure=DistanceMeasure.COSINE
        )
        
        results = list(exact_query.get())
        print(f"✅ Query executed successfully")
        print(f"📊 Results found: {len(results)}")
        
        if len(results) > 0:
            print("🎉 SUCCESS! Vector search is working!")
            for i, doc in enumerate(results[:3]):
                doc_data = doc.to_dict()
                cpt = doc_data.get('CPT Codes', 'N/A')
                desc = doc_data.get('Descriptions', 'N/A')
                print(f"  {i+1}. CPT {cpt}: {desc[:50]}...")
                
                # The first result should be the exact same document
                if i == 0 and cpt == sample_cpt:
                    print("    ✅ Perfect match found (same document)")
        else:
            print("❌ Query succeeded but returned 0 results")
            print("   This suggests a fundamental vector search issue")
            
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        print(f"   Error type: {type(e)}")
        return
    
    # Test 2: Generate new embedding and search
    print(f"\n🧪 TEST 2: Generate new embedding and search")
    
    # Use a simple, known description
    test_text = sample_desc  # Use same text as the stored vector
    print(f"Generating embedding for: {test_text[:80]}...")
    
    try:
        embeddings = get_vertex_embeddings(
            descriptions=[test_text],
            project=vertex_project,
            location=vertex_location,
            model=vertex_model,
            task_type='RETRIEVAL_DOCUMENT',  # Same as database
            batch_size=1
        )
        
        if not embeddings or len(embeddings) == 0:
            print("❌ Failed to generate embedding")
            return
            
        new_embedding = embeddings[0]
        print(f"✅ Generated embedding: {len(new_embedding)} dimensions")
        
        # Search with the new embedding
        new_query = collection_ref.find_nearest(
            vector_field='vector',
            query_vector=new_embedding,
            limit=10,
            distance_measure=DistanceMeasure.COSINE
        )
        
        new_results = list(new_query.get())
        print(f"📊 New embedding search results: {len(new_results)}")
        
        if len(new_results) > 0:
            print("🎉 SUCCESS! New embedding search works!")
            for i, doc in enumerate(new_results[:5]):
                doc_data = doc.to_dict()
                cpt = doc_data.get('CPT Codes', 'N/A')
                desc = doc_data.get('Descriptions', 'N/A')
                print(f"  {i+1}. CPT {cpt}: {desc[:50]}...")
            
            # Check if we found the same document in top results
            found_same = any(doc.to_dict().get('CPT Codes') == sample_cpt for doc in new_results[:5])
            if found_same:
                print("    ✅ Found the same document we used for text generation!")
            else:
                print("    ⚠️ Didn't find the same document in top 5 (might indicate embedding inconsistency)")
                
        else:
            print("❌ New embedding search returned 0 results")
            print("   This suggests embedding compatibility issues")
            
    except Exception as e:
        print(f"❌ New embedding search failed: {e}")
        return
    
    print(f"\n📋 SUMMARY:")
    print(f"✅ Firestore connection: Working")
    print(f"✅ Collection access: Working") 
    print(f"✅ Vector field present: Working")
    print(f"✅ Vector search API: Working")
    if len(results) > 0 and len(new_results) > 0:
        print(f"✅ Overall system: WORKING!")
        print(f"\n🔧 The issue is likely in the Cloud Function implementation")
        print(f"   Possible causes:")
        print(f"   1. JavaScript vs Python API differences")
        print(f"   2. Vector format conversion issues")
        print(f"   3. Query parameter format differences")
    elif len(results) > 0:
        print(f"⚠️ Exact vector works, new embeddings don't")
        print(f"   This indicates embedding generation inconsistency")
    else:
        print(f"❌ Vector search not working at all")
        print(f"   This indicates a fundamental configuration issue")

if __name__ == '__main__':
    simple_vector_search_test()