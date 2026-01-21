from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
import os
import shutil
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

def delete_path(path: str, state: Annotated[dict, InjectedState]):
    """
    This tool deletes a folder or file at the given path, ensuring it is placed inside one of the allowed repositories in the codebase.
    It checks for directory traversal and codebase root violations.

    Args:
        path (str): Relative path from the codebase root.
        state: Automatically injected by the system.

    Returns:
        dict: {'success': str} if deleted, or {'error': str} if failed
    """
    try:
        # Locate the session-specific codebase directory
        codebase_dir = os.path.abspath(os.path.join(current_dir, "..","..", "tmp", state["session_id"], "codebase"))
        codebase_repos = os.listdir(codebase_dir)

        # Ensure the path is not empty or suspicious
        if not path or ".." in path.split(os.sep):
            return {"error": "Invalid or unsafe path. Directory traversal is not allowed."}

        # Validate that it's placed inside one of the allowed top-level repos
        first_folder = path.split("/")[0]
        if first_folder not in codebase_repos:
            return {"error": f"You can only delete files or folders inside one of the allowed repositories: {codebase_repos}"}

        # Resolve the absolute path
        abs_path = os.path.abspath(os.path.join(codebase_dir, path))

        # Ensure the path is still within the codebase (double-check)
        if not abs_path.startswith(codebase_dir):
            return {"error": "The specified path is outside the codebase directory."}

        if not os.path.exists(abs_path):
            return {"error": f"The path does not exist: {abs_path}"}

        # Perform deletion
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
            return {"success": f"Directory deleted: {abs_path}"}
        else:
            os.remove(abs_path)
            return {"success": f"File deleted: {abs_path}"}

    except Exception as e:
        logger.exception("Failed to delete path")
        return {"error": str(e)}
