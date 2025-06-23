from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    query: str
    full_github_repositories: list
    github_repositories: list
    github_token: str
    query_category: str
    sa_key: dict
    messages: Annotated[list,add_messages]