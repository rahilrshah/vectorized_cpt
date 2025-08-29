
import pandas as pd
from config import default_csv_path, description_column, collection_name, cred_path, vertex_project, vertex_location, vertex_model, vertex_batch_size, vertex_task_type
from firebase_utils import init_firestore
import numpy as np
import scipy.sparse

# --- LOAD DATA ---
from vertex_ai_utils import get_vertex_embeddings

def load_vectors_and_data(csv_path, description_column, project=None, location=None, model=None, task_type=None, batch_size=32):
    try:
        df = pd.read_csv(csv_path)
        if description_column not in df.columns:
            print(f"Column '{description_column}' not found in CSV.")
            return None, None
        descriptions = df[description_column].fillna("").astype(str).tolist()
        if not all([project, location, model, task_type]):
            print("Vertex AI project, location, model, and task_type must be provided.")
            return None, None
        vectors = get_vertex_embeddings(descriptions, project, location, model, task_type, batch_size)
        return df, vectors
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None

# --- FIREBASE INIT ---
# Now imported from firebase_utils.py

# --- UPLOAD TO FIRESTORE ---
def upload_vectors_to_firestore(df, vectors, db, collection_name):
    try:
        for idx, row in df.iterrows():
            vector = vectors[idx] if isinstance(vectors[idx], list) else vectors[idx].toarray().flatten().tolist()
            doc_data = row.to_dict()
            # Ensure consistent field naming for CPT codes
            if 'CPT Codes' in doc_data:
                doc_data['cpt_code'] = doc_data['CPT Codes']
            doc_data['vector'] = vector
            db.collection(collection_name).add(doc_data)
        print('Upload complete!')
    except Exception as e:
        print(f"Error uploading to Firestore: {e}")

if __name__ == '__main__':
    # This allows running the script directly for testing
    df, vectors = load_vectors_and_data(
        default_csv_path,
        description_column,
        project=vertex_project,
        location=vertex_location,
        model=vertex_model,
        task_type=vertex_task_type,
        batch_size=vertex_batch_size
    )
    if df is not None and vectors is not None:
        db = init_firestore(cred_path)
        if db:
            upload_vectors_to_firestore(df, vectors, db, collection_name)
