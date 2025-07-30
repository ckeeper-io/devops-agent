from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
import os
import subprocess
import requests
import logging
import jwt
import time
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))


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
                
def run_git(command, cwd):
    """Run git command in repo_path, return CompletedProcess."""
    return subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

def create_pull_request(repo_name,pr_title,pr_body,state: Annotated[dict, InjectedState]):
    """
    This tool commits changes, pushes a new branch ('iacagent-hotfix'), and opens a pull request on GitHub with the provided title and body. It uses the GitHub App credentials from the injected state for authentication.

    Args:
        repo_name (str): The name of the changed repository (must match a folder in the codebase).
        pr_title (str): Title for the pull request, describing the problem or change.
        pr_body (str): Detailed body for the pull request, explaining the problem and the provided solution.
        state: Automatically injected by the system - do not include this parameter in tool calls.
    Returns:
        None if successful. Logs the pull request URL or error details.

    Example:
        >>> create_pull_request(
        ...     repo_name='repo',
        ...     pr_title='Fix bug in deployment',
        ...     pr_body='This PR fixes the deployment bug by ...'
        ... )

    Edge Cases:
        - If the repository name is not found in the codebase, the PR cannot be created.
        - If there are no changes to commit, git may return an error.
    """
    try:
        githubapp_installation_id = None
        for project in state['codebase']:
            if repo_name in project['repository_url']:
                githubapp_installation_id = project['githubapp_installation_id']
                break
        if githubapp_installation_id:
            jwt_token = get_jwt(state['githubapp_privatekey'], state['githubapp_id'])
            install_token = get_installation_token(jwt_token, githubapp_installation_id)

            
            command=f'cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {repo_name} && git add . && git commit -m "iacagent-hotfix"'
            result = run_git(command, current_dir)
            print('commit command')
            print(result)
            print("//////")
            command=f'cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {repo_name} && git push --set-upstream origin iacagent-hotfix'
            result = run_git(command, current_dir)
            print('First push command')
            print(result)
            print("//////")
            if result.returncode ==1:
                command=f'cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {repo_name} && git push --force origin iacagent-hotfix'
                result = run_git(command, current_dir)
                print('Second push command')
                print(result)
                print("//////")
            #########################################################################################
            # Open PR
            for repo in state['codebase']:
                if repo_name in repo["repository_url"]:
                    repo_url = repo["repository_url"]
                    branch=repo["branch"]
            repo_fullname=repo_url.split("https://github.com/")[1]
            repo_fullname=repo_fullname.split(".git")[0]
            logger.info(repo_fullname)
            url = f"https://api.github.com/repos/{repo_fullname}/pulls"
            headers = {
            "Authorization": f"token {install_token}",
            "Accept": "application/vnd.github+json"
            }
            payload = {
                "title": pr_title,
                "head": "iacagent-hotfix",
                "base": branch,
                "body": pr_body
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                pr_url = response.json().get("html_url")
                logger.info(f"✅ Pull Request created: {pr_url}")
            else:
                logger.info("❌ Failed to create pull request:")
                logger.info(f"Status Code: {response.status_code}")
                logger.info(response.json())
        else:
            return "❌ Repository not found in codebase"
    except Exception as e:
        logger.error(f"Error creating pull request: {str(e)}", exc_info=True)