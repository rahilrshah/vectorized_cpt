
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from typing import List
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

def get_vertex_embeddings(descriptions: List[str], project: str, location: str, model: str, task_type: str, batch_size: int = 32) -> List[List[float]]:
    """
    Get embeddings from Vertex AI for a list of descriptions in batches using REST API.
    Returns a list of embedding vectors.
    """
    print("Authenticating with Google Cloud...")
    # Load service account credentials from config.py
    cred_path = config.cred_path
    credentials = service_account.Credentials.from_service_account_file(
        cred_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    access_token = credentials.token
    print("Authentication successful.")
    endpoint_url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/google/models/{model}:predict"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    embeddings = []
    num_descriptions = len(descriptions)
    total_batches = (num_descriptions + batch_size - 1) // batch_size
    print(f"Getting embeddings for {num_descriptions} descriptions in {total_batches} batches...")

    for i in range(0, num_descriptions, batch_size):
        batch = descriptions[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        print(f"  Processing batch {batch_num}/{total_batches}...")
        instances = [
            {"content": d, "task_type": task_type}
            for d in batch
        ]
        payload = {"instances": instances}
        try:
            # Added a 60-second timeout to prevent indefinite hanging
            response = requests.post(endpoint_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            print(f"\nError: The request to Vertex AI timed out on batch {batch_num}.")
            print("This could be due to network issues or a slow API response. Consider increasing the timeout or reducing 'vertex_batch_size' in config.py.")
            raise
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e}")
            print(f"Response body: {response.text}")
            raise
        predictions = response.json()["predictions"]
        for pred in predictions:
            # The embedding values are in pred['embeddings']['values']
            embeddings.append(pred["embeddings"]["values"])

    print("Finished getting all embeddings.")
    return embeddings
