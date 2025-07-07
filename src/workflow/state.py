from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    query: str
    codebase: list
    github_repositories: list
    githubapp_id: str
    githubapp_installation_id: str
    githubapp_privatekey: str
    query_category: str
    sa_key_bucket_link: dict
    user_dir: str
    current_step: str
    previous_steps_actions: list
    current_cycle: int
    max_cycle_executor: int
    executor_messages: Annotated[list,add_messages]
    input_tokens: int
    output_tokens: int
    messages: Annotated[list,add_messages]