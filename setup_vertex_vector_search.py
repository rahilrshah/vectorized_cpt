#!/usr/bin/env python3
"""
Set up Vertex AI Vector Search - create bucket, upload data, create index and endpoint
"""

import json
import os
import time
from google.cloud import storage
from google.cloud import aiplatform
from config import vertex_project, vertex_location, cred_path

# Load configuration
with open('vertex_ai_config.json', 'r') as f:
    config = json.load(f)

def setup_authentication():
    """Set up Google Cloud authentication"""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
    print(f"✅ Authentication set up using {cred_path}")

def create_storage_bucket():
    """Create Cloud Storage bucket for vector data"""
    print("\n📦 Setting up Cloud Storage...")
    
    try:
        # Initialize storage client
        storage_client = storage.Client(project=config['project_id'])
        bucket_name = config['bucket_name']
        
        # Check if bucket already exists
        try:
            bucket = storage_client.bucket(bucket_name)
            if bucket.exists():
                print(f"✅ Bucket '{bucket_name}' already exists")
                return bucket_name
        except Exception:
            pass
        
        # Create bucket
        bucket = storage_client.create_bucket(
            bucket_name, 
            location=config['location']
        )
        print(f"✅ Created bucket '{bucket_name}' in {config['location']}")
        return bucket_name
        
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        return None

def upload_vectors_to_storage(bucket_name):
    """Upload JSONL file to Cloud Storage"""
    print(f"\n📤 Uploading vectors to Cloud Storage...")
    
    try:
        storage_client = storage.Client(project=config['project_id'])
        bucket = storage_client.bucket(bucket_name)
        
        # Upload the JSONL file
        jsonl_filename = "cpt_vectors.jsonl"
        blob_name = f"vectors/{jsonl_filename}"
        blob = bucket.blob(blob_name)
        
        print(f"  Uploading {jsonl_filename} to gs://{bucket_name}/{blob_name}...")
        
        with open(jsonl_filename, 'rb') as f:
            blob.upload_from_file(f)
        
        print(f"✅ Uploaded {jsonl_filename} successfully")
        
        # Return the full GCS path
        gcs_path = f"gs://{bucket_name}/{blob_name}"
        print(f"📍 Vector data location: {gcs_path}")
        return gcs_path
        
    except Exception as e:
        print(f"❌ Error uploading to storage: {e}")
        return None

def create_vector_search_index(gcs_path):
    """Create Vertex AI Vector Search index"""
    print(f"\n🔍 Creating Vertex AI Vector Search index...")
    
    try:
        # Initialize Vertex AI
        aiplatform.init(
            project=config['project_id'],
            location=config['location']
        )
        
        print(f"  Creating index '{config['index_name']}'...")
        print(f"  Data source: {gcs_path}")
        print(f"  Dimensions: {config['dimensions']}")
        print(f"  Distance measure: {config['distance_measure']}")
        
        # Create the index
        index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
            display_name=config['index_name'],
            contents_delta_uri=gcs_path,
            dimensions=config['dimensions'],
            distance_measure_type=config['distance_measure'],
            approximate_neighbors_count=10,  # Required for tree-AH algorithm
            leaf_node_embedding_count=500,   # Optional: controls index quality vs speed
            leaf_nodes_to_search_percent=10, # Optional: controls search quality vs speed  
            description="CPT Code Vector Search Index for Medical Billing",
            labels={"application": "cpt-search", "version": "v1"}
        )
        
        print(f"✅ Created index: {index.display_name}")
        print(f"📍 Index resource name: {index.resource_name}")
        
        # Save index info to config
        config['index_resource_name'] = index.resource_name
        config['index_id'] = index.resource_name.split('/')[-1]
        
        with open('vertex_ai_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return index
        
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        return None

def create_vector_search_endpoint():
    """Create Vertex AI Vector Search endpoint"""
    print(f"\n🌐 Creating Vertex AI Vector Search endpoint...")
    
    try:
        # Create endpoint
        print(f"  Creating endpoint '{config['endpoint_name']}'...")
        
        endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
            display_name=config['endpoint_name'],
            description="CPT Code Vector Search Endpoint",
            public_endpoint_enabled=True,  # Enable public endpoint access
            labels={"application": "cpt-search", "version": "v1"}
        )
        
        print(f"✅ Created endpoint: {endpoint.display_name}")
        print(f"📍 Endpoint resource name: {endpoint.resource_name}")
        
        # Save endpoint info to config
        config['endpoint_resource_name'] = endpoint.resource_name
        config['endpoint_id'] = endpoint.resource_name.split('/')[-1]
        
        with open('vertex_ai_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return endpoint
        
    except Exception as e:
        print(f"❌ Error creating endpoint: {e}")
        return None

def deploy_index_to_endpoint(index, endpoint):
    """Deploy the index to the endpoint"""
    print(f"\n🚀 Deploying index to endpoint...")
    print(f"⚠️  This operation takes approximately 30-45 minutes...")
    
    try:
        deployed_index = endpoint.deploy_index(
            index=index,
            deployed_index_id="cpt-deployed-index",
            display_name="CPT Vector Search Deployed Index",
            machine_type=config['machine_type'],
            min_replica_count=1,
            max_replica_count=2
        )
        
        print(f"✅ Index deployment initiated successfully!")
        print(f"📍 Deployed index ID: cpt-deployed-index")
        
        # Save deployment info
        config['deployed_index_id'] = "cpt-deployed-index"
        config['deployment_status'] = "deploying"
        
        with open('vertex_ai_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return deployed_index
        
    except Exception as e:
        print(f"❌ Error deploying index: {e}")
        return None

def main():
    """Main setup function"""
    print("=" * 80)
    print("VERTEX AI VECTOR SEARCH SETUP")
    print("=" * 80)
    
    # Set up authentication
    setup_authentication()
    
    # Create bucket and upload data
    bucket_name = create_storage_bucket()
    if not bucket_name:
        print("❌ Failed to create bucket")
        return False
    
    gcs_path = upload_vectors_to_storage(bucket_name)
    if not gcs_path:
        print("❌ Failed to upload vectors")
        return False
    
    # Create index
    index = create_vector_search_index(gcs_path)
    if not index:
        print("❌ Failed to create index")
        return False
    
    # Create endpoint
    endpoint = create_vector_search_endpoint()
    if not endpoint:
        print("❌ Failed to create endpoint")
        return False
    
    # Deploy index to endpoint
    deployed_index = deploy_index_to_endpoint(index, endpoint)
    if deployed_index is None:  # Can be False or an object
        print("❌ Failed to start deployment")
        return False
    
    print("\n" + "=" * 80)
    print("🎉 VERTEX AI VECTOR SEARCH SETUP COMPLETE!")
    print("=" * 80)
    print(f"📦 Bucket: gs://{bucket_name}")
    print(f"📁 Data: {gcs_path}")
    print(f"🔍 Index: {config.get('index_resource_name', 'Created')}")
    print(f"🌐 Endpoint: {config.get('endpoint_resource_name', 'Created')}")
    print(f"🚀 Deployment: In Progress (30-45 minutes)")
    
    print(f"\n📋 Next Steps:")
    print(f"1. Wait for deployment to complete (~30-45 minutes)")
    print(f"2. Test vector search functionality") 
    print(f"3. Update Cloud Function to use Vertex AI")
    print(f"4. Test end-to-end system")
    
    print(f"\n💡 Monitor deployment status:")
    print(f"   Check vertex_ai_config.json for resource names")
    print(f"   Use Google Cloud Console to monitor progress")
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)