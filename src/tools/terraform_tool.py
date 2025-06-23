# Create temporary backend config file
import tempfile
import os        # Execute terraform command
import subprocess
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



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
def terraform_command_executor(terraform_command: str, dir_execution: str):
    """
    Execute Terraform command
    Args:
        terrafor_command (str): The terraform command to run
        dir_execution (str): This is the path in which the terraform operation should be executed
    """
    try:
        logger.info("In terraform operation tool")
        # Validate operation parameter
        valid_operations = ['init', 'plan','validate', 'fmt', 'show','state list']
        valid_operation=False
        for op in valid_operations:
            if op in terraform_command:
                valid_operation=True
                break
        if terraform_command.split(" ")[1] == "apply":
            valid_operation=False
        if not valid_operation:
            return f"The operation in your command is not valid. Valid operations: {valid_operations}"
        if 'init' in terraform_command and '-backend-config' not in terraform_command:
            return "To use init command you should always provide backend config file to get the state"

  

        go_back=""
        for i in range(len(dir_execution.split('/'))+1):
            go_back+="../"
        cmd= f'cd .. && cd codebase && cd {dir_execution} && export GOOGLE_APPLICATION_CREDENTIALS="{go_back}sa_key.json" && {terraform_command}'

        # Execute the command
        result = run_command(cmd,current_dir)
        # logger.info(f"This is the result from terraform command: {result.stdout}")
        logger.info("out of terraform operation tool")
        return {
            'success': True,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
                
    except Exception as e:
        print(e)
        return {
            'success': True,
            'stdout': "result.stdout",
            'stderr': "result.stderr"
        }