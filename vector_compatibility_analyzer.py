import os
import numpy as np
from firebase_utils import init_firestore
from config import cred_path, collection_name, vertex_project, vertex_location, vertex_model
import json
import math

# Set up authentication for Vertex AI
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot_product / (norm1 * norm2)

def euclidean_distance(vec1, vec2):
    """Calculate Euclidean distance between two vectors"""
    return np.linalg.norm(np.array(vec1) - np.array(vec2))

def generate_embedding_with_vertex_ai(text, project_id, location, model_name):
    """Generate embedding using Vertex AI (matching the Cloud Function exactly)"""
    try:
        # Use the exact same approach as the Cloud Function
        from google.cloud.aiplatform import v1
        
        # Initialize client
        client_options = {
            "api_endpoint": f"{location}-aiplatform.googleapis.com"
        }
        prediction_service_client = v1.PredictionServiceClient(client_options)
        endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_name}"

        # Create instance exactly like the Cloud Function
        instance = {
            "structValue": {
                "fields": {
                    "content": {"stringValue": text},
                    "task_type": {"stringValue": "RETRIEVAL_DOCUMENT"}
                }
            }
        }
        
        instances = [instance]
        request_payload = {"endpoint": endpoint, "instances": instances}
        
        # Make the prediction
        response = prediction_service_client.predict(**request_payload)
        
        # Extract embeddings exactly like the Cloud Function
        prediction = response.predictions[0]
        values = prediction.struct_value.fields["embeddings"].struct_value.fields["values"].list_value.values
        embedding = [v.number_value for v in values]
        
        return embedding
        
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        print(f"   Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return None

def analyze_vector_compatibility():
    """Comprehensive vector compatibility analysis"""
    print("=" * 80)
    print("VECTOR COMPATIBILITY ANALYSIS")
    print("=" * 80)
    
    # Initialize Firestore
    db = init_firestore(cred_path)
    if not db:
        print("❌ Failed to initialize Firestore")
        return
    
    # 1. Get sample stored vectors
    print("\n🔍 STEP 1: RETRIEVING STORED VECTORS")
    try:
        docs = list(db.collection(collection_name).limit(5).stream())
        stored_vectors = []
        stored_descriptions = []
        
        for i, doc in enumerate(docs):
            doc_data = doc.to_dict()
            if 'vector' in doc_data and 'Descriptions' in doc_data:
                stored_vectors.append(doc_data['vector'])
                stored_descriptions.append(doc_data['Descriptions'])
                print(f"✅ Doc {i+1}: {doc_data.get('CPT Codes', 'N/A')} - {doc_data['Descriptions'][:80]}...")
        
        print(f"✅ Retrieved {len(stored_vectors)} stored vectors")
        
    except Exception as e:
        print(f"❌ Error retrieving stored vectors: {e}")
        return
    
    # 2. Generate new embeddings for same descriptions
    print(f"\n🧠 STEP 2: GENERATING NEW EMBEDDINGS")
    print(f"Using: {vertex_model} in {vertex_location}")
    
    generated_vectors = []
    
    for i, description in enumerate(stored_descriptions):
        print(f"\nGenerating embedding {i+1}/5 for: {description[:50]}...")
        
        # Try using the same method as the Cloud Function
        embedding = generate_embedding_with_vertex_ai(
            description, vertex_project, vertex_location, vertex_model
        )
        
        if embedding:
            generated_vectors.append(embedding)
            print(f"✅ Generated vector dimension: {len(embedding)}")
            print(f"  Range: [{min(embedding):.6f}, {max(embedding):.6f}]")
        else:
            print("❌ Failed to generate embedding")
            
    print(f"\n✅ Generated {len(generated_vectors)} new embeddings")
    
    # 3. Compare stored vs generated embeddings
    print(f"\n📊 STEP 3: COMPARING STORED VS GENERATED EMBEDDINGS")
    
    if len(generated_vectors) == len(stored_vectors):
        similarities = []
        
        for i in range(len(stored_vectors)):
            stored_vec = np.array(stored_vectors[i])
            generated_vec = np.array(generated_vectors[i])
            
            # Calculate similarity
            cos_sim = cosine_similarity(stored_vec, generated_vec)
            eucl_dist = euclidean_distance(stored_vec, generated_vec)
            
            similarities.append(cos_sim)
            
            print(f"\nComparison {i+1}:")
            print(f"  Description: {stored_descriptions[i][:80]}...")
            print(f"  Cosine Similarity: {cos_sim:.6f}")
            print(f"  Euclidean Distance: {eucl_dist:.6f}")
            
            if cos_sim > 0.95:
                print(f"  ✅ EXCELLENT match")
            elif cos_sim > 0.8:
                print(f"  ⚠️  Good match")
            elif cos_sim > 0.5:
                print(f"  ⚠️  Moderate match")
            else:
                print(f"  ❌ POOR match - potential issue!")
        
        avg_similarity = np.mean(similarities)
        print(f"\n📈 AVERAGE COSINE SIMILARITY: {avg_similarity:.6f}")
        
        if avg_similarity > 0.95:
            print("✅ EMBEDDINGS ARE HIGHLY CONSISTENT")
        elif avg_similarity > 0.8:
            print("⚠️  EMBEDDINGS ARE SOMEWHAT CONSISTENT")
        else:
            print("❌ EMBEDDINGS ARE INCONSISTENT - MAJOR ISSUE!")
    
    # 4. Test with knee surgery query
    print(f"\n🦵 STEP 4: TESTING WITH KNEE SURGERY QUERY")
    
    # This is similar to what would come from Gemini
    test_query = "Bilateral total knee arthroplasty with patellar resurfacing; Right knee lateral release."
    print(f"Test Query: {test_query}")
    
    query_embedding = generate_embedding_with_vertex_ai(
        test_query, vertex_project, vertex_location, vertex_model
    )
    
    if query_embedding:
        print(f"✅ Query embedding generated, dimension: {len(query_embedding)}")
        
        # Find best matches from stored vectors
        print("\n🔍 SEARCHING FOR BEST MATCHES:")
        
        all_docs = list(db.collection(collection_name).stream())
        best_matches = []
        
        for doc in all_docs[:50]:  # Test first 50 for speed
            doc_data = doc.to_dict()
            if 'vector' in doc_data:
                stored_vec = np.array(doc_data['vector'])
                query_vec = np.array(query_embedding)
                
                similarity = cosine_similarity(stored_vec, query_vec)
                
                if similarity > 0.1:  # Only keep reasonable matches
                    best_matches.append({
                        'cpt_code': doc_data.get('CPT Codes', 'N/A'),
                        'description': doc_data.get('Descriptions', 'N/A'),
                        'similarity': similarity
                    })
        
        # Sort by similarity
        best_matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        print(f"\n🏆 TOP 10 MATCHES (from first 50 docs):")
        for i, match in enumerate(best_matches[:10]):
            print(f"{i+1:2d}. CPT {match['cpt_code']} (sim: {match['similarity']:.4f})")
            print(f"     {match['description'][:100]}...")
        
        if best_matches:
            best_sim = best_matches[0]['similarity']
            if best_sim > 0.5:
                print(f"\n✅ FOUND GOOD MATCHES! Best similarity: {best_sim:.4f}")
            elif best_sim > 0.2:
                print(f"\n⚠️  Found moderate matches. Best similarity: {best_sim:.4f}")
            else:
                print(f"\n❌ POOR MATCHES. Best similarity: {best_sim:.4f}")
        else:
            print(f"\n❌ NO MATCHES FOUND ABOVE THRESHOLD!")
    
    else:
        print("❌ Failed to generate query embedding")
    
    print("\n" + "=" * 80)
    print("VECTOR COMPATIBILITY ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    analyze_vector_compatibility()