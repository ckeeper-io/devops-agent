from workflow.graph import WorkFlow
from fastapi import FastAPI, BackgroundTasks, HTTPException
import os
import logging
from pathlib import Path
from typing import Dict
import json
import subprocess
import string
import random
from tools.terraform_tool import *
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()




def generate_random_string():
    letters_and_digits = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(letters_and_digits) for i in range(10))
    return random_string
@app.post("/devopsagent", response_model=Dict[str, str])
def devops_agent(issue: dict):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        user_dir=f'run_{issue["workspace_id"]}_{generate_random_string()}'
        folder_path = Path(os.path.join(current_dir,"tmp",user_dir,"codebase"))
        folder_path.mkdir(parents=True, exist_ok=True)
        work_flow = WorkFlow(user_dir=user_dir)
        work_flow(issue=issue,user_dir=user_dir)
        
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
        resource_info = None
        if 'incident' in info and 'resource' in info['incident']:
            resource_info = info['incident']['resource']
            logger.info(f"Resource information extracted")
        else:
            logger.info("No resource information found in incident")
        
        if resource_info:
            try:
                # Create a query for the devops agent

                payload=info['incident']['policy_user_labels']
                payload['query']=f"Analyze and fix issues with resource: {resource_info}"
                
                # Call the devops agent endpoint
                devops_response = devops_agent(payload)
                
            except Exception as devops_error:
                logger.error(f"Error calling devops agent: {str(devops_error)}")
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