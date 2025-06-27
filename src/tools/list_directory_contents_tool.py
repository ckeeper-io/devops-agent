import subprocess
import os
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
current_dir = os.path.dirname(os.path.abspath(__file__))
def run_command(command, cwd):
    return subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

def list_directory_contents(dir_path, state: Annotated[dict, InjectedState]):
    """
    This tool lists the contents of a directory with the number of lines for each file.
    arguments:
        dir_path: str
    """
    try:
        abs_dir_path = os.path.abspath(os.path.join(current_dir, "..", "tmp", state["user_dir"], "codebase", dir_path))
        if not os.path.isdir(abs_dir_path):
            return {"error": f"Directory '{dir_path}' not found."}
        
        items = []
        for item in os.listdir(abs_dir_path):
            item_path = os.path.join(abs_dir_path, item)
            if os.path.isfile(item_path):
                with open(item_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                items.append(f"{item}, it has {line_count} lines")
            else:
                items.append(item)

        return {
            "items": items
        }
        
    except FileNotFoundError:
        return {"error": f"Directory '{dir_path}' not found."}
    except Exception as e:
        return {"error": str(e)}
