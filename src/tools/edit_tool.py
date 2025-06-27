import os
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated

current_dir = os.path.dirname(os.path.abspath(__file__))

def edit(file_path:str, new_code: str, starting_line: int, ending_line:int,state: Annotated[dict, InjectedState]):
    """
    This tool replaces the contents of the file from a starting line (inclusive) to ending line (inclusive) with new_code.
    arguments:
        file_path: str
        new_code: str
        starting_line: int
        ending_line: int
    """
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