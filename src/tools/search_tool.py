import os
import subprocess
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
current_dir = os.path.dirname(os.path.abspath(__file__))

def search(query:str,state: Annotated[dict, InjectedState]):
    """
    This tool is used to search for a code snippet in the codebase. You should a code snippet as a query.
    arguments:
        query: str
    """
    

    # Build the full command as a single shell string
    command = f'cd .. && cd tmp && cd {state["user_dir"]} && cd codebase && timeout 5s grep -rn --exclude="*.ipynb" "{query}"'

    # Run the command in a shell
    result = subprocess.run(
        command,
        cwd=current_dir,         # Start from current_dir
        shell=True,              # Required for using 'cd' and '&&'
        stdout=subprocess.PIPE,  # Capture standard output
        stderr=subprocess.PIPE,  # Capture standard error
        text=True                # Decode output as string
    )
    return result.stdout