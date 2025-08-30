import os
import subprocess
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
import requests
import json
current_dir = os.path.dirname(os.path.abspath(__file__))

def search_by_grep(query:str,state: Annotated[dict, InjectedState]):
    """
    This tool runs a recursive search (excluding .ipynb files) for the given query string in all files of the user's codebase directory. It returns matching lines with file names and line numbers.

    Args:
        query (str): The text or code snippet to search for. Can be a word, phrase, or code fragment. Quoting and escaping are handled automatically.
        state: Automatically injected by the system - do not include this parameter in tool calls.
    Returns:
        str: The grep output, listing matches as 'filename:line_number:matched_line'. If no matches are found, returns an empty string. If an error occurs, stderr is included in the output.

    Example:
        >>> search(
        ...     query='def my_function'
        ... )

    Edge Cases:
        - If the query is empty, grep will return no results.
    """
    

    # Build the full command as a single shell string
    command = f'cd .. && cd .. && cd tmp && cd {state["session_id"]} && cd codebase && timeout 5s grep -rn --exclude="*.ipynb" "{query}"'

    # Run the command in a shell
    result = subprocess.run(
        command,
        cwd=current_dir,         # Start from current_dir
        shell=True,              # Required for using 'cd' and '&&'
        stdout=subprocess.PIPE,  # Capture standard output
        stderr=subprocess.PIPE,  # Capture standard error
        text=True                # Decode output as string
    )
    return result.stdout



def search_by_natural_language_query(natural_language_query:str,state: Annotated[dict, InjectedState]):
    """
    This tool perform similarity search between the natural_language_query and the codebase

    Args:
        natural_language_query (str): The text or code snippet to search for. Can be a word, phrase, or code fragment
        state: Automatically injected by the system - do not include this parameter in tool calls.
    Returns:
        List of dicts that have file_path and score as fields
    """
    
    add_file_url=os.environ.get("KNOWLEDGE_GRAPH_MANGER_URL")+"/search/search_file"
    payload = {
        "session_id": state["session_id"],
        "workspace_id": state["workspace_id"],
        "natural_language_query": natural_language_query
    }

    response= requests.post(add_file_url, json=payload)
    json_str = response.content.decode('utf-8')

    # Step 2: parse JSON to Python list
    search_result = json.loads(json_str)

    return search_result