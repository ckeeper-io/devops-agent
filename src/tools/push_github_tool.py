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

def push_changes(path,state: Annotated[dict, InjectedState]):
    """
    This tool pushs changes to github

    Args:
        path (str): Relative path from the codebase root. This where push command is going to be executed
        state: Automatically injected by the system - do not include this parameter in tool calls.
    """
    try:
        repo_name=path.split('/')[0]
        command=f'cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {repo_name} && git branch'
        result = run_git(command, current_dir)
        current_branch=extract_current_branch(result.stdout)
        for project in state["codebase"]:
            if repo_name in project["repository_url"]:
                if current_branch==project["branch"]:
                    return f"You are not permitted to push to this branch {current_branch}. Please create new branch and push again"
        

        githubapp_installation_id = None
        for project in state['codebase']:
            if repo_name in project['repository_url']:
                githubapp_installation_id = project['githubapp_installation_id']
                break
        if githubapp_installation_id:
            jwt_token = get_jwt(state['githubapp_privatekey'], state['githubapp_id'])
            install_token = get_installation_token(jwt_token, githubapp_installation_id)
        authed_url = project["repository_url"].replace("https://", f"https://x_access-token:{install_token}@")
        command=f'cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {path} && git remote set-url origin {authed_url} && git push --set-upstream origin {current_branch}'
        result = run_git(command, current_dir)
        print('First push command')
        print(result)
        print("//////")
        if result.returncode ==1:
            command=f'cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {path} && git remote set-url origin {authed_url} && git push --force origin {current_branch}'
            result = run_git(command, current_dir)
            print('Second push command')
            print(result)
            print("//////")
        return result
    except Exception as e:
        logger.error(f"Error executing git push command: {str(e)}", exc_info=True)
        return f"❌ Error executing git push command: {str(e)}"