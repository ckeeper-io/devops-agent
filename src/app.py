from workflow.graph import WorkFlow
from fastapi import FastAPI, BackgroundTasks, HTTPException
import os
import logging
from pathlib import Path
from typing import Dict
import json
import subprocess
import string
import shutil
import random
from tools.terraform_tool import *
from fastapi.middleware.cors import CORSMiddleware
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# List of allowed origins (for example, frontend URLs)
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Origins that are allowed to make requests
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods: GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],              # Allow all headers
)

@app.get("/health")
def health_check():
    """Health check endpoint for the DevOps agent API."""
    return {"status": "healthy", "message": "DevOps agent API is running"}


@app.get("/")
def root():
    """Root endpoint that redirects to docs."""
    return {"message": "DevOps Agent API", "docs": "/docs"}


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
        
        agent_trajectory=work_flow.messages_to_trajectory_string()
        # Delete the user_dir before ending the endpoint
        
        user_dir_path = Path(os.path.join(current_dir, "tmp", user_dir))
        if user_dir_path.exists() and user_dir_path.is_dir():
            shutil.rmtree(user_dir_path)
            logger.info(f"Deleted user_dir: {user_dir_path}")
        return {
            "agent_response": work_flow.workflow.get_state(work_flow.config).values["agent_response"],
            "status": "success",
            "message": "devops agent launched successfully.",
            "agent_trajectory":agent_trajectory
        }
        
    except Exception as e:
        user_dir_path = Path(os.path.join(current_dir, "tmp", user_dir))
        if user_dir_path.exists() and user_dir_path.is_dir():
            shutil.rmtree(user_dir_path)
            logger.info(f"Deleted user_dir: {user_dir_path}")
        logger.error(f"Error launching workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to launch workflow: {str(e)}"
        )



@app.post("/selfhealing", response_model=Dict[str, str])
def self_healing(info: dict):    
    try:
        logger.info("Selfhealing endpoint called")
        logger.info("-----------------------------------")
        print(info)
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        # resource_info = None
        # logger.info(f"This is the info:\n{info}\n\n")
        # if 'incident' in info and 'resource' in info['incident']:
        #     resource_info = info['incident']['resource']
        #     logger.info(f"Resource information extracted")
        # else:
        #     logger.info("No resource information found in incident")
        
        # if resource_info:
        #     try:
        #         # Create a query for the devops agent
                
        #         payload=info['incident']['policy_user_labels']
        #         payload['query']=f"Analyze and fix issues with resource: {resource_info}"
        #         ## Those value are hardcoded until the backend or database is ready 
        #         payload['codebase']=[
        #             {
        #                 "repository_url":"https://github.com/ckeeper-io/foundation.git",
        #                 "branch":"develop", 
        #                 "metadata":"This repository contains all terraform code"
        #             },
        #             {
        #                 "repository_url":"https://github.com/ckeeper-io/iac-agent.git",
        #                 "branch":"develop",
        #                 "metadata":"In this repo we develop an agent tool"
        #             },
        #             {
        #                 "repository_url":"https://github.com/ckeeper-io/backend-js.git",
        #                 "branch":"develop",
        #                 "metadata":"Nest framework TypeScript starter repository."
        #             },
        #             {
        #                 "repository_url":"https://github.com/ckeeper-io/webapp.git",
        #                 "branch":"develop",
        #                 "metadata":"Frontend app"
        #             }
        #         ]
        #         payload['sa_key_bucket_link']="gs://sa_keys_bucket/ckeeper.json"
        #         payload['github_app_installation_id']="74312314"
        #         # Call the devops agent endpoint
        #         # devops_response = devops_agent(payload)
        #         logger.info(f'This is the payload that will be passed to devops agent:\n{payload}')
                
        #     except Exception as devops_error:
        #         logger.error(f"Error calling devops agent: {str(devops_error)}")
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
