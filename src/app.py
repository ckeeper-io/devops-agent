from workflow.planner.graph import WorkFlow
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
    state: dict
class ChatBackgroundResponse(BaseModel):
    agent_response: str
    step: str
    status: str
    message: str
    agent_trajectory: str
    state: dict

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


@app.post("/chat", response_model=ChatBackgroundResponse)
def chat(request: ChatRequest):
    try:
        logger.info("Workflow endpoint called")
        logger.info("/////////////////////////:")
        work_flow = WorkFlow(request=request)
        work_flow(request=request)
        state_values = work_flow.workflow.get_state(work_flow.config).values
        return {
            "agent_response": state_values.get("agent_response",""),
            "status": "success",
            "state":state_values     
        }
        
    except Exception as e:
        logger.error(f"Error launching workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to launch workflow: {str(e)}"
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