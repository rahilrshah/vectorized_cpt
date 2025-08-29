import firebase_admin
from firebase_admin import credentials, firestore

def init_firestore(cred_path):
    try:
        # Check if Firebase is already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        return db
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        return None
