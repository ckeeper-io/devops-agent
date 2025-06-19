from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
import os
import subprocess
import requests
current_dir = os.getcwd()


def run_git_command(command, cwd):
    result = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        return result.stderr.strip()
    return result.stdout.strip()

def create_pull_request(repo_name,pr_title,pr_body,state: Annotated[dict, InjectedState]):
    """
    This tool is used to create a pull request for the repository that you changed.
    arguments:
        repo_name: str : This should be the name of the repository
        pr_title: str : Information about the problem
        pr_body: str : Generate a well structured report to make the user understand the problem and the solution
    """
    result=run_git_command("cd selfhealing-agent  && git status", current_dir)
    current_branch = result.split("\n")[0].split(" ")[2]
    result=run_git_command("cd selfhealing-agent  && git checkout selfhealing-hotfix", current_dir)
    if "did not match any file(s) known to git" in result:
        result=run_git_command("cd selfhealing-agent  && git checkout -b selfhealing-hotfix", current_dir)
    else:
        result=run_git_command(f"cd selfhealing-agent  && git checkout {current_branch}", current_dir)
        print(result)
        result = run_git_command(f'cd selfhealing-agent  && git push origin --delete selfhealing-hotfix', current_dir)
        print(result)
        result = run_git_command("cd selfhealing-agent  && git branch -d selfhealing-hotfix", current_dir)
        print(result)
        result=run_git_command("cd selfhealing-agent  && git checkout -b selfhealing-hotfix", current_dir)
        print(result)
    command = f'cd {repo_name}  && git add . && git commit -m "selfhealing-hotfixx" && git push --set-upstream origin selfhealing-hotfix'
    result = run_git_command(command, current_dir)
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
        "head": "selfhealing-hotfix",
        "base": current_branch,
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
