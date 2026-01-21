import os
import subprocess
from typing_extensions import Annotated
from langgraph.prebuilt import InjectedState
import requests
current_dir = os.path.dirname(os.path.abspath(__file__))

DANGEROUS_GIT_COMMANDS = ['push','remote','config']
def run_git_command(command: str,path: str, state: Annotated[dict, InjectedState]) -> str:
    """
    Execute a git command. Only commands that starts with git keyword are eligible.
    Args:
        command (str): (e.g., "git add ."), Those commands are not eligible ['push','remote','config']
        path (str): Relative path from the codebase root. This where you want to execute the git command
        state: Automatically injected by the system.
        
    Returns:
        str: The stdout output from the git command if successful, or an error message             
    """
    try:
        codebase_dir = os.path.abspath(os.path.join(current_dir, "..","..", "tmp", state["session_id"], "codebase"))
        if command.split(' ')[0] != 'git':
            return f"Error: git command not found in the command: {command}"
        for d_cmd in DANGEROUS_GIT_COMMANDS:
            if d_cmd in command:
                return f"You can not execute this command"
        if "checkout" in command:
            # Get repo name (assume state contains it, fallback to directory name)
            repo_name = path.split('/')[0]

            # Get old commit SHA
            cmd = f'cd .. && cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {path} && git rev-parse HEAD'
            result = subprocess.run(cmd, cwd=current_dir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            old_commit = result.stdout.strip()

            # Run the checkout command
            cmd = f'cd .. && cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {path} && {command}'
            result = subprocess.run(cmd, cwd=current_dir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            checkout_stdout = result.stdout
            checkout_stderr = result.stderr

            # Get new/current commit SHA
            cmd = f'cd .. && cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {path} && git rev-parse HEAD'
            result = subprocess.run(cmd, cwd=current_dir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            current_commit = result.stdout.strip()

            # Get the diff between old and current commit
            cmd = f'cd .. && cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {path} && git diff --name-status {old_commit} {current_commit}'
            result = subprocess.run(cmd, cwd=current_dir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            diff_output = result.stdout.strip().splitlines()

            changes = []
            for line in diff_output:
                parts = line.split()
                if not parts:
                    continue
                status = parts[0]
                if status.startswith("R"):  # Rename → normalize as D + A
                    old_file, new_file = parts[1], parts[2]
                    changes.append({"status": "D", "file_path": f"{repo_name}/{old_file}"})
                    changes.append({"status": "A", "file_path": f"{repo_name}/{new_file}"})
                elif status.startswith("C"):  # Copy → normalize as A
                    new_file = parts[2]
                    changes.append({"status": "A", "file_path": f"{repo_name}/{new_file}"})
                elif status in ["T", "U", "X"] or status.startswith("B"):  # Treat all as modified
                    file_path = parts[-1]
                    changes.append({"status": "M", "file_path": f"{repo_name}/{file_path}"})
                else:  # Normal M, A, D
                    file_path = parts[1]
                    changes.append({"status": status, "file_path": f"{repo_name}/{file_path}"})
            for i in range(len(changes)):
                if ".git" not in changes[i]["file_path"].split("/"):
                    if changes[i]["status"]=="M":
                        with open(os.path.abspath(os.path.join(codebase_dir, changes[i]["file_path"])), "r") as file:
                            file_content = file.read()    
                        edit_file_url=os.environ.get("KNOWLEDGE_GRAPH_MANGER_URL")+"/session/edit_file"
                        payload = {
                            "session_id": state["session_id"],
                            "file_path": changes[i]["file_path"],
                            "file_content": file_content,
                            "workspace_id": state["workspace_id"]
                        }
                        requests.post(edit_file_url, json=payload)
                    if changes[i]["status"]=="A":
                        with open(os.path.abspath(os.path.join(codebase_dir, changes[i]["file_path"])), "r") as file:
                            file_content = file.read()    
                        add_file_url=os.environ.get("KNOWLEDGE_GRAPH_MANGER_URL")+"/session/add_file"
                        payload = {
                            "session_id": state["session_id"],
                            "file_path": changes[i]["file_path"],
                            "file_content": file_content,
                            "workspace_id": state["workspace_id"]
                        }
                        requests.post(add_file_url, json=payload)
                    if changes[i]["status"]=="D":    
                        delete_file_url=os.environ.get("KNOWLEDGE_GRAPH_MANGER_URL")+"/session/delete_file"
                        payload = {
                            "session_id": state["session_id"],
                            "file_path": changes[i]["file_path"],
                            "workspace_id": state["workspace_id"]
                        }
                        requests.post(delete_file_url, json=payload)
            return {
                "stdout":checkout_stdout,
                "stderr":checkout_stderr
            }
        else:
            cmd=f'cd .. && cd .. && cd tmp && cd {state["session_id"]} && cd codebase && cd {path} && {command}'
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