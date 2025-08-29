import pandas as pd
from firebase_utils import init_firestore
from config import cred_path, collection_name
import json

def comprehensive_firestore_analysis(db, collection, limit=10):
    """
    Enhanced Firestore collection analysis with comprehensive logging
    """
    print("=" * 80)
    print(f"COMPREHENSIVE FIRESTORE ANALYSIS: {collection}")
    print("=" * 80)
    
    # 1. Collection Overview
    print("\n🔍 COLLECTION OVERVIEW:")
    try:
        # Get total document count
        all_docs = list(db.collection(collection).stream())
        total_count = len(all_docs)
        print(f"✅ Total documents in collection: {total_count}")
        
        if total_count == 0:
            print("❌ CRITICAL: Collection is empty!")
            return
            
    except Exception as e:
        print(f"❌ ERROR accessing collection: {e}")
        return
    
    # 2. Document Structure Analysis
    print(f"\n📊 DOCUMENT STRUCTURE ANALYSIS (first {min(limit, total_count)} docs):")
    
    sample_docs = []
    vector_dimensions = []
    field_names = set()
    
    for i, doc in enumerate(all_docs[:limit]):
        doc_data = doc.to_dict()
        sample_docs.append(doc_data)
        
        # Collect all field names
        field_names.update(doc_data.keys())
        
        # Analyze vector field
        if 'vector' in doc_data:
            vector = doc_data['vector']
            if isinstance(vector, list):
                vector_dimensions.append(len(vector))
                print(f"  Doc {i+1}: Vector dimension = {len(vector)}")
                
                # Check vector value ranges
                if len(vector) > 0:
                    min_val = min(vector)
                    max_val = max(vector)
                    avg_val = sum(vector) / len(vector)
                    print(f"    Vector range: [{min_val:.6f}, {max_val:.6f}], avg: {avg_val:.6f}")
            else:
                print(f"  Doc {i+1}: ❌ Vector is not a list! Type: {type(vector)}")
        else:
            print(f"  Doc {i+1}: ❌ No 'vector' field found!")
    
    # 3. Field Analysis
    print(f"\n📋 FIELD ANALYSIS:")
    print(f"All field names found: {sorted(field_names)}")
    
    required_fields = ['vector', 'Descriptions', 'CPT Codes']
    for field in required_fields:
        if field in field_names:
            print(f"✅ {field}: Present")
        else:
            print(f"❌ {field}: MISSING")
    
    # 4. Vector Dimension Analysis
    print(f"\n🔢 VECTOR DIMENSION ANALYSIS:")
    if vector_dimensions:
        unique_dims = set(vector_dimensions)
        print(f"Unique vector dimensions found: {unique_dims}")
        
        if len(unique_dims) == 1:
            dim = list(unique_dims)[0]
            if dim == 768:
                print(f"✅ All vectors have correct dimension: {dim}")
            else:
                print(f"❌ CRITICAL: All vectors have dimension {dim}, but should be 768!")
        else:
            print(f"❌ CRITICAL: Inconsistent vector dimensions found!")
    else:
        print("❌ No valid vectors found!")
    
    # 5. CPT Code Analysis - Look for knee-related codes
    print(f"\n🦵 KNEE-RELATED CPT CODE SEARCH:")
    knee_keywords = ['knee', 'arthroplasty', 'patella', 'meniscus', 'cruciate', 'femoral', 'tibial']
    knee_related_docs = []
    
    for doc in sample_docs:
        if 'Descriptions' in doc:
            description = str(doc['Descriptions']).lower()
            if any(keyword in description for keyword in knee_keywords):
                knee_related_docs.append({
                    'cpt_code': doc.get('CPT Codes', 'N/A'),
                    'description': doc['Descriptions'][:100] + '...' if len(doc['Descriptions']) > 100 else doc['Descriptions']
                })
    
    if knee_related_docs:
        print(f"✅ Found {len(knee_related_docs)} knee-related procedures in sample:")
        for doc in knee_related_docs:
            print(f"  CPT {doc['cpt_code']}: {doc['description']}")
    else:
        print("⚠️  No knee-related procedures found in sample (checking larger dataset...)")
        
        # Search entire collection for knee procedures
        for doc in all_docs:
            doc_data = doc.to_dict()
            if 'Descriptions' in doc_data:
                description = str(doc_data['Descriptions']).lower()
                if any(keyword in description for keyword in knee_keywords):
                    knee_related_docs.append({
                        'cpt_code': doc_data.get('CPT Codes', 'N/A'),
                        'description': doc_data['Descriptions'][:100] + '...' if len(doc_data['Descriptions']) > 100 else doc_data['Descriptions']
                    })
        
        if knee_related_docs:
            print(f"✅ Found {len(knee_related_docs)} knee-related procedures in full dataset:")
            for doc in knee_related_docs[:5]:  # Show first 5
                print(f"  CPT {doc['cpt_code']}: {doc['description']}")
            if len(knee_related_docs) > 5:
                print(f"  ... and {len(knee_related_docs) - 5} more")
        else:
            print("❌ CRITICAL: No knee-related procedures found in entire dataset!")
    
    # 6. Sample Document Display
    print(f"\n📄 SAMPLE DOCUMENTS:")
    for i, doc in enumerate(sample_docs[:3]):
        print(f"\nDocument {i+1}:")
        doc_display = doc.copy()
        if 'vector' in doc_display:
            vector = doc_display['vector']
            if isinstance(vector, list) and len(vector) > 4:
                doc_display['vector'] = f"[{vector[0]:.6f}, {vector[1]:.6f}, {vector[2]:.6f}, {vector[3]:.6f}, ...] (len={len(vector)})"
        
        for key, value in doc_display.items():
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    db = init_firestore(cred_path)
    if db:
        comprehensive_firestore_analysis(db, collection_name, limit=20)
    else:
        print("❌ Failed to initialize Firestore connection")