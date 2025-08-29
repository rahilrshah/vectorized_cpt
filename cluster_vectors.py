import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Load your vectorized dataset (assume a CSV with 'id' and 'vector' columns)
# If your vectors are stored as lists in a column, you may need to convert them to arrays

def load_vectors(csv_path):
    df = pd.read_csv(csv_path)
    # Convert string representation of lists to actual lists if needed
    if isinstance(df['vector'].iloc[0], str):
        import ast
        df['vector'] = df['vector'].apply(ast.literal_eval)
    X = list(df['vector'])
    return df, X

def cluster_vectors(X, n_clusters=5):
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(X)
    return labels, kmeans

def plot_clusters(X, labels):
    # Reduce to 2D for visualization
    from sklearn.decomposition import PCA
    X_2d = PCA(n_components=2).fit_transform(X)
    plt.scatter(X_2d[:,0], X_2d[:,1], c=labels, cmap='tab10')
    plt.title('KMeans Clusters (PCA-reduced)')
    plt.xlabel('PC1')
    plt.ylabel('PC2')
    plt.show()

if __name__ == '__main__':
    csv_path = 'vectorized_dataset.csv'  # Update to your output file
    n_clusters = 5  # Set the number of clusters you want
    df, X = load_vectors(csv_path)
    labels, kmeans = cluster_vectors(X, n_clusters)
    df['cluster'] = labels
    df.to_csv('vectorized_dataset_with_clusters.csv', index=False)
    print('Cluster assignments saved to vectorized_dataset_with_clusters.csv')
    plot_clusters(X, labels)
