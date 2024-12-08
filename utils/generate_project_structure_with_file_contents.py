# generate_project_structure_with_file_contents.py

import os
import json
from datetime import datetime

# These are the exclude patterns taken from concatenate_scripts.py for directories and files
exclude_patterns = [
    '.log', '.env', '.gitignore', '.DS_Store', 'Thumbs.db',
    '__pycache__', '.pyc', '.pyo', '.pyd', '.db', '.sqlite',
    '.swp', '.swo', '~', '.egg-info', 'venv', 'node_modules', '.git',
    '.idea', '.vscode', 'env', 'dist', 'build',
    '.mypy_cache', '.pytest_cache', '.ipynb_checkpoints'
]

def should_exclude_dir(dirname: str) -> bool:
    """
    Determine if a directory should be excluded based on exclude_patterns.
    If the directory name contains any of the patterns, exclude it.
    """
    return any(pattern in dirname for pattern in exclude_patterns)

def should_exclude_file(filename: str) -> bool:
    """
    Determine if a file should be excluded based on exclude_patterns.
    If the file name or its extension matches any pattern, exclude it.
    """
    return any(pattern in filename for pattern in exclude_patterns)

def get_directory_structure_with_content(root_dir: str) -> dict:
    """
    Recursively scans the directory structure starting at root_dir
    and returns a nested dictionary representing directories and files.

    For each file, this stores the entire file content as a string.
    Directories and files matching exclude patterns are skipped entirely.
    """
    structure = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter out excluded directories
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d)]

        relative_path = os.path.relpath(dirpath, root_dir)
        if relative_path == ".":
            current_dict = structure
        else:
            path_parts = relative_path.split(os.sep)
            current_dict = structure
            for part in path_parts:
                current_dict = current_dict.setdefault(part, {})

        # Process files
        for filename in filenames:
            # Skip excluded files
            if should_exclude_file(filename):
                continue

            file_path = os.path.join(dirpath, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (UnicodeDecodeError, PermissionError):
                content = "<unreadable or binary content>"
            current_dict[filename] = content

    return structure

if __name__ == "__main__":
    # Specify the root directory you want to reflect
    root_directory = os.getcwd()

    # Get the directory structure with full file content
    project_structure = get_directory_structure_with_content(root_directory)

    # Print the directory structure as JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"project_structure_with_content_{timestamp}.json"

    with open(output_filename, "w", encoding='utf-8') as f:
        json.dump(project_structure, f, indent=4, ensure_ascii=False)

    print(f"The project structure with file contents has been saved to '{output_filename}'.")
