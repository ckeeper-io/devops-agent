import os
import subprocess
current_dir = os.path.dirname(os.path.abspath(__file__))

def search(query:str):
    """
    This tool is used to search for a code snippet in the codebase. You should a code snippet as a query.
    arguments:
        query: str
    """
    

    # Build the full command as a single shell string
    command = f'cd .. && cd codebase && timeout 5s grep -rn --exclude="*.ipynb" "{query}"'

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