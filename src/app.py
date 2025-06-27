from workflow.graph import WorkFlow
from fastapi import FastAPI, BackgroundTasks, HTTPException
import os
import logging
from pathlib import Path
from typing import Dict
import json
import subprocess
import tempfile
import shutil
from tools.terraform_tool import *import subprocess
import tempfile
import shutil
from tools.terraform_tool import *from tools.terraform_tool import *
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import uuid

@app.post("/devopsagent", response_model=Dict[str, str])
def devops_agent(issue: dict, background_tasks: BackgroundTasks):
    temp_dir = None
    try:
        thread_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Processing request with thread_id: {thread_id} in temp_dir: {temp_dir}")
        work_flow.show_state()
        return {
            "status": "success",
            "message": "devops agent launched successfully."
        }
        
    except Exception as e:
        logger.error(f"Error launching workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to launch workflow: {str(e)}"
        )
    finally:
        if temp_dir and os.path.exists(temp_dir):
            logger.info(f"Scheduling cleanup for temp_dir: {temp_dir}")
            background_tasks.add_task(shutil.rmtree, temp_dir)        # Log workflow state
        work_flow.show_state()
        return {def devops_agent(issue: dict):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        work_flow = WorkFlow()
        work_flow(issue)
        
        # Log workflow state
        work_flow.show_state()
        return {
            "status": "success",
            "message": "devops agent launched successfully."
        }
        
    except Exception as e:
        logger.error(f"Error launching workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to launch workflow: {str(e)}"
        )



@app.post("/selfhealing", response_model=Dict[str, str])
def self_healing(info: dict):    
    try:
        logger.info("Selfhealing endpoint called")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # logger.info(info['incidents'].keys())
        logger.info(info['incident'])
        logger.info("DONE")
        return {
            "status": "success",
            "message": "selfhealing endpoint launched successfully."
        }       
    except Exception as e:
        logger.error(f"Error launching selfhealing endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to launch selfhealing endpoint: {str(e)}"
        )
    
@app.post("/test", response_model=Dict[str, str])
def test(info: dict):    
    try:
        logger.info("test endpoint called")
        if info['error']==True: 
            print(1 / 0)
        else:
            logger.info("No error, All good")
        return {
            "status": "success",
            "message": "test endpoint launched successfully."
        }       
    except Exception as e:
        logger.error(f"Error launching test endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to launch test endpoint: {str(e)}"
        )
    

@app.post("/test_terraform_tool")
def test_terraform_tool(issue: dict):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "sa_key.json"), "w") as f:
        json.dump(issue['sa_key'], f)

    # command='export GOOGLE_APPLICATION_CREDENTIALS="../sa_key.json"'
    # result=subprocess.run(
    #     command,
    #     cwd=current_dir,
    #     shell=True,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     text=True
    # )
    github_token=os.environ.get("GITHUB_TOKEN")
    command=f'cd codebase && git clone https://{github_token}@github.com/{issue["github_repositories"][0]}.git'
    result = subprocess.run(
        command,
        cwd=current_dir,         # Start from current_dir
        shell=True,              # Required for using 'cd' and '&&'
        stdout=subprocess.PIPE,  # Capture standard output
        stderr=subprocess.PIPE,  # Capture standard error
        text=True                # Decode output as string
    )
    # command='export GOOGLE_APPLICATION_CREDENTIALS="sa_key.json"'
    # result=subprocess.run(
    #     command,
    #     cwd=current_dir,
    #     shell=True,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     text=True
    # )
    # result=terraform_command_executor("terraform plan","foundation")
    # logger.info(result['stdout'])
    # logger.info(result['stderr'])
    result=terraform_command_executor("terraform init -backend-config=backend.config","foundation")
    logger.info(result['stdout'])
    logger.info(result['stderr'])

    result=terraform_command_executor("terraform state list","foundation")
    logger.info(result['stdout'])
    logger.info(result['stderr'])
    return "GOOD"
