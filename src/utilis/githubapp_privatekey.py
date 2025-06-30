import os
import json
from google.cloud import storage
from google.oauth2 import service_account

current_dir = os.path.dirname(os.path.abspath(__file__))

def get_github_app_private_key(url):
    """
    Downloads a GitHub App private key from a GCS URL and returns it as a string.
    """
    # Parse the GCS URL
    url=url.split('//')
    url=url[1]
    url=url.split('/')
    sa_key_json = os.getenv('SA_KEY')
    if not sa_key_json:
        raise ValueError("Environment variable SA_KEY not set")

    sa_info = json.loads(sa_key_json)

    # Create credentials from the service account info
    credentials = service_account.Credentials.from_service_account_info(sa_info)

    # Initialize the client with explicit credentials
    client = storage.Client(credentials=credentials, project=sa_info.get("project_id"))
    bucket_name = url[0]
    blob_path = url[1]
    # Get bucket and blob
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Download the blob contents as bytes and decode to a string
    private_key_bytes = blob.download_as_bytes()
    private_key = private_key_bytes.decode('utf-8')
    
    print(f"Successfully downloaded private key from gs://{bucket_name}/{blob_path}")
    
    return private_key