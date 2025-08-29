#!/usr/bin/env python3

from firebase_utils import init_firestore
from config import cred_path, collection_name
import json

def debug_vector_query_issue():
    """Debug the actual vector query implementation issue"""
    print("="*80)
    print("🐛 DEBUGGING VECTOR QUERY IMPLEMENTATION")
    print("="*80)
    
    db = init_firestore(cred_path)
    if not db:
        print("❌ Failed to connect to Firestore")
        return
    
    # Get a sample document
    print("🔍 Getting sample document...")
    docs = list(db.collection(collection_name).limit(1).stream())
    if not docs:
        print("❌ No documents found")
        return
    
    sample_doc = docs[0]
    sample_data = sample_doc.to_dict()
    sample_vector = sample_data['vector']
    
    print(f"✅ Sample document: CPT {sample_data.get('CPT Codes', 'N/A')}")
    print(f"✅ Vector dimensions: {len(sample_vector)}")
    print(f"✅ Vector field exists: {'vector' in sample_data}")
    print(f"✅ Vector type: {type(sample_vector)}")
    print(f"✅ First few values: {sample_vector[:5]}")
    
    # Now try different approaches to vector query
    collection_ref = db.collection(collection_name)
    
    print(f"\\n🧪 TESTING DIFFERENT VECTOR QUERY APPROACHES:")
    
    # Method 1: Try findNearest (what our Cloud Function uses)
    print("\\nMethod 1: collection.findNearest()")
    try:
        if hasattr(collection_ref, 'findNearest'):
            print("✅ findNearest method exists")
            
            # Try the exact query our Cloud Function uses
            query = collection_ref.findNearest(
                "vector", 
                sample_vector, 
                {
                    "limit": 20,
                    "distanceMeasure": "COSINE"
                }
            )
            print("✅ Query object created successfully")
            
            # Try to execute it
            try:
                results = query.get()
                print(f"✅ Query executed successfully!")
                print(f"📊 Results: {len(results.docs)} documents")
                
                if results.docs:
                    for i, doc in enumerate(results.docs[:3]):
                        doc_data = doc.to_dict()
                        print(f"   {i+1}. CPT {doc_data.get('CPT Codes', 'N/A')}")
                else:
                    print("❌ Query succeeded but returned 0 documents!")
                    print("   This matches our Cloud Function behavior")
                    
            except Exception as e:
                print(f"❌ Query execution failed: {e}")
                print(f"   Error type: {type(e)}")
                
                # Check if it's the "index building" error
                error_str = str(e).lower()
                if "building" in error_str or "failed_precondition" in error_str:
                    print("🔧 DIAGNOSIS: Index is still building!")
                elif "permission" in error_str:
                    print("🔧 DIAGNOSIS: Permission issue")
                elif "not found" in error_str:
                    print("🔧 DIAGNOSIS: Collection or field not found")
                else:
                    print("🔧 DIAGNOSIS: Unknown vector search error")
        else:
            print("❌ findNearest method not available")
            print("   Available methods:", [m for m in dir(collection_ref) if not m.startswith('_')])
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    # Method 2: Check if it's a client version issue
    print("\\nMethod 2: Check Firestore client version")
    try:
        import google.cloud.firestore
        print(f"✅ Firestore client version: {getattr(google.cloud.firestore, '__version__', 'Unknown')}")
        
        # Check if the client supports vector operations
        print(f"✅ Client supports vector operations: {hasattr(collection_ref, 'findNearest')}")
        
    except Exception as e:
        print(f"❌ Client check failed: {e}")
    
    # Method 3: Try to manually inspect the database structure
    print("\\nMethod 3: Database structure analysis")
    try:
        # Check if we can see the index information
        print("🔍 Checking database collection structure...")
        
        # Get multiple documents to verify consistency
        all_docs = list(db.collection(collection_name).limit(5).stream())
        print(f"✅ Retrieved {len(all_docs)} documents")
        
        vector_fields_consistent = True
        for i, doc in enumerate(all_docs):
            doc_data = doc.to_dict()
            if 'vector' not in doc_data:
                print(f"❌ Document {i+1} missing vector field")
                vector_fields_consistent = False
            elif len(doc_data['vector']) != 768:
                print(f"❌ Document {i+1} has wrong vector dimension: {len(doc_data['vector'])}")
                vector_fields_consistent = False
        
        if vector_fields_consistent:
            print("✅ All documents have consistent vector fields (768 dimensions)")
        else:
            print("❌ Vector field inconsistency detected!")
            
    except Exception as e:
        print(f"❌ Database structure check failed: {e}")
    
    # Method 4: Test with Cloud Function simulation
    print("\\nMethod 4: Cloud Function simulation")
    try:
        from vertex_ai_utils import create_embedding
        
        # Create an embedding for a test query (like the Cloud Function does)
        test_text = "Bilateral total knee arthroplasty with patellar resurfacing"
        print(f"🔍 Creating embedding for: {test_text}")
        
        embedding = create_embedding(test_text)
        print(f"✅ Embedding created: {len(embedding)} dimensions")
        
        # Now try the same findNearest call that Cloud Function makes
        print("🧪 Simulating Cloud Function vector query...")
        query = collection_ref.findNearest(
            "vector",
            embedding,
            {
                "limit": 20,
                "distanceMeasure": "COSINE"
            }
        )
        
        results = query.get()
        print(f"📊 Simulation results: {len(results.docs)} documents")
        
        if results.docs:
            print("🎉 CLOUD FUNCTION SIMULATION WORKED!")
            for i, doc in enumerate(results.docs[:3]):
                doc_data = doc.to_dict()
                print(f"   {i+1}. CPT {doc_data.get('CPT Codes', 'N/A')}: {doc_data.get('Descriptions', '')[:60]}...")
        else:
            print("❌ Cloud Function simulation also returned 0 results")
            print("   This confirms the issue is with the vector search itself")
            
    except Exception as e:
        print(f"❌ Cloud Function simulation failed: {e}")
        if "building" in str(e).lower():
            print("🔧 CONFIRMED: The vector index is still building!")
        else:
            print("🔧 CONFIRMED: There's a vector search implementation issue!")
    
    print(f"\\n" + "="*80)
    print("🔧 DEBUGGING SUMMARY")
    print("="*80)

if __name__ == '__main__':
    debug_vector_query_issue()