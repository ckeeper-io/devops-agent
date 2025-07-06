import os
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated

current_dir = os.path.dirname(os.path.abspath(__file__))

def edit(file_path:str, new_code: str, starting_line: int, ending_line:int,state: Annotated[dict, InjectedState]):
    """
    This tool replaces the contents of a file from starting_line to ending_line (inclusive) with the provided new_code string. Useful for patching or updating code snippets in-place.

    Args:
        file_path (str): Path to the file (relative to codebase root, e.g., 'repo/main.py').
        new_code (str): The code to insert in place of the specified lines.
        starting_line (int): The first line to replace (1-based, inclusive).
        ending_line (int): The last line to replace (1-based, inclusive).
        state: Automatically injected by the system - do not include this parameter in tool calls.
    Returns:
        str: Success message if the edit is applied, or an error message if starting_line < 1 or another error occurs.

    Example:
        >>> edit(
        ...     file_path='repo/main.py',
        ...     new_code='print("Patched!")',
        ...     starting_line=5,
        ...     ending_line=7
        ... )

    Edge Cases:
        - If starting_line < 1, returns an error.
        - If ending_line exceeds file length, only available lines are replaced.
        - If the file does not exist, raises an exception.
    """
    starting_line = int(starting_line)
    ending_line = int(ending_line)
    with open(os.path.abspath(os.path.join(current_dir, "..", "tmp", state["user_dir"], "codebase", file_path)), "r") as file:
        lines = file.readlines()
    if starting_line>0:
        lines[starting_line-1:ending_line] = [new_code]

        for i in range(len(lines)):
            if "\n" not in lines[i]:
                lines[i]+="\n"
        print("/////////////:")
        print(lines)
        print("/////////////:")
        with open(os.path.abspath(os.path.join(current_dir, "..", "tmp", state["user_dir"],  "codebase", file_path)), "w") as file:
            file.writelines(lines)
        return "File edited successfully"
    else:
        return "Starting line must be greater than 0"