from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))
codebase_dir = os.path.abspath(os.path.join(current_dir, "..", "codebase"))

def create_file(file_path: str, content: str,state: Annotated[dict, InjectedState]):
    """
    This tool creates a new file in the codebase.
    arguments:
        file_path: str – Path to the new file to be created.
        content: str – Content of the new file to be created.
    """
    try:
        first_folder=file_path.split("/")[0]
        if first_folder not in state["github_repositories"]:
            return {"error": f"The file is not created because you should place the file inside one of the provided repositories in the codebase. {state['github_repositories']}"}
        # Resolve absolute path
        abs_path = os.path.abspath(os.path.join(codebase_dir, file_path))

        # Ensure the file path is within the codebase directory
        if not abs_path.startswith(codebase_dir):
            return {"error": "File path is outside the codebase directory."}

        # Check if the file is directly inside the codebase root (i.e., not inside a subfolder/repo)
        relative_path = os.path.relpath(abs_path, codebase_dir)
        if len(relative_path.split(os.sep)) == 1:
            return {"error": f"The file is not created because you should place the file inside one of the provided repositories in the codebase. {state['github_repositories']}"}

        # Create directories if necessary
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        # Write the file
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {"success": f"File created at {abs_path}"}
    except Exception as e:
        return {"error": str(e)}
