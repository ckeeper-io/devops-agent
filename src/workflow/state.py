from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    query: str
    codebase: list
    github_repositories: list
    github_token: str
    query_category: str
    sa_key_bucket_link: dict
    user_dir: str
    messages: Annotated[list,add_messages]