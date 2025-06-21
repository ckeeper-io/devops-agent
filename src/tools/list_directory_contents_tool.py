import subprocess
import os

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

def list_directory_contents(dir_path):
    """
    This tool lists the contents of a directory.
    arguments:
        dir_path: str
    """
    try:
        command = f'cd .. && cd codebase && cd {dir_path} && ls -a'
        # Run the `ls` command on the given directory
        result = run_command(command, current_dir)

        # Split the output into individual items
        items = result.stdout.strip().split('\n')
        return {
            "items": items
        }

    except subprocess.CalledProcessError as e:
        return {"error": f"Command failed: {e.stderr.strip()}"}
    except FileNotFoundError:
        return {"error": f"Directory '{dir_path}' not found."}
    except Exception as e:
        return {"error": str(e)}
