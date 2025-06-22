import os
import  logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))
def create_file(file_path: str, content: str):
    """
    This tool creates a new file in the codebase.
    arguments:
        file_path: str – Path to the new file to be created.
        content: str – Content of the new file to be created.
    """
    try:
        file_path=os.path.abspath((os.path.join(current_dir, "..", "codebase",file_path)))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write content to the file
        with open(file_path, 'w',encoding='utf-8') as f:
            f.write(content)

        return {"success": f"File created at {file_path}"}
    except Exception as e:
        return {"error": str(e)}