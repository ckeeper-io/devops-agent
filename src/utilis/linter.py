import os
import ast
import subprocess
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def infer_language_from_extension(file_path: str) -> str:
    if file_path.endswith(".py"):
        return "python"
    elif file_path.endswith(".js"):
        return "javascript"
    elif file_path.endswith(".tf"):
        return "terraform"
    else:
        return "unknown"

def check_syntax(language: str, code: str, file_path: str, session_dir: str) -> str:
    if language == "python":
        try:
            ast.parse(code)
            return ""
        except SyntaxError as e:
            return f"Python SyntaxError: {e.msg} on line {e.lineno}"

    elif language == "javascript":
        temp_path = os.path.join(session_dir, "__temp_check.js")
        with open(temp_path, "w") as f:
            f.write(code)
        result = subprocess.run(["eslint", temp_path], capture_output=True, text=True)
        os.remove(temp_path)
        if result.returncode != 0:
            return f"JavaScript Lint Error:\n{result.stderr.strip()}"
        return ""

    elif language == "terraform":
        init_command = ["terraform", "init", "-input=false", "-no-color"]
        result=subprocess.run(init_command, cwd=session_dir, capture_output=True)
        if result.returncode== 1:
            return ""
        result = subprocess.run(["terraform", "validate", "-no-color"], cwd=session_dir, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Terraform Validation Error:\n{result.stderr.strip() or result.stdout.strip()}"
        return ""

    return ""