from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
import subprocess
import os
import  logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
def clone_repository(repo_url: str,branch: str,state: Annotated[dict, InjectedState]):
    """
    This tool is used to clone a repository from a given URL and branch.
    arguments:
        repo_url: str : This should be the URL of the repository you want to clone.
        branch: str : This should be the branch of the repository you want to clone.
    """
    try:
        current_dir=os.path.dirname(os.path.abspath(__file__))
        repo_url = repo_url.replace("https://", f"https://{state['github_token']}@")
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
        result = subprocess.run(
            command,
            cwd=current_dir,         # Start from current_dir
            shell=True,              # Required for using 'cd' and '&&'
            stdout=subprocess.PIPE,  # Capture standard output
            stderr=subprocess.PIPE,  # Capture standard error
            text=True                # Decode output as string
        )
        logger.info(result)
    except:
        return {"error": "git command failed"}