#!/usr/bin/env python3

from firebase_utils import init_firestore
from config import cred_path, collection_name, vertex_project, vertex_location, vertex_model
from vertex_ai_utils import get_vertex_embeddings
import json

def replicate_cloud_function_exact():
    """Replicate the exact Cloud Function logic to find the issue"""
    print("="*80)
    print("🔍 EXACT CLOUD FUNCTION REPLICATION")
    print("="*80)
    
    # Step 1: Initialize Firestore (same as Cloud Function)
    print("Step 1: Initialize Firestore")
    db = init_firestore(cred_path)
    if not db:
        print("❌ Failed to initialize Firestore")
        return
    print("✅ Firestore initialized")
    
    # Step 2: Create embedding (same as Cloud Function)
    print("\\nStep 2: Create embedding")
    test_text = "Bilateral total knee arthroplasty with patellar resurfacing"
    print(f"Text: {test_text}")
    
    # Use the same vertex AI approach as Cloud Function
    try:
        # Create embedding using text-embedding-004 (same as Cloud Function)
        model_name = vertex_model  # This should be "text-embedding-004"
        print(f"Using model: {model_name}")
        print(f"Project: {vertex_project}")
        print(f"Location: {vertex_location}")
        
        # This replicates the Cloud Function's embedding creation
        embeddings = get_vertex_embeddings(
            descriptions=[test_text],
            project=vertex_project,
            location=vertex_location,
            model=model_name,
            task_type="RETRIEVAL_DOCUMENT"
        )
        
        embedding = embeddings[0]
        print(f"✅ Embedding created: {len(embedding)} dimensions")
        print(f"First 5 values: {embedding[:5]}")
        
    except Exception as e:
        print(f"❌ Embedding creation failed: {e}")
        print(f"This might indicate the same issue affecting the Cloud Function")
        return
    
    # Step 3: Collection check (same as Cloud Function)
    print(f"\\nStep 3: Collection check")
    collection_name_cf = "Vectorized_CPT_Test"  # Exactly as in Cloud Function
    vector_field_cf = "vector"  # Exactly as in Cloud Function
    
    collection_ref = db.collection(collection_name_cf)
    print(f"Collection: {collection_name_cf}")
    print(f"Vector field: {vector_field_cf}")
    
    # Check if collection has documents (same as Cloud Function)
    test_snapshot = collection_ref.limit(1).get()
    print(f"Test snapshot size: {len(test_snapshot)}")
    
    if len(test_snapshot) == 0:
        print("❌ Collection is empty")
        return
    else:
        print("✅ Collection has documents")
    
    # Step 4: Vector query (EXACT same as Cloud Function)
    print(f"\\nStep 4: Vector query (replicating Cloud Function exactly)")
    
    try:
        print("Creating vector query...")
        
        # Check if the method exists
        if hasattr(collection_ref, 'findNearest'):
            print("✅ findNearest method available")
            
            # Create the exact query from Cloud Function
            vector_query = collection_ref.findNearest(
                vector_field_cf,
                embedding,
                {
                    "limit": 20,  # Same as our enhanced Cloud Function
                    "distanceMeasure": "COSINE"
                }
            )
            print("✅ Vector query object created")
            
            # Execute query
            print("Executing vector query...")
            snapshot = vector_query.get()
            
            results = [{"id": doc.id, **doc.to_dict()} for doc in snapshot]
            print(f"✅ Query executed successfully!")
            print(f"📊 Results count: {len(results)}")
            
            if len(results) > 0:
                print("🎉 SUCCESS! Found matches:")
                for i, result in enumerate(results[:5]):
                    cpt = result.get('CPT Codes', 'N/A')
                    desc = result.get('Descriptions', 'N/A')
                    print(f"   {i+1}. CPT {cpt}: {desc[:60]}...")
                    
                print("\\n🔧 CONCLUSION: Local replication works - Cloud Function issue is elsewhere")
            else:
                print("❌ Query succeeded but returned 0 results")
                print("   This matches the Cloud Function behavior!")
                print("\\n🔍 DEBUGGING THE ZERO RESULTS:")
                
                # Additional debugging for zero results
                print("\\nDebugging zero results issue:")
                
                # Check 1: Verify vector data in database
                print("Check 1: Verify sample vector data")
                sample_doc = list(collection_ref.limit(1).stream())[0]
                sample_data = sample_doc.to_dict()
                db_vector = sample_data['vector']
                print(f"   Database vector length: {len(db_vector)}")
                print(f"   Query vector length: {len(embedding)}")
                print(f"   Vector types match: {type(db_vector)} vs {type(embedding)}")
                
                # Check 2: Compare vector values  
                print("Check 2: Vector value comparison")
                print(f"   DB vector sample: {db_vector[:3]}")
                print(f"   Query vector sample: {embedding[:3]}")
                
                # Check 3: Try with the exact same vector from database
                print("Check 3: Query with exact database vector (should return similarity=1.0)")
                try:
                    exact_query = collection_ref.findNearest(
                        vector_field_cf,
                        db_vector,  # Use exact vector from database
                        {
                            "limit": 5,
                            "distanceMeasure": "COSINE"
                        }
                    )
                    exact_results = exact_query.get()
                    print(f"   Exact vector query results: {len(exact_results)} documents")
                    
                    if len(exact_results) > 0:
                        print("   ✅ Exact vector query works - the issue is with embedding compatibility")
                        
                        # Compare the vectors numerically
                        import numpy as np
                        db_vec_np = np.array(db_vector)
                        query_vec_np = np.array(embedding)
                        
                        # Calculate similarity manually
                        dot_product = np.dot(db_vec_np, query_vec_np)
                        norm1 = np.linalg.norm(db_vec_np)
                        norm2 = np.linalg.norm(query_vec_np)
                        
                        if norm1 > 0 and norm2 > 0:
                            similarity = dot_product / (norm1 * norm2)
                            print(f"   Manual similarity calculation: {similarity:.6f}")
                            
                            if similarity < 0.1:
                                print("   🔧 DIAGNOSIS: Query embedding is not similar enough to database embeddings")
                                print("   🔧 POSSIBLE CAUSE: Embedding model version mismatch or text processing difference")
                            else:
                                print("   ✅ Similarity is good - there might be a search threshold issue")
                        
                    else:
                        print("   ❌ Even exact vector query returns 0 results!")
                        print("   🔧 DIAGNOSIS: The vector index is fundamentally broken")
                        
                except Exception as e:
                    print(f"   ❌ Exact vector query failed: {e}")
                    if "building" in str(e).lower() or "precondition" in str(e).lower():
                        print("   🔧 DIAGNOSIS: Vector index is still building!")
                    else:
                        print("   🔧 DIAGNOSIS: Vector search API issue")
        else:
            print("❌ findNearest method not available")
            available_methods = [m for m in dir(collection_ref) if 'find' in m.lower() or 'near' in m.lower()]
            print(f"   Available find/near methods: {available_methods}")
            
            # Try the snake_case version
            if hasattr(collection_ref, 'find_nearest'):
                print("   ✅ Found find_nearest (snake_case) - trying that...")
                try:
                    # Try with string distance measure first
                    vector_query = collection_ref.find_nearest(
                        vector_field=vector_field_cf,
                        query_vector=embedding,
                        limit=20,
                        distance_measure="COSINE"
                    )
                    print("✅ Vector query object created with find_nearest")
                    
                    # Execute query
                    print("Executing vector query...")
                    snapshot = vector_query.get()
                    
                    results = list(snapshot)
                    print(f"✅ Query executed successfully!")
                    print(f"📊 Results count: {len(results)}")
                    
                    if len(results) > 0:
                        print("🎉 SUCCESS! Found matches with find_nearest:")
                        for i, doc in enumerate(results[:5]):
                            doc_data = doc.to_dict()
                            cpt = doc_data.get('CPT Codes', 'N/A')
                            desc = doc_data.get('Descriptions', 'N/A')
                            print(f"   {i+1}. CPT {cpt}: {desc[:60]}...")
                            
                        print("\\n🎉 BREAKTHROUGH: Local vector search WORKS!")
                        print("🔧 CONCLUSION: The issue is with Cloud Function implementation!")
                        
                    else:
                        print("❌ find_nearest also returns 0 results")
                        print("   The issue is deeper - let's test with exact database vector")
                        
                        # Test with exact database vector
                        print("\\n🧪 Testing with exact database vector:")
                        sample_doc = list(collection_ref.limit(1).stream())[0]
                        sample_data = sample_doc.to_dict()
                        db_vector = sample_data['vector']
                        
                        exact_query = collection_ref.find_nearest(
                            vector_field=vector_field_cf,
                            query_vector=db_vector,
                            limit=5,
                            distance_measure="COSINE"
                        )
                        exact_results = list(exact_query.get())
                        print(f"   Exact vector results: {len(exact_results)} documents")
                        
                        if len(exact_results) > 0:
                            print("   ✅ Exact vector works - embedding compatibility issue")
                        else:
                            print("   ❌ Even exact vector fails - index issue confirmed")
                        
                except Exception as e:
                    print(f"❌ find_nearest failed: {e}")
                    
                    if "building" in str(e).lower() or "precondition" in str(e).lower():
                        print("🔧 CONFIRMED: Vector index is still building!")
                    else:
                        print("🔧 Vector search implementation error")
            else:
                print("   ❌ No find_nearest method available either")
    
    except Exception as e:
        print(f"❌ Vector query failed: {e}")
        print(f"   Error type: {type(e)}")
        
        error_str = str(e).lower()
        if "building" in error_str or "precondition" in error_str:
            print("🔧 DIAGNOSIS: Vector index is still building")
        elif "not found" in error_str or "does not exist" in error_str:
            print("🔧 DIAGNOSIS: Index or collection configuration issue")
        elif "permission" in error_str or "denied" in error_str:
            print("🔧 DIAGNOSIS: Permission/authentication issue")
        else:
            print("🔧 DIAGNOSIS: Unknown vector search error")
    
    print("\\n" + "="*80)
    print("🔧 REPLICATION COMPLETE")
    print("="*80)

if __name__ == '__main__':
    replicate_cloud_function_exact()