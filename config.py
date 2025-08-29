# config.py

# Path to your CSV file (default)
default_csv_path = 'CPT_Codes_Raw.csv'

# Path to saved vectors (optional)
vector_path = 'vectorized.npz'

description_column = 'Descriptions'  # Change if needed
collection_name = 'Vectorized_CPT_Test'  # Change to your Firestore collection
cred_path = 'cpt-code-vectorized-dataset-firebase-adminsdk-fbsvc-2c5f693340.json'  # Path to Firebase credentials

# Vertex AI config
vertex_project = 'cpt-code-vectorized-dataset'  # GCP project ID
vertex_location = 'us-central1'         # GCP region
vertex_model = 'text-embedding-004'  # Vertex AI embedding model
vertex_batch_size = 32
vertex_task_type = 'RETRIEVAL_DOCUMENT' # Task type for embeddings, e.g., RETRIEVAL_DOCUMENT, CLASSIFICATION, CLUSTERING
