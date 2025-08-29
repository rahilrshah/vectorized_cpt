import pandas as pd

csv_path = 'your-data-file.csv'  # Change this to your CSV file name

def read_csv_to_dataframe(path):
    try:
        df = pd.read_csv(path)
        print('CSV loaded successfully!')
        print(df.head())
        return df
    except FileNotFoundError:
        print(f'File not found: {path}')
    except Exception as e:
        print(f'Error reading CSV: {e}')
    return None

if __name__ == '__main__':
    read_csv_to_dataframe(csv_path)
