import numpy as np

# This should match the path in your config.py
vector_path = 'vectorized.npz'

print(f"--- Verifying Vector File: {vector_path} ---")

try:
    with np.load(vector_path, allow_pickle=True) as data:
        if 'embeddings' not in data:
            print("ERROR: 'embeddings' key not found in the .npz file.")
            exit()
        
        embeddings = data['embeddings']

        print(f"Successfully loaded embeddings.")
        print(f"Shape of the embedding matrix: {embeddings.shape}")
        
        if len(embeddings.shape) != 2:
            print("ERROR: Embeddings are not a 2D matrix!")
        else:
            num_vectors, dimension = embeddings.shape
            print(f"Number of vectors: {num_vectors}")
            print(f"Vector dimension: {dimension}")

            if dimension != 768:
                print(f"CRITICAL ERROR: Vector dimension is {dimension}, but it MUST BE 768 for text-embedding-004.")
            else:
                print("SUCCESS: Vector dimension is correct (768).")

            # Check the data type of the numbers
            first_vector_element = embeddings[0][0]
            print(f"Data type of vector elements: {type(first_vector_element)}")

            if isinstance(first_vector_element, np.float32) or isinstance(first_vector_element, np.float64):
                print("SUCCESS: Data type appears to be a float, which is correct.")
            else:
                print(f"WARNING: Data type is {type(first_vector_element)}, which might be incorrect. It should be a float.")

except FileNotFoundError:
    print(f"ERROR: The file '{vector_path}' was not found. Please check the path.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("--- Verification Complete ---")