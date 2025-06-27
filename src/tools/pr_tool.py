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

def create_pull_request(repo_name,pr_title,pr_body,state: Annotated[dict, InjectedState]):
    """
    This tool is used to create a pull request for the repository that you changed.
    arguments:
        repo_name: str : This should be the name of the changed repository, just the name of that repo folder
        pr_title: str : Information about the problem
        pr_body: str : Generate a well structured report to make the user understand the problem and the provided solution
    """
    try:
        command=f'cd .. && cd tmp && cd {state["user_dir"]} && cd codebase && cd {repo_name} && git add . && git commit -m "iacagent-hotfixx"'
        result = run_git(command, current_dir)
        print('commit command')
        print(result)
        print("//////")
        command=f'cd .. && cd tmp && cd {state["user_dir"]} && cd codebase && cd {repo_name} && git push --set-upstream origin iacagent-hotfix'
        result = run_git(command, current_dir)
        print('First push command')
        print(result)
        print("//////")
        if result.returncode ==1:
            command=f'cd .. && cd tmp && cd {state["user_dir"]} && cd codebase && cd {repo_name} && git push --force origin iacagent-hotfix'
            result = run_git(command, current_dir)
            print('Second push command')
            print(result)
            print("//////")
        #########################################################################################
        for repo in state['codebase']:
            if repo_name in repo["repository_url"]:
                repo_url = repo["repository_url"]
                branch=repo["branch"]
        repo_fullname=repo_url.split("https://github.com/")[1]
        repo_fullname=repo_fullname.split(".git")[0]
        logger.info(repo_fullname)
        url = f"https://api.github.com/repos/{repo_fullname}/pulls"
        
        headers = {
            "Authorization": f"token {state['github_token']}",
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
    except Exception as e:
        logger.error(f"Error creating pull request: {str(e)}", exc_info=True)