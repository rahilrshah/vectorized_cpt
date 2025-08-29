from firebase_utils import init_firestore
from config import cred_path, collection_name
import json
import numpy as np

def validate_cloud_function_config():
    """Validate all configuration matches between local config and Cloud Function"""
    print("=" * 80)
    print("CONFIGURATION VALIDATION - CLOUD FUNCTION vs LOCAL")
    print("=" * 80)
    
    # 1. Load local config
    print("\n🔧 STEP 1: LOCAL CONFIGURATION")
    from config import vertex_project, vertex_location, vertex_model, collection_name
    
    print(f"✅ Local Config:")
    print(f"   Project ID: {vertex_project}")
    print(f"   Location: {vertex_location}")
    print(f"   Model: {vertex_model}")
    print(f"   Collection: {collection_name}")
    
    # 2. Load Cloud Function config
    print(f"\n☁️  STEP 2: CLOUD FUNCTION CONFIGURATION")
    try:
        with open('/workspace/windows-projects/Vectorized_CPT/functions/src/index.ts', 'r') as f:
            cf_content = f.read()
            
        # Extract config values
        import re
        project_match = re.search(r'PROJECT_ID = "([^"]+)"', cf_content)
        location_match = re.search(r'LOCATION = "([^"]+)"', cf_content)
        model_match = re.search(r'EMBEDDING_MODEL = "([^"]+)"', cf_content)
        collection_match = re.search(r'COLLECTION_NAME = "([^"]+)"', cf_content)
        field_match = re.search(r'FIRESTORE_VECTOR_FIELD = "([^"]+)"', cf_content)
        
        cf_project = project_match.group(1) if project_match else "NOT FOUND"
        cf_location = location_match.group(1) if location_match else "NOT FOUND"
        cf_model = model_match.group(1) if model_match else "NOT FOUND"
        cf_collection = collection_match.group(1) if collection_match else "NOT FOUND"
        cf_vector_field = field_match.group(1) if field_match else "NOT FOUND"
        
        print(f"✅ Cloud Function Config:")
        print(f"   Project ID: {cf_project}")
        print(f"   Location: {cf_location}")
        print(f"   Model: {cf_model}")
        print(f"   Collection: {cf_collection}")
        print(f"   Vector Field: {cf_vector_field}")
        
        # 3. Compare configurations
        print(f"\n🔍 STEP 3: CONFIGURATION COMPARISON")
        
        configs_match = True
        if vertex_project != cf_project:
            print(f"❌ PROJECT MISMATCH: Local '{vertex_project}' vs CF '{cf_project}'")
            configs_match = False
        else:
            print(f"✅ Project ID matches: {vertex_project}")
            
        if vertex_location != cf_location:
            print(f"❌ LOCATION MISMATCH: Local '{vertex_location}' vs CF '{cf_location}'")
            configs_match = False
        else:
            print(f"✅ Location matches: {vertex_location}")
            
        if vertex_model != cf_model:
            print(f"❌ MODEL MISMATCH: Local '{vertex_model}' vs CF '{cf_model}'")
            configs_match = False
        else:
            print(f"✅ Model matches: {vertex_model}")
            
        if collection_name != cf_collection:
            print(f"❌ COLLECTION MISMATCH: Local '{collection_name}' vs CF '{cf_collection}'")
            configs_match = False
        else:
            print(f"✅ Collection matches: {collection_name}")
        
        if configs_match:
            print(f"\n🎉 ALL CONFIGURATIONS MATCH!")
        else:
            print(f"\n🚨 CONFIGURATION MISMATCHES FOUND!")
            
    except Exception as e:
        print(f"❌ Error reading Cloud Function config: {e}")
    
    # 4. Validate Firestore collections
    print(f"\n🗄️  STEP 4: FIRESTORE COLLECTION VALIDATION")
    
    db = init_firestore(cred_path)
    if not db:
        print("❌ Failed to initialize Firestore")
        return
    
    # List all collections (this is tricky in Firestore - we'll try to access the known one)
    try:
        # Test if the collection exists and has documents
        test_docs = list(db.collection(collection_name).limit(1).stream())
        if test_docs:
            print(f"✅ Collection '{collection_name}' exists and accessible")
            
            # Check the field structure
            doc_data = test_docs[0].to_dict()
            print(f"✅ Sample document fields: {list(doc_data.keys())}")
            
            # Validate vector field specifically
            if 'vector' in doc_data:
                vector = doc_data['vector']
                if isinstance(vector, list) and len(vector) == 768:
                    print(f"✅ Vector field: Present, correct type (list), correct dimension (768)")
                else:
                    print(f"❌ Vector field: Present but wrong format - type: {type(vector)}, length: {len(vector) if isinstance(vector, list) else 'N/A'}")
            else:
                print(f"❌ Vector field: MISSING from documents!")
                
        else:
            print(f"❌ Collection '{collection_name}' is empty or inaccessible")
            
    except Exception as e:
        print(f"❌ Error accessing collection: {e}")
    
    # 5. Test vector index configuration
    print(f"\n📊 STEP 5: VECTOR INDEX VALIDATION")
    
    # Check if our firestore.indexes.json matches the actual data
    try:
        with open('/workspace/windows-projects/Vectorized_CPT/firestore.indexes.json', 'r') as f:
            index_config = json.load(f)
        
        print(f"✅ Index config loaded")
        
        if 'indexes' in index_config:
            for idx in index_config['indexes']:
                print(f"   Collection: {idx.get('collectionGroup')}")
                print(f"   Query Scope: {idx.get('queryScope')}")
                
                if 'fields' in idx:
                    for field in idx['fields']:
                        print(f"   Field Path: {field.get('fieldPath')}")
                        if 'vectorConfig' in field:
                            vec_config = field['vectorConfig']
                            print(f"   Vector Dimension: {vec_config.get('dimension')}")
                            print(f"   Vector Type: {list(vec_config.keys())}")
        
        # Validate against our data
        if index_config['indexes'][0]['collectionGroup'] == collection_name:
            print(f"✅ Index collection matches: {collection_name}")
        else:
            print(f"❌ Index collection mismatch!")
            
        if index_config['indexes'][0]['fields'][0]['vectorConfig']['dimension'] == 768:
            print(f"✅ Index dimension matches data: 768")
        else:
            print(f"❌ Index dimension mismatch!")
            
    except Exception as e:
        print(f"❌ Error validating index config: {e}")
    
    # 6. Test a simple vector query to see if index works
    print(f"\n🧪 STEP 6: VECTOR QUERY TEST")
    
    try:
        # Get a sample vector from the database
        sample_doc = list(db.collection(collection_name).limit(1).stream())[0]
        sample_data = sample_doc.to_dict()
        sample_vector = sample_data['vector']
        
        print(f"Using sample vector from CPT {sample_data.get('CPT Codes', 'N/A')}")
        
        # Try a vector query (this will test the index)
        vector_query = db.collection(collection_name).findNearest(
            "vector", 
            sample_vector, 
            {
                "limit": 3,
                "distanceMeasure": "COSINE"
            }
        )
        
        results = vector_query.get()
        print(f"✅ Vector query successful! Returned {len(results.docs)} results")
        
        for i, doc in enumerate(results.docs):
            doc_data = doc.to_dict()
            print(f"   {i+1}. CPT {doc_data.get('CPT Codes', 'N/A')}: {doc_data.get('Descriptions', 'N/A')[:60]}...")
            
        print(f"✅ VECTOR INDEX IS WORKING CORRECTLY!")
        
    except Exception as e:
        print(f"❌ Vector query failed: {e}")
        print(f"   This suggests an index or configuration issue")
    
    print("\n" + "=" * 80)
    print("CONFIGURATION VALIDATION COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    validate_cloud_function_config()