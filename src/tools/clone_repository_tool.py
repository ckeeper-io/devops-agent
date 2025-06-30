from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
import subprocess
import os
import  logging
import time
import jwt  # pip install PyJWT
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_jwt(private_key: str, app_id: str) -> str:
    """Generate a JWT for the GitHub App using its private key."""
    now = int(time.time())
    payload = {"iat": now, "exp": now + 600, "iss": app_id}
    return jwt.encode(payload, private_key, algorithm="RS256")

def get_installation_token(jwt_token: str, installation_id: str) -> str:
    """Exchange the JWT for an installation access token."""
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json"
    }
    resp = requests.post(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return data["token"]


def clone_repository(repo_url: str,branch: str,state: Annotated[dict, InjectedState]):
    """
    This tool is used to clone a repository from a given URL and branch.
    arguments:
        repo_url: str : This should be the URL of the repository you want to clone.
        branch: str : This should be the branch of the repository you want to clone.
    """
    try:
        jwt_token = get_jwt(state['githubapp_privatekey'], state['githubapp_id'])
        install_token = get_installation_token(jwt_token, state['githubapp_installation_id'])

        current_dir=os.path.dirname(os.path.abspath(__file__))
        repo_url = repo_url.replace("https://", f"https://x_access-token:{install_token}@")
        command=f'cd .. && cd tmp && cd {state["user_dir"]} && cd codebase && git clone --branch {branch} {repo_url}'
        result = subprocess.run(
            command,
            cwd=current_dir,         # Start from current_dir
            shell=True,              # Required for using 'cd' and '&&'
            stdout=subprocess.PIPE,  # Capture standard output
            stderr=subprocess.PIPE,  # Capture standard error
            text=True                # Decode output as string
        )
        logger.info(result)
        repo_name=repo_url.split("/")[-1].split(".")[0]
        command=f'cd .. && cd tmp && cd {state["user_dir"]} && cd codebase && cd {repo_name} && git checkout -b iacagent-hotfix'
        result2 = subprocess.run(
            command,
            cwd=current_dir,         # Start from current_dir
            shell=True,              # Required for using 'cd' and '&&'
            stdout=subprocess.PIPE,  # Capture standard output
            stderr=subprocess.PIPE,  # Capture standard error
            text=True                # Decode output as string
        )
        logger.info(result2)
        # Optionally, return success info here
    except Exception as e:
        logger.error(f"Exception occurred: {type(e).__name__}: {e}", exc_info=True)
        error_details = {
            "error": "git command failed",
            "exception_type": type(e).__name__,
            "exception_message": str(e)
        }
        # Try to include stderr from subprocess if available
        if 'result' in locals() and hasattr(result, 'stderr'):
            error_details["stderr_clone"] = result.stderr
        if 'result2' in locals() and hasattr(result2, 'stderr'):
            error_details["stderr_checkout"] = result2.stderr
        return error_details