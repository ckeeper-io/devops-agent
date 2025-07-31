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
from pydantic import BaseModel
from utilis.format_plan import format_plans_to_markdown
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()
current_dir = os.path.dirname(os.path.abspath(__file__))
# List of allowed origins (for example, frontend URLs)
origins = [
    "*",
]

class ChatRequest(BaseModel):
    query: str
    codebase: list
    workspace_id: str
    session_id: str
    sa_key_bucket_link: str


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


@app.post("/chat_background", response_model=Dict[str, str])
def chat_background(issue: ChatRequest):
    try:
        work_flow = WorkFlow(issue=issue)
        work_flow(issue=issue)
        
        # Log workflow state
        work_flow.show_state()
        
        agent_trajectory=work_flow.messages_to_trajectory_string()
        state_values = work_flow.workflow.get_state(work_flow.config).values
        return {
            "agent_response": state_values.get("agent_response",""),
            "plan":format_plans_to_markdown(state_values.get("plans", [])),
            "status": "success",
            "message": "devops agent launched successfully.",
            "agent_trajectory":agent_trajectory
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