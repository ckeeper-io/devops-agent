from typing_extensions import TypedDict
from typing import Annotated, List
from langgraph.graph.message import add_messages
from pydantic import BaseModel

class RepoBranch(BaseModel):
    repository_url: str
    agent_branch: str
    original_branch: str

class State(TypedDict):
    query: str
    codebase: list
    current_repo_branch: List[RepoBranch]
    session_id: str
    workspace_id: str
    chat_history: list
    githubapp_id: str
    githubapp_privatekey: str
    sa_key_bucket_link: dict
    current_step: str
    plans: list
    previous_steps_actions: list
    step_action_markdown_format: str
    current_cycle: int
    max_cycle_executor: int
    agent_response: str
    input_tokens: int
    output_tokens: int
    recursion_limit: int
    current_recursion: int
    executor_messages: Annotated[list,add_messages]
    messages_for_evaluation: Annotated[list,add_messages]