from typing_extensions import TypedDict
from typing import Annotated, List
from langgraph.graph.message import add_messages
from pydantic import BaseModel

class RepoBranch(BaseModel):
    repository_url: str
    agent_branch: str
    original_branch: str

class PlannerState(TypedDict):
    query: str
    codebase: list
    current_repo_branch: List[RepoBranch]
    session_id: str
    workspace_id: str
    githubapp_id: str
    githubapp_privatekey: str
    sa_key_bucket_link: dict
    current_plan: str
    agent_response: str
    planner_messages: Annotated[list,add_messages]