from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
import os
import subprocess
import requests
import logging

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
def branch_exists_local(branch, repo_path):
    """Return True if branch exists locally."""
    result = run_git(f"cd .. && cd codebase && cd {repo_path} && git rev-parse --verify --quiet {branch}", repo_path)
    return result.returncode == 0

def branch_exists_remote(branch, repo_path):
    """Return True if branch exists on origin."""
    result = run_git(f"cd .. && cd codebase && cd {repo_path} && git ls-remote --exit-code --heads origin {branch}", repo_path)
    print(result)
    return result.returncode == 0


def create_pull_request(repo_name,pr_title,pr_body,state: Annotated[dict, InjectedState]):
    """
    This tool is used to create a pull request for the repository that you changed.
    arguments:
        repo_name: str : This should be the name of the changed repository
        pr_title: str : Information about the problem
        pr_body: str : Generate a well structured report to make the user understand the problem and the provided solution
    """
    try:
        command=f'cd .. && cd codebase && cd {repo_name} && git add . && git commit -m "iacagent-hotfixx"'
        result = run_git(command, current_dir)
        command=f'cd .. && cd codebase && cd {repo_name} && git push --set-upstream origin iacagent-hotfix'
        result = run_git(command, current_dir)
        if result.returncode ==1:
            command=f'cd .. && cd codebase && cd {repo_name} && git push --force origin iacagent-hotfix'
            result = run_git(command, current_dir)
        #########################################################################################
        for repo in state['github_repositories']:
            if repo_name in repo:
                repo_name_git = repo
        url = f"https://api.github.com/repos/{repo_name_git}/pulls"
        
        headers = {
            "Authorization": f"token {state['github_token']}",
            "Accept": "application/vnd.github+json"
        }
        payload = {
            "title": pr_title,
            "head": "iacagent-hotfix",
            "base": "main",
            "body": pr_body
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            pr_url = response.json().get("html_url")
            print(f"✅ Pull Request created: {pr_url}")
        else:
            print("❌ Failed to create pull request:")
            print(f"Status Code: {response.status_code}")
            print(response.json())
    except Exception as e:
        logger.error(f"Error creating pull request: {str(e)}", exc_info=True)