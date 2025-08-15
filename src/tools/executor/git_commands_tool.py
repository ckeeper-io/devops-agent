import os
import subprocess
import json
from typing_extensions import Annotated
from langgraph.prebuilt import InjectedState

current_dir = os.path.dirname(os.path.abspath(__file__))

DANGEROUS_GIT_COMMANDS = ['push','remote','config']
def run_git_command(command: str,path: str, state: Annotated[dict, InjectedState]) -> str:
    """
    Execute a git command.
    Args:
        command (str): (e.g., "git add ."), Those commands are not eligible ['push','remote','config']
        path (str): Relative path from the codebase root. This where you want to execute the git command
        state: Automatically injected by the system.
        
    Returns:
        str: The stdout output from the git command if successful, or an error message             
    """
    try:
        if command.split(' ')[0] != 'git':
            return f"Error: git command not found in the command: {command}"
        for d_cmd in DANGEROUS_GIT_COMMANDS:
            if d_cmd in command:
                return f"You can not execute this command" 
        cmd=f'cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {path} && {command}'
        result = subprocess.run(
                cmd,
                cwd=current_dir,         # Start from current_dir
                shell=True,              # Required for using 'cd' and '&&'
                stdout=subprocess.PIPE,  # Capture standard output
                stderr=subprocess.PIPE,  # Capture standard error
                text=True                # Decode output as string
            )
        return result
    except Exception as e:
        return f"Error running gcloud command: {e}"