from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
import os
import subprocess
import requests
import logging
from utilis.githubapp_privatekey import get_jwt, get_installation_token

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))





                
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

def check_and_delete_existing_pr(repo_fullname, agent_branch, base_branch, install_token):
    """Check for existing PR between the same branches and delete it if found."""
    try:
        # Get all open pull requests
        url = f"https://api.github.com/repos/{repo_fullname}/pulls"
        headers = {
            "Authorization": f"token {install_token}",
            "Accept": "application/vnd.github+json"
        }
        params = {"state": "open"}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            existing_prs = response.json()
            
            # Check for existing PR with same head and base branches
            for pr in existing_prs:
                if pr["head"]["ref"] == agent_branch and pr["base"]["ref"] == base_branch:
                    # Delete the existing PR
                    delete_url = f"https://api.github.com/repos/{repo_fullname}/pulls/{pr['number']}"
                    delete_response = requests.delete(delete_url, headers=headers)
                    if delete_response.status_code == 204:
                        logger.info(f"✅ Deleted existing PR #{pr['number']} between {agent_branch} and {base_branch}")
                    else:
                        logger.warning(f"Failed to delete existing PR #{pr['number']}: {delete_response.status_code}")
                    break
    except Exception as e:
        logger.error(f"Error checking/deleting existing PR: {str(e)}")
# Parse the current branch
def extract_current_branch(git_stdout: str) -> str:
    for line in git_stdout.splitlines():
        if line.strip().startswith("*"):
            return line.strip().split()[1]  # The branch name is the second word
    return None  # Fallback if not found

def create_pull_request(repo_name,agent_branch,target_branch,pr_title,pr_body,state: Annotated[dict, InjectedState]):
    """
    This tool opens a pull request on GitHub with the provided title and body. It uses the GitHub App credentials from the injected state for authentication.

    Args:
        repo_name (str): The name of the changed repository (must match a folder in the codebase).
        agent_branch (str): The current working branch containing your changes.
        target_branch (str): The branch you want to merge your changes into.
        pr_title (str): Title for the pull request, describing the problem or change.
        pr_body (str): Detailed body for the pull request, explaining the problem and the provided solution.
        state: Automatically injected by the system - do not include this parameter in tool calls.
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

            # Open PR
            for repo in state['codebase']:
                if repo_name in repo["repository_url"]:
                    repo_url = repo["repository_url"]
            repo_fullname=repo_url.split("https://github.com/")[1]
            repo_fullname=repo_fullname.split(".git")[0]
            logger.info(repo_fullname)
            
            # Check and delete existing PR between the same branches
            check_and_delete_existing_pr(repo_fullname, agent_branch, target_branch, install_token)
            
            url = f"https://api.github.com/repos/{repo_fullname}/pulls"
            headers = {
            "Authorization": f"token {install_token}",
            "Accept": "application/vnd.github+json"
            }
            payload = {
                "title": pr_title,
                "head": agent_branch,
                "base": target_branch,
                "body": pr_body
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                pr_url = response.json().get("html_url")
                logger.info(f"✅ Pull Request created: {pr_url}")
                return f"✅ Pull Request created: {pr_url}"
            else:
                logger.info("❌ Failed to create pull request:")
                logger.info(f"Status Code: {response.status_code}")
                logger.info(response.json())
                return f"❌ Failed to create pull request {response.status_code}"
        else:
            return "❌ Repository not found in codebase"
    except Exception as e:
        logger.error(f"Error creating pull request: {str(e)}", exc_info=True)
        return f"❌ Error creating pull request: {str(e)}"