import os
import json
from google.cloud import storage
from google.oauth2 import service_account
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

def download_single_file(bucket_name, blob_name, local_path, prefix):
    """Download a single file - used for parallel processing"""
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)
        # logger.info(f"Downloaded gs://{bucket_name}/{blob_name} to {local_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {blob_name}: {e}")
        return False

def download_codebase(workspace_id,session_id,current_repo_branch,codebase):

    client = get_gcs_client()
    bucket_name = "sandbox_bucket_ckeeper"
    bucket = client.bucket(bucket_name)

    prefix = f"{workspace_id}/codebase/"
    blobs = list(client.list_blobs(bucket_name, prefix=prefix))

    if not blobs:
        # Create folder by uploading a dummy file (GCS has no real folders)
        folder_blob = bucket.blob(prefix)
        folder_blob.upload_from_string('', content_type='application/x-www-form-urlencoded')
        logger.info(f"Created folder gs://{bucket_name}/{prefix}")

    # Prepare download tasks
    download_tasks = []
    local_base = os.path.abspath(os.path.join(current_dir, "..", "..", "tmp", session_id, "codebase"))
    os.makedirs(local_base, exist_ok=True)

    for blob in blobs:
        if blob.name.endswith('/'):
            continue  # skip folder placeholders

        # Construct local path
        relative_path = os.path.relpath(blob.name, prefix)
        local_path = os.path.join(local_base, relative_path)
        download_tasks.append((bucket_name, blob.name, local_path, prefix))

    # Download files in parallel (max 10 concurrent downloads)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(download_single_file, *task) for task in download_tasks]
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Download task failed: {e}")
    for repo_branch in codebase:
        repo_name=repo_branch["repository_url"].split("https://github.com/")[1]
        repo_name=repo_name.split(".git")[0]
        command=f'cd .. && cd tmp && cd {session_id} && cd codebase && cd {repo_name} && git pull'
        result= subprocess.run(
            command,
            cwd=current_dir,         # Start from current_dir
            shell=True,              # Required for using 'cd' and '&&'
            stdout=subprocess.PIPE,  # Capture standard output
            stderr=subprocess.PIPE,  # Capture standard error
            text=True                # Decode output as string
        )
        logger.info("This is the result of git pull:",result)
    for repo_branch in current_repo_branch:
        repo_name=repo_branch["repository_url"].split("https://github.com/")[1]
        repo_name=repo_name.split(".git")[0]
        command=f'cd .. && cd tmp && cd {session_id} && cd codebase && cd {repo_name} && git checkout {repo_branch["agent_branch"]}'
        result= subprocess.run(
            command,
            cwd=current_dir,         # Start from current_dir
            shell=True,              # Required for using 'cd' and '&&'
            stdout=subprocess.PIPE,  # Capture standard output
            stderr=subprocess.PIPE,  # Capture standard error
            text=True                # Decode output as string
        )
        logger.info("This is the result of git checkout to agent_branch:",result)
