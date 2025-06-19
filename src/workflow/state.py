from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    query: str
    github_repositories: str
    github_token: str
    messages: Annotated[list,add_messages]