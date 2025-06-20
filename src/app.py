from workflow.graph import WorkFlow
from fastapi import FastAPI, BackgroundTasks, HTTPException
import os
import logging
from pathlib import Path
from typing import Dict
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.post("/launch_iac", response_model=Dict[str, str])
def self_healing(issue: dict):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        work_flow = WorkFlow()
        work_flow(issue)
        
        # Log workflow state
        work_flow.show_state()
        return {
            "status": "success",
            "message": "iac-agent launched successfully."
        }
        
    except Exception as e:
        logger.error(f"Error launching workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to launch workflow: {str(e)}"
        )