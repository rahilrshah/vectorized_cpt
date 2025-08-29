

import sys
from config import default_csv_path, description_column, collection_name, cred_path, vertex_project, vertex_location, vertex_model, vertex_batch_size, vertex_task_type
from firebase_utils import init_firestore
from upload_vectors_to_firestore import load_vectors_and_data, upload_vectors_to_firestore


def main():
    # Get CSV path from command-line argument if provided
    csv_path = sys.argv[1] if len(sys.argv) > 1 else default_csv_path
    print(f'Using CSV file: {csv_path}')
    df, vectors = load_vectors_and_data(
        csv_path,
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
        else:
            print('Failed to initialize Firestore.')
    else:
        print('Failed to load data or vectorize descriptions.')

if __name__ == '__main__':
    main()
