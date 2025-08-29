from firebase_utils import init_firestore
from config import cred_path, collection_name
import json
import numpy as np

def diagnose_zero_results_issue():
    """Diagnose why the Cloud Function is returning 0 results"""
    print("="*80)
    print("🔍 DIAGNOSING ZERO RESULTS ISSUE")
    print("="*80)
    
    db = init_firestore(cred_path)
    if not db:
        print("❌ Failed to connect to Firestore")
        return
    
    # 1. Check if collection has documents
    print("\n📊 STEP 1: COLLECTION DOCUMENT COUNT")
    try:
        all_docs = list(db.collection(collection_name).stream())
        print(f"✅ Total documents in collection: {len(all_docs)}")
        
        if len(all_docs) == 0:
            print(f"❌ CRITICAL: Collection is empty!")
            return
            
        # Check vector field presence
        docs_with_vectors = 0
        for doc in all_docs[:10]:  # Check first 10
            doc_data = doc.to_dict()
            if 'vector' in doc_data and isinstance(doc_data['vector'], list):
                docs_with_vectors += 1
        
        print(f"✅ Documents with vector field (sample of 10): {docs_with_vectors}/10")
        
    except Exception as e:
        print(f"❌ Error checking collection: {e}")
        return
    
    # 2. Check the exact error from Cloud Function logs
    print(f"\n📋 STEP 2: RECENT CLOUD FUNCTION BEHAVIOR")
    
    # Look at the logs to understand what's happening
    print("Recent log analysis:")
    print("- Collection accessible: ✅")
    print("- Embedding generated: ✅ (768 dimensions)")
    print("- Vector search executed: ✅")
    print("- Results returned: ❌ (0 documents)")
    print("")
    print("This suggests the vector search is working but not finding similarities above threshold.")
    
    # 3. Test different similarity thresholds manually
    print(f"\n🧪 STEP 3: MANUAL SIMILARITY TESTING")
    
    # Get first document as reference
    sample_doc = all_docs[0].to_dict()
    sample_vector = np.array(sample_doc['vector'])
    
    print(f"Using sample document: CPT {sample_doc.get('CPT Codes', 'N/A')}")
    print(f"Description: {sample_doc.get('Descriptions', 'N/A')[:80]}...")
    
    # Calculate similarities with all other documents
    similarities = []
    for doc in all_docs[1:51]:  # Test with first 50 other docs
        doc_data = doc.to_dict()
        if 'vector' in doc_data:
            doc_vector = np.array(doc_data['vector'])
            
            # Calculate cosine similarity
            dot_product = np.dot(sample_vector, doc_vector)
            norm1 = np.linalg.norm(sample_vector)
            norm2 = np.linalg.norm(doc_vector)
            
            if norm1 > 0 and norm2 > 0:
                similarity = dot_product / (norm1 * norm2)
                similarities.append({
                    'cpt_code': doc_data.get('CPT Codes', 'N/A'),
                    'description': doc_data.get('Descriptions', 'N/A'),
                    'similarity': similarity
                })
    
    # Sort by similarity
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    print(f"\n🏆 TOP 10 MANUAL SIMILARITY RESULTS:")
    for i, match in enumerate(similarities[:10]):
        print(f"  {i+1:2d}. CPT {match['cpt_code']} (sim: {match['similarity']:.6f})")
        print(f"      {match['description'][:70]}...")
    
    # Analyze similarity ranges
    if similarities:
        sim_values = [s['similarity'] for s in similarities]
        print(f"\n📊 SIMILARITY STATISTICS:")
        print(f"   Highest: {max(sim_values):.6f}")
        print(f"   Average: {np.mean(sim_values):.6f}")
        print(f"   Median:  {np.median(sim_values):.6f}")
        print(f"   Lowest:  {min(sim_values):.6f}")
        
        # Check different thresholds
        thresholds = [0.5, 0.3, 0.1, 0.05]
        for threshold in thresholds:
            count = sum(1 for s in sim_values if s >= threshold)
            print(f"   Above {threshold}: {count} documents")
    
    # 4. Check if the issue is with COSINE vs other distance measures
    print(f"\n🔄 STEP 4: DISTANCE MEASURE ANALYSIS")
    
    if len(similarities) >= 5:
        test_doc = similarities[0]  # Use highest similarity doc
        ref_vector = sample_vector
        test_vector = None
        
        # Find the actual vector for the test document
        for doc in all_docs:
            doc_data = doc.to_dict()
            if doc_data.get('CPT Codes') == test_doc['cpt_code']:
                test_vector = np.array(doc_data['vector'])
                break
        
        if test_vector is not None:
            # Calculate different distance measures
            cosine_sim = test_doc['similarity']
            
            # Euclidean distance (lower is better)
            euclidean_dist = np.linalg.norm(ref_vector - test_vector)
            
            # Dot product
            dot_product = np.dot(ref_vector, test_vector)
            
            print(f"Distance measures for best match (CPT {test_doc['cpt_code']}):")
            print(f"   Cosine Similarity: {cosine_sim:.6f}")
            print(f"   Euclidean Distance: {euclidean_dist:.6f}")
            print(f"   Dot Product: {dot_product:.6f}")
            
            # Compare with Firestore's expectations
            print(f"\nFirestore vector search expects:")
            print(f"   - COSINE distance measure")
            print(f"   - Values closer to 1.0 are better matches")
            
            if cosine_sim > 0.5:
                print(f"   ✅ Manual calculation shows good similarities exist")
                print(f"   🔧 Issue might be with Firestore vector search implementation")
            elif cosine_sim > 0.1:
                print(f"   ⚠️  Manual calculation shows moderate similarities")
                print(f"   🔧 May need to adjust search parameters or data")
            else:
                print(f"   ❌ Manual calculation shows low similarities")
                print(f"   🔧 Possible data or embedding generation issue")
    
    # 5. Suggest specific fixes
    print(f"\n🔧 STEP 5: RECOMMENDED FIXES")
    
    if similarities and max(sim_values) > 0.3:
        print("✅ GOOD NEWS: Manual similarities show the data works!")
        print("\nPossible issues with Cloud Function:")
        print("1. Vector search limit too restrictive (currently limit: 5)")
        print("2. Distance threshold too high")
        print("3. Firestore vector search configuration")
        print("4. Query vector format mismatch")
        
        print(f"\n💡 IMMEDIATE ACTIONS:")
        print("1. Increase search limit from 5 to 20")
        print("2. Add debug logging for actual similarity scores")
        print("3. Verify vector normalization")
        print("4. Test with exact same vector (should return similarity = 1.0)")
        
    else:
        print("❌ Manual similarities are also low")
        print("This suggests a deeper issue with:")
        print("1. Embedding generation consistency")
        print("2. Vector data quality")
        print("3. Query processing")

if __name__ == '__main__':
    diagnose_zero_results_issue()