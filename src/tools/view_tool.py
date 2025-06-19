
import os

current_dir = os.path.dirname(os.path.abspath(__file__))


def view(file_path: str, starting_line: int, ending_line:int):
    """
    This tool is used to view the contents of a file from a starting line (inclusive) to ending line (inclusive).
    arguments:
        file_path: str
        starting_line: int
        ending_line: int
    """
    with open(os.path.abspath(os.path.join(current_dir, "..", "codebase", file_path)), "r") as file:
        lines = file.readlines()
    if starting_line>0:
        window=lines[starting_line-1:ending_line]
        for i in range(len(window)):
            window[i]=f"{i+1}: {window[i]}"
        return "".join(window)
    else:
        return "Starting line must be greater than 0"