from typing_extensions import TypedDict
from typing import Annotated, List
from langgraph.graph.message import add_messages
from pydantic import BaseModel



class ExecutorState(TypedDict):
    executor_messages: Annotated[list,add_messages]
    current_plan: str
    codebase: list
    session_id: str
    workspace_id: str
    githubapp_id: str
    current_repo_branch: str
    githubapp_privatekey: str
    sa_key_bucket_link: dict
    max_recursion_limit: int
    current_recursion: int
