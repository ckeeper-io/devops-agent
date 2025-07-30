import os
import json
from google.cloud import storage
from google.oauth2 import service_account
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

def download_sandbox(session_id):
    sa_key_json = os.getenv('SA_KEY')
    if not sa_key_json:
        raise ValueError("Environment variable SA_KEY not set")

    sa_info = json.loads(sa_key_json)

    credentials = service_account.Credentials.from_service_account_info(sa_info)
    client = storage.Client(credentials=credentials, project=sa_info.get("project_id"))

    bucket_name = "sandbox_bucket_ckeeper"
    bucket = client.bucket(bucket_name)

    prefix = f"{session_id}/codebase/"
    blobs = list(client.list_blobs(bucket_name, prefix=prefix))

    if not blobs:
        # Create folder by uploading a dummy file (GCS has no real folders)
        folder_blob = bucket.blob(prefix)
        folder_blob.upload_from_string('', content_type='application/x-www-form-urlencoded')
        logger.info(f"Created folder gs://{bucket_name}/{prefix}")

    # Download all blobs under the session_id/ prefix
    local_base = os.path.abspath(os.path.join(current_dir, "..", "..", "tmp", session_id, "codebase"))
    os.makedirs(local_base, exist_ok=True)

    for blob in blobs:
        if blob.name.endswith('/'):
            continue  # skip folder placeholders

        # Construct local path
        relative_path = os.path.relpath(blob.name, prefix)
        local_path = os.path.join(local_base, relative_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)
        logger.info(f"Downloaded gs://{bucket_name}/{blob.name} to {local_path}")