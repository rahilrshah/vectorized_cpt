from firebase_utils import init_firestore
import pandas as pd


# Path to your Firebase Admin SDK JSON file
cred_path = 'cpt-code-vectorized-dataset-firebase-adminsdk-fbsvc-2c5f693340.json'

db = init_firestore(cred_path)
if db is None:
    exit(1)

# Example: Fetch all documents from a collection
collection_name = 'your-collection-name'  # Change this to your Firestore collection

try:
    docs = db.collection(collection_name).stream()
    data = []
    for doc in docs:
        row = doc.to_dict()
        row['id'] = doc.id
        data.append(row)

    # Convert to pandas DataFrame
    if data:
        df = pd.DataFrame(data)
        print(df.head())
    else:
        print('No documents found in the collection.')
except Exception as e:
    print(f"Error accessing Firestore: {e}")
