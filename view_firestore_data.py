import pandas as pd
from firebase_utils import init_firestore
from config import cred_path, collection_name

def view_firestore_collection(db, collection, limit=5):
    """
    Fetches and displays documents from a Firestore collection.
    """
    print(f"Fetching up to {limit} documents from collection '{collection}'...")
    try:
        docs = db.collection(collection).limit(limit).stream()
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            # Shorten the vector for a cleaner display
            if 'vector' in doc_data and isinstance(doc_data['vector'], list):
                preview = f"[{', '.join(map(str, doc_data['vector'][:4]))}, ...]"
                doc_data['vector_preview'] = preview
                del doc_data['vector']  # Remove the full vector from this preview
            data.append(doc_data)

        if not data:
            print("No documents found in the collection.")
            return

        # Convert to pandas DataFrame for nice printing
        df = pd.DataFrame(data)
        print("Successfully fetched data. Here's a preview:")
        print(df.to_string())

    except Exception as e:
        print(f"An error occurred while fetching data: {e}")

if __name__ == '__main__':
    db = init_firestore(cred_path)
    if db:
        view_firestore_collection(db, collection_name)