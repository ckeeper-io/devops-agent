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
    This tool authenticates using a GitHub App, clones the specified repository and branch into the user's codebase workspace, and checks out a new branch for hotfixes.

    Args:
        repo_url (str): The HTTPS URL of the repository to clone. Must be a valid GitHub repository URL (e.g., 'https://github.com/owner/repo.git').
        branch (str): The branch to clone from the repository (e.g., 'main', 'develop').
        state: Automatically injected by the system - do not include this parameter in tool calls.


    Returns:
        successful message, or a dict with error details if cloning or checkout fails.

    Example:
        >>> clone_repository(
        ...     repo_url='https://github.com/example/repo.git',
        ...     branch='main'
        ... )

    Edge Cases:
        - If the repository URL is invalid or inaccessible, returns an error dict with details.
        - If the branch does not exist, the git command will fail and return error details.
        - If the target directory already contains a clone, git will return an error.
    """
    try:
        githubapp_installation_id = None
        for project in state['codebase']:
            print(project['repository_url'])
            if project['repository_url'] == repo_url:
                githubapp_installation_id = project['githubapp_installation_id']
                break
        if githubapp_installation_id:
            jwt_token = get_jwt(state['githubapp_privatekey'], state['githubapp_id'])
            install_token = get_installation_token(jwt_token, githubapp_installation_id)

            current_dir=os.path.dirname(os.path.abspath(__file__))
            repo_url = repo_url.replace("https://", f"https://x_access-token:{install_token}@")
            command=f'cd .. && cd tmp && cd {state["session_id"]} && cd codebase && git clone --branch {branch} {repo_url}'
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
            command=f'cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {repo_name} && git checkout -b iacagent-hotfix'
            result2 = subprocess.run(
                command,
                cwd=current_dir,         # Start from current_dir
                shell=True,              # Required for using 'cd' and '&&'
                stdout=subprocess.PIPE,  # Capture standard output
                stderr=subprocess.PIPE,  # Capture standard error
                text=True                # Decode output as string
            )
            logger.info(result2)
            return "Successfully cloned the repository!"
        else:
            return "No matching repository found in the codebase."
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