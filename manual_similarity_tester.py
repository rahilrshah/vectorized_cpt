import numpy as np
from firebase_utils import init_firestore
from config import cred_path, collection_name
import json

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot_product / (norm1 * norm2)

def manual_similarity_analysis():
    """Test similarity calculations manually to understand why no matches are found"""
    print("=" * 80)
    print("MANUAL SIMILARITY ANALYSIS")
    print("=" * 80)
    
    # Initialize Firestore
    db = init_firestore(cred_path)
    if not db:
        print("❌ Failed to initialize Firestore")
        return
    
    # 1. Get all vectors and find knee-related ones
    print("\n🔍 STEP 1: LOADING ALL VECTORS AND FINDING KNEE PROCEDURES")
    
    all_docs = list(db.collection(collection_name).stream())
    print(f"✅ Loaded {len(all_docs)} total documents")
    
    knee_docs = []
    other_docs = []
    knee_keywords = ['knee', 'arthroplasty', 'patella', 'meniscus', 'cruciate', 'femoral', 'tibial']
    
    for doc in all_docs:
        doc_data = doc.to_dict()
        if 'Descriptions' in doc_data and 'vector' in doc_data:
            description = str(doc_data['Descriptions']).lower()
            if any(keyword in description for keyword in knee_keywords):
                knee_docs.append(doc_data)
            else:
                other_docs.append(doc_data)
    
    print(f"✅ Found {len(knee_docs)} knee-related procedures")
    print(f"✅ Found {len(other_docs)} other procedures")
    
    # Show knee procedures
    print(f"\n🦵 KNEE PROCEDURES FOUND:")
    for i, doc in enumerate(knee_docs[:10]):
        print(f"{i+1:2d}. CPT {doc.get('CPT Codes', 'N/A')}: {doc['Descriptions'][:100]}...")
    
    if len(knee_docs) > 10:
        print(f"    ... and {len(knee_docs) - 10} more")
    
    # 2. Test similarity between knee procedures
    print(f"\n📊 STEP 2: TESTING SIMILARITY BETWEEN KNEE PROCEDURES")
    
    if len(knee_docs) >= 2:
        similarities = []
        
        for i in range(min(5, len(knee_docs))):
            for j in range(i+1, min(5, len(knee_docs))):
                vec1 = np.array(knee_docs[i]['vector'])
                vec2 = np.array(knee_docs[j]['vector'])
                similarity = cosine_similarity(vec1, vec2)
                similarities.append(similarity)
                
                print(f"\nSimilarity between knee procedures {i+1} and {j+1}:")
                print(f"  CPT {knee_docs[i].get('CPT Codes')}: {knee_docs[i]['Descriptions'][:50]}...")
                print(f"  CPT {knee_docs[j].get('CPT Codes')}: {knee_docs[j]['Descriptions'][:50]}...")
                print(f"  Cosine Similarity: {similarity:.6f}")
        
        if similarities:
            avg_knee_similarity = np.mean(similarities)
            max_knee_similarity = max(similarities)
            print(f"\n📈 KNEE PROCEDURE SIMILARITY STATS:")
            print(f"  Average: {avg_knee_similarity:.6f}")
            print(f"  Maximum: {max_knee_similarity:.6f}")
            print(f"  Range: [{min(similarities):.6f}, {max_knee_similarity:.6f}]")
    
    # 3. Test similarity between knee and non-knee procedures
    print(f"\n🔄 STEP 3: TESTING KNEE vs NON-KNEE SIMILARITY")
    
    if knee_docs and other_docs:
        cross_similarities = []
        
        # Test first 3 knee procedures against first 10 other procedures
        for i in range(min(3, len(knee_docs))):
            knee_vec = np.array(knee_docs[i]['vector'])
            best_match = None
            best_similarity = -1
            
            for j in range(min(10, len(other_docs))):
                other_vec = np.array(other_docs[j]['vector'])
                similarity = cosine_similarity(knee_vec, other_vec)
                cross_similarities.append(similarity)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = other_docs[j]
            
            print(f"\nBest non-knee match for knee procedure {i+1}:")
            print(f"  Knee: CPT {knee_docs[i].get('CPT Codes')} - {knee_docs[i]['Descriptions'][:60]}...")
            print(f"  Match: CPT {best_match.get('CPT Codes')} - {best_match['Descriptions'][:60]}...")
            print(f"  Similarity: {best_similarity:.6f}")
        
        if cross_similarities:
            avg_cross_similarity = np.mean(cross_similarities)
            max_cross_similarity = max(cross_similarities)
            print(f"\n📈 CROSS-CATEGORY SIMILARITY STATS:")
            print(f"  Average: {avg_cross_similarity:.6f}")
            print(f"  Maximum: {max_cross_similarity:.6f}")
            print(f"  Range: [{min(cross_similarities):.6f}, {max_cross_similarity:.6f}]")
    
    # 4. Simulate the Cloud Function search process
    print(f"\n🤖 STEP 4: SIMULATING CLOUD FUNCTION SEARCH")
    
    # Simulate what happens when we search for a knee procedure
    if knee_docs:
        # Use the first knee procedure as our "query"
        query_doc = knee_docs[0]
        query_vector = np.array(query_doc['vector'])
        
        print(f"Query (simulating Gemini output): {query_doc['Descriptions']}")
        
        # Search through all documents (like the Cloud Function would)
        matches = []
        for doc in all_docs:
            doc_data = doc.to_dict()
            if 'vector' in doc_data:
                doc_vector = np.array(doc_data['vector'])
                similarity = cosine_similarity(query_vector, doc_vector)
                matches.append({
                    'cpt_code': doc_data.get('CPT Codes', 'N/A'),
                    'description': doc_data.get('Descriptions', 'N/A'),
                    'similarity': similarity
                })
        
        # Sort by similarity (like Firestore vector search would)
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        print(f"\n🏆 TOP 10 MATCHES FROM SIMULATED SEARCH:")
        for i, match in enumerate(matches[:10]):
            marker = "🎯" if i == 0 else "  "  # Mark the exact match
            print(f"{marker} {i+1:2d}. CPT {match['cpt_code']} (sim: {match['similarity']:.6f})")
            print(f"      {match['description'][:100]}...")
        
        # Analysis
        top_similarity = matches[0]['similarity']
        if top_similarity == 1.0:
            print(f"\n✅ PERFECT: Found exact match (similarity = 1.0)")
        elif top_similarity > 0.9:
            print(f"\n✅ EXCELLENT: Top match has high similarity ({top_similarity:.6f})")
        elif top_similarity > 0.5:
            print(f"\n⚠️  MODERATE: Top match has moderate similarity ({top_similarity:.6f})")
        else:
            print(f"\n❌ POOR: Top match has low similarity ({top_similarity:.6f})")
        
        # Check if any knee procedures appear in top 10
        knee_in_top10 = sum(1 for match in matches[:10] if any(kw in match['description'].lower() for kw in knee_keywords))
        print(f"   Knee procedures in top 10: {knee_in_top10}")
    
    # 5. Analyze typical similarity ranges
    print(f"\n📏 STEP 5: ANALYZING TYPICAL SIMILARITY RANGES")
    
    # Sample random similarities
    random_similarities = []
    import random
    
    for _ in range(100):
        doc1 = random.choice(all_docs).to_dict()
        doc2 = random.choice(all_docs).to_dict()
        
        if 'vector' in doc1 and 'vector' in doc2:
            vec1 = np.array(doc1['vector'])
            vec2 = np.array(doc2['vector'])
            sim = cosine_similarity(vec1, vec2)
            random_similarities.append(sim)
    
    if random_similarities:
        print(f"Random similarity statistics (100 random pairs):")
        print(f"  Mean: {np.mean(random_similarities):.6f}")
        print(f"  Std:  {np.std(random_similarities):.6f}")
        print(f"  Min:  {min(random_similarities):.6f}")
        print(f"  Max:  {max(random_similarities):.6f}")
        print(f"  90th percentile: {np.percentile(random_similarities, 90):.6f}")
        print(f"  95th percentile: {np.percentile(random_similarities, 95):.6f}")
    
    print("\n" + "=" * 80)
    print("MANUAL SIMILARITY ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    manual_similarity_analysis()