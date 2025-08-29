#!/usr/bin/env python3
"""
Export vectors from Firestore to JSONL format for Vertex AI Vector Search
"""

import json
import os
from firebase_utils import init_firestore
from config import cred_path, collection_name, vertex_project, vertex_location

def export_vectors_to_jsonl():
    """Export all vectors from Firestore to JSONL format for Vertex AI"""
    print("=" * 80)
    print("EXPORTING VECTORS TO VERTEX AI FORMAT")
    print("=" * 80)
    
    # Initialize Firestore
    db = init_firestore(cred_path)
    if not db:
        print("❌ Failed to initialize Firestore")
        return False
    
    collection_ref = db.collection(collection_name)
    
    # Get all documents
    print("📊 Fetching all documents from Firestore...")
    docs = list(collection_ref.stream())
    print(f"✅ Retrieved {len(docs)} documents")
    
    if len(docs) == 0:
        print("❌ No documents found in collection")
        return False
    
    # Prepare JSONL data
    jsonl_data = []
    valid_docs = 0
    
    print("\n🔄 Processing documents...")
    for i, doc in enumerate(docs):
        doc_data = doc.to_dict()
        
        # Check if document has required fields
        if 'vector' not in doc_data or 'CPT Codes' not in doc_data:
            print(f"⚠️  Skipping document {doc.id} - missing required fields")
            continue
            
        vector = doc_data['vector']
        if not isinstance(vector, list) or len(vector) != 768:
            print(f"⚠️  Skipping document {doc.id} - invalid vector")
            continue
        
        # Create the JSONL entry in the format expected by Vertex AI
        entry = {
            "id": f"cpt_{doc_data.get('CPT Codes', doc.id)}",  # Use CPT code as ID
            "embedding": vector,  # The 768-dimensional vector
            # Metadata for retrieval
            "restricts": [
                {"namespace": "cpt_code", "allow": [str(doc_data.get('CPT Codes', ''))]}
            ],
            # Additional metadata
            "cpt_code": str(doc_data.get('CPT Codes', '')),
            "description": doc_data.get('Descriptions', ''),
            "category": doc_data.get('Procedure Code Category', ''),
            "status": doc_data.get('Code Status', ''),
            "firestore_id": doc.id
        }
        
        jsonl_data.append(entry)
        valid_docs += 1
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(docs)} documents...")
    
    print(f"✅ Processed {valid_docs} valid documents out of {len(docs)} total")
    
    # Write to JSONL file
    output_file = "cpt_vectors.jsonl"
    print(f"\n💾 Writing to {output_file}...")
    
    try:
        with open(output_file, 'w') as f:
            for entry in jsonl_data:
                json.dump(entry, f)
                f.write('\n')
        
        print(f"✅ Successfully wrote {len(jsonl_data)} entries to {output_file}")
        
        # Show file size
        file_size = os.path.getsize(output_file)
        file_size_mb = file_size / (1024 * 1024)
        print(f"📁 File size: {file_size_mb:.2f} MB")
        
        # Show sample entry
        print(f"\n📋 Sample JSONL entry:")
        print(json.dumps(jsonl_data[0], indent=2)[:500] + "...")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error writing JSONL file: {e}")
        return False

def create_vertex_config():
    """Create configuration for Vertex AI setup"""
    config = {
        "project_id": vertex_project,
        "location": vertex_location,
        "bucket_name": f"{vertex_project}-vector-search",
        "index_name": "cpt-vector-search-index",
        "endpoint_name": "cpt-vector-search-endpoint",
        "dimensions": 768,
        "distance_measure": "COSINE_DISTANCE",
        "machine_type": "e2-standard-2"  # Cost-effective option
    }
    
    config_file = "vertex_ai_config.json"
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n⚙️  Vertex AI configuration saved to {config_file}")
        print(f"📋 Configuration:")
        for key, value in config.items():
            print(f"   {key}: {value}")
            
        return config_file
        
    except Exception as e:
        print(f"❌ Error writing config file: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Starting Vertex AI Vector Search migration...")
    
    # Export vectors
    jsonl_file = export_vectors_to_jsonl()
    
    if jsonl_file:
        # Create config
        config_file = create_vertex_config()
        
        if config_file:
            print(f"\n🎉 DATA EXPORT COMPLETE!")
            print(f"📁 JSONL file: {jsonl_file}")
            print(f"⚙️  Config file: {config_file}")
            print(f"\n📋 Next steps:")
            print(f"1. Upload {jsonl_file} to Cloud Storage")
            print(f"2. Create Vertex AI Vector Search index")
            print(f"3. Deploy index to endpoint")
        else:
            print(f"\n⚠️  Export completed but config creation failed")
    else:
        print(f"\n❌ Export failed!")