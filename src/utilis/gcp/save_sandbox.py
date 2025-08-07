import os
import json
from google.cloud import storage
from google.oauth2 import service_account
import shutil
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Thread-local storage for GCS client
thread_local = threading.local()

def get_gcs_client():
    """Get or create GCS client for current thread"""
    if not hasattr(thread_local, 'client'):
        sa_key_json = os.getenv('SA_KEY')
        if not sa_key_json:
            raise ValueError("Environment variable SA_KEY not set")
        
        sa_info = json.loads(sa_key_json)
        credentials = service_account.Credentials.from_service_account_info(sa_info)
        thread_local.client = storage.Client(credentials=credentials, project=sa_info.get("project_id"))
    
    return thread_local.client

def upload_single_file(bucket_name, local_path, blob_path):
    """Upload a single file - used for parallel processing"""
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        blob.upload_from_filename(local_path)
        # logger.info(f"Uploaded {local_path} to gs://{bucket_name}/{blob_path}")
        return True
    except Exception as e:
        logger.error(f"Could not upload {local_path} to gs://{bucket_name}/{blob_path}: {e}")
        return False

def upload_codebase(session_id,current_repo_branch):
    for repo_branch in current_repo_branch:
        repo_name=repo_branch["repo_url"].split("https://github.com/")[1]
        repo_name=repo_name.split(".git")[0]
        command=f'cd .. && cd tmp && cd {session_id} && cd codebase && cd {repo_name} && git checkout {repo_branch["original_branch"]}'
        result= subprocess.run(
            command,
            cwd=current_dir,         # Start from current_dir
            shell=True,              # Required for using 'cd' and '&&'
            stdout=subprocess.PIPE,  # Capture standard output
            stderr=subprocess.PIPE,  # Capture standard error
            text=True                # Decode output as string
        )
        logger.info("This is the result of git checkout to original_branch:",result)
    client = get_gcs_client()
    bucket_name = "sandbox_bucket_ckeeper"
    bucket = client.bucket(bucket_name)

    # Define local folder to upload
    local_base = os.path.abspath(os.path.join(current_dir, "..", "..", "tmp", session_id))

    if not os.path.exists(local_base):
        return f"Local folder {local_base} does not exist"
    
    # Prepare upload tasks
    upload_tasks = []
    
    # Walk through the local directory
    for root, dirs, files in os.walk(local_base):
        for file_name in files:
            local_path = os.path.join(root, file_name)
            
            # Skip files larger than 1MB
            if os.path.getsize(local_path) > 1 * 1024 * 1024:
                logger.error(f"Skipping large file ({os.path.getsize(local_path)/1024/1024:.1f}MB): {local_path}")
                continue
            
            # Construct blob path relative to session_id root
            relative_path = os.path.relpath(local_path, local_base)
            blob_path = f"{session_id}/{relative_path}"
            upload_tasks.append((bucket_name, local_path, blob_path))
    
    # Upload files in parallel (max 10 concurrent uploads)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(upload_single_file, *task) for task in upload_tasks]
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Upload task failed: {e}")
    
    # Delete the user_dir before ending the endpoint
    local_base = Path(os.path.join(current_dir, "..", "..", "tmp", session_id))
    if local_base.exists() and local_base.is_dir():
        shutil.rmtree(local_base)
        logger.info(f"Deleted user_dir: {local_base}")