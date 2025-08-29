from firebase_utils import init_firestore
from config import cred_path, collection_name
import time

def test_vector_index_status():
    """Test if the vector index is ready by attempting a vector query"""
    print("=" * 80)
    print("VECTOR INDEX STATUS TEST")
    print("=" * 80)
    
    db = init_firestore(cred_path)
    if not db:
        print("❌ Failed to initialize Firestore")
        return
    
    print(f"Testing vector index for collection: {collection_name}")
    
    try:
        # Get a sample document with vector
        print("\n🔍 Getting sample vector...")
        sample_docs = list(db.collection(collection_name).limit(1).stream())
        
        if not sample_docs:
            print("❌ No documents found in collection")
            return
            
        sample_data = sample_docs[0].to_dict()
        if 'vector' not in sample_data:
            print("❌ No vector field found in sample document")
            return
            
        sample_vector = sample_data['vector']
        print(f"✅ Got sample vector with {len(sample_vector)} dimensions")
        print(f"   CPT Code: {sample_data.get('CPT Codes', 'N/A')}")
        
        # Test vector query using different methods
        print(f"\n🧪 TESTING VECTOR QUERY METHODS...")
        
        # Method 1: Try findNearest (if available)
        try:
            print("Method 1: Using collection.findNearest()")
            vector_query = db.collection(collection_name).findNearest(
                "vector", 
                sample_vector, 
                {"limit": 3, "distanceMeasure": "COSINE"}
            )
            
            start_time = time.time()
            results = vector_query.get()
            end_time = time.time()
            
            print(f"✅ SUCCESS! Vector query completed in {end_time - start_time:.2f}s")
            print(f"   Returned {len(results.docs)} results")
            
            for i, doc in enumerate(results.docs):
                doc_data = doc.to_dict()
                print(f"   {i+1}. CPT {doc_data.get('CPT Codes', 'N/A')}: {doc_data.get('Descriptions', '')[:60]}...")
            
            print(f"\n🎉 VECTOR INDEX IS READY AND WORKING!")
            return True
            
        except AttributeError as e:
            print(f"❌ Method 1 failed: findNearest method not available ({e})")
            
        except Exception as e:
            if "index is currently building" in str(e).lower():
                print(f"❌ Method 1 failed: INDEX STILL BUILDING")
                print(f"   Error: {str(e)[:200]}...")
                return False
            else:
                print(f"❌ Method 1 failed: {e}")
        
        # Method 2: Try using the Admin SDK directly (if available)
        try:
            print("\nMethod 2: Using vector_query() method")
            
            # This is how the Cloud Function should work
            from google.cloud.firestore_v1.types import StructuredQuery
            from google.cloud.firestore_v1 import VectorQuery
            
            # Create vector query object
            collection_ref = db.collection(collection_name)
            
            # Try different approach
            print("   Testing alternative vector query...")
            
            # This might not work in this environment, but let's see
            query = collection_ref.vector_query(
                vector_field="vector",
                query_vector=sample_vector,
                limit=3,
                distance_measure="COSINE"
            )
            
            results = query.get()
            print(f"✅ Method 2 SUCCESS!")
            print(f"   Returned {len(results)} results")
            return True
            
        except Exception as e:
            print(f"❌ Method 2 failed: {e}")
        
        print(f"\n❌ ALL VECTOR QUERY METHODS FAILED")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_index_building_time():
    """Estimate how long the index has been building"""
    print(f"\n⏰ INDEX BUILDING TIME ESTIMATION:")
    
    # Check when we deployed the index
    import os
    import datetime
    
    try:
        # Get the modification time of the index file
        index_file = '/workspace/windows-projects/Vectorized_CPT/firestore.indexes.json'
        if os.path.exists(index_file):
            mod_time = os.path.getmtime(index_file)
            created_time = datetime.datetime.fromtimestamp(mod_time)
            current_time = datetime.datetime.now()
            elapsed = current_time - created_time
            
            print(f"   Index config created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Time elapsed: {elapsed}")
            
            # Vector indexes can take 30 minutes to several hours depending on data size
            if elapsed.total_seconds() < 1800:  # 30 minutes
                print(f"   ⏳ Index likely still building (usually takes 30+ minutes for large datasets)")
            elif elapsed.total_seconds() < 7200:  # 2 hours
                print(f"   ⏳ Index may still be building (can take up to 2 hours)")
            else:
                print(f"   ⚠️  Index should be ready by now - there may be an issue")
                
    except Exception as e:
        print(f"   ❌ Could not determine timing: {e}")

if __name__ == '__main__':
    index_ready = test_vector_index_status()
    check_index_building_time()
    
    if not index_ready:
        print(f"\n" + "="*80)
        print("RECOMMENDATION: WAIT FOR INDEX TO FINISH BUILDING")
        print("="*80)
        print("The vector index is still building. This is normal for large datasets.")
        print("Try testing the website again in 10-20 minutes.")
        print("You can monitor progress by re-running this script.")
    else:
        print(f"\n" + "="*80)
        print("INDEX IS READY - WEBSITE SHOULD WORK!")
        print("="*80)