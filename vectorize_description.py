import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

csv_path = 'your-data-file.csv'  # Change this to your CSV file name
description_column = 'Descriptions'  # Change this if your column has a different name

def vectorize_descriptions(path, column):
    try:
        df = pd.read_csv(path)
        if column not in df.columns:
            print(f"Column '{column}' not found in CSV.")
            return None
        descriptions = df[column].fillna("").astype(str)
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(descriptions)
        print('Vectorization complete!')
        print('Shape:', vectors.shape)
        return vectors, vectorizer
    except FileNotFoundError:
        print(f'File not found: {path}')
    except Exception as e:
        print(f'Error: {e}')
    return None, None

if __name__ == '__main__':
    vectorize_descriptions(csv_path, description_column)
