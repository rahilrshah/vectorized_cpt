#!/usr/bin/env python3
"""
Continue Vertex AI setup - create endpoint and deploy existing index
"""

import json
import os
from google.cloud import aiplatform
from config import vertex_project, vertex_location, cred_path

# Load configuration
with open('vertex_ai_config.json', 'r') as f:
    config = json.load(f)

def setup_authentication():
    """Set up Google Cloud authentication"""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
    print(f"✅ Authentication set up using {cred_path}")

def create_vector_search_endpoint():
    """Create Vertex AI Vector Search endpoint"""
    print(f"\n🌐 Creating Vertex AI Vector Search endpoint...")
    
    try:
        # Initialize Vertex AI
        aiplatform.init(
            project=config['project_id'],
            location=config['location']
        )
        
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

def deploy_index_to_endpoint():
    """Deploy the existing index to the endpoint"""
    print(f"\n🚀 Deploying index to endpoint...")
    print(f"⚠️  This operation takes approximately 30-45 minutes...")
    
    try:
        # Initialize Vertex AI
        aiplatform.init(
            project=config['project_id'],
            location=config['location']
        )
        
        # Get the existing index
        index = aiplatform.MatchingEngineIndex(config['index_resource_name'])
        print(f"✅ Found existing index: {index.display_name}")
        
        # Get the endpoint we just created
        endpoint = aiplatform.MatchingEngineIndexEndpoint(config['endpoint_resource_name'])
        print(f"✅ Found endpoint: {endpoint.display_name}")
        
        # Deploy index to endpoint
        deployed_index = endpoint.deploy_index(
            index=index,
            deployed_index_id="cpt_deployed_index",  # Use underscores instead of hyphens
            display_name="CPT Vector Search Deployed Index",
            machine_type=config['machine_type'],
            min_replica_count=1,
            max_replica_count=2
        )
        
        print(f"✅ Index deployment initiated successfully!")
        print(f"📍 Deployed index ID: cpt_deployed_index")
        
        # Save deployment info
        config['deployed_index_id'] = "cpt_deployed_index"
        config['deployment_status'] = "deploying"
        
        with open('vertex_ai_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return deployed_index
        
    except Exception as e:
        print(f"❌ Error deploying index: {e}")
        return None

def main():
    """Main continuation function"""
    print("=" * 80)
    print("CONTINUING VERTEX AI VECTOR SEARCH SETUP")
    print("=" * 80)
    
    # Set up authentication
    setup_authentication()
    
    # Show current status
    print(f"\n📋 Current Status:")
    print(f"✅ Index created: {config.get('index_resource_name', 'Not found')}")
    print(f"🔄 Creating endpoint and deploying...")
    
    # Create endpoint
    endpoint = create_vector_search_endpoint()
    if not endpoint:
        print("❌ Failed to create endpoint")
        return False
    
    # Deploy index to endpoint
    deployed_index = deploy_index_to_endpoint()
    if deployed_index is None:
        print("❌ Failed to start deployment")
        return False
    
    print("\n" + "=" * 80)
    print("🎉 VERTEX AI VECTOR SEARCH SETUP COMPLETE!")
    print("=" * 80)
    print(f"🔍 Index: {config.get('index_resource_name')}")
    print(f"🌐 Endpoint: {config.get('endpoint_resource_name')}")
    print(f"🚀 Deployment: In Progress (30-45 minutes)")
    
    print(f"\n📋 Next Steps:")
    print(f"1. Wait for deployment to complete (~30-45 minutes)")
    print(f"2. Create vector search utility functions") 
    print(f"3. Update Cloud Function to use Vertex AI")
    print(f"4. Test end-to-end system")
    
    print(f"\n💡 You can start working on the code while deployment runs in background")
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)