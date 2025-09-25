import os

def build_tree(start_path, prefix="", ignore=None):
    """
    Recursively builds a directory tree representation.

    Args:
        start_path (str): Path to the root directory.
        prefix (str): Internal prefix for indentation.
        ignore (set): Folder/file names to ignore.

    Returns:
        list of (path, line): Relative path and formatted tree line.
    """
    if ignore is None:
        ignore = {".git", ".github", "__pycache__", ".venv", "node_modules", ".idea", ".DS_Store"}

    items = sorted(
        [item for item in os.listdir(start_path) if item not in ignore]
    )

    entries = []
    for idx, item in enumerate(items):
        path = os.path.join(start_path, item)
        connector = "└─ " if idx == len(items) - 1 else "├─ "
        line = prefix + connector + item
        entries.append((path, line))

        if os.path.isdir(path):
            extension = "   " if idx == len(items) - 1 else "│  "
            entries.extend(build_tree(path, prefix + extension, ignore))

    return entries


def get_folder_tree(root_dir, comments=None, ignore=None):
    """
    Return a string representing the folder tree with optional comments.

    Args:
        root_dir (str): Path to root folder.
        comments (dict): {relative_path: comment}.
        ignore (set): Folders/files to ignore.

    Returns:
        str: The formatted tree.
    """
    if comments is None:
        comments = {}

    entries = build_tree(root_dir, ignore=ignore)
    # lines = [f"{os.path.basename(root_dir)}/"]
    lines=[]
    for path, line in entries:
        rel_path = os.path.relpath(path, root_dir)
        comment = f"  # {comments[rel_path]}" if rel_path in comments else ""
        lines.append(f"{line}{comment}")
    return "\n".join(lines)