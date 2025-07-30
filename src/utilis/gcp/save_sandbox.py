import os
import json
from google.cloud import storage
from google.oauth2 import service_account
import shutil
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))


def upload_sandbox(session_id):
    sa_key_json = os.getenv('SA_KEY')
    if not sa_key_json:
        raise ValueError("Environment variable SA_KEY not set")

    sa_info = json.loads(sa_key_json)
    credentials = service_account.Credentials.from_service_account_info(sa_info)
    client = storage.Client(credentials=credentials, project=sa_info.get("project_id"))

    bucket_name = "sandbox_bucket_ckeeper"
    bucket = client.bucket(bucket_name)

    # Define local folder to upload
    local_base = os.path.abspath(os.path.join(current_dir, "..", "..", "tmp", session_id))

    if not os.path.exists(local_base):
        return f"Local folder {local_base} does not exist"
    
    # Walk through the local directory
    for root, dirs, files in os.walk(local_base):
        for file_name in files:
            local_path = os.path.join(root, file_name)
            # Construct blob path relative to session_id root
            relative_path = os.path.relpath(local_path, local_base)
            blob_path = f"{session_id}/{relative_path}"

            blob = bucket.blob(blob_path)
            blob.upload_from_filename(local_path)
            logger.info(f"Uploaded {local_path} to gs://{bucket_name}/{blob_path}")
    
    # Delete the user_dir before ending the endpoint
    local_base = os.path.abspath(os.path.join(current_dir, "..", "..", "tmp", session_id))
    if local_base.exists() and local_base.is_dir():
        shutil.rmtree(local_base)
        logger.info(f"Deleted user_dir: {local_base}")
