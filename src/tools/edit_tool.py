import os

current_dir = os.path.dirname(os.path.abspath(__file__))

def edit(file_path:str, new_code: str, starting_line: int, ending_line:int):
    """
    This tool replaces the contents of the file from a starting line (inclusive) to ending line (inclusive) with new_code.
    arguments:
        file_path: str
        new_code: str
        starting_line: int
        ending_line: int
    """
    with open(os.path.abspath(os.path.join(current_dir, "..", "codebase", file_path)), "r") as file:
        lines = file.readlines()
    if starting_line>0:
        lines[starting_line-1:ending_line] = [new_code]
        print("/////////////:")
        print(lines)
        print("/////////////:")
        with open(os.path.abspath(os.path.join(current_dir, "..", "codebase", file_path)), "w") as file:
            file.writelines(lines)
        return "File edited successfully"
    else:
        return "Starting line must be greater than 0"