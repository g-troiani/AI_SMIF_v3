# generate_project_structure_dynamically.py

import os
import json
from typing import Dict, Optional
from datetime import datetime

# Patterns to exclude (files and directories)
EXCLUDE_PATTERNS = [
    '.log', '.env', '.gitignore', '.DS_Store', 'Thumbs.db',
    '__pycache__', '.pyc', '.pyo', '.pyd', '.db', '.sqlite',
    '.swp', '.swo', '~', '.egg-info', 'venv', 'node_modules', '.git'
]

def should_exclude(name: str) -> bool:
    """
    Determine if a file or directory should be excluded based on the EXCLUDE_PATTERNS.
    """
    for pattern in EXCLUDE_PATTERNS:
        # Exclude if exact match or if name ends with the pattern
        if name == pattern or name.endswith(pattern):
            return True
    return False

def get_directory_structure(root_dir: str) -> Dict[str, Optional[dict]]:
    """
    Recursively scans the directory structure starting at root_dir 
    and returns a nested dictionary representing directories and files.
    Excludes files and directories that match patterns in EXCLUDE_PATTERNS.
    """
    structure = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter out excluded directories
        dirnames[:] = [d for d in dirnames if not should_exclude(d)]

        relative_path = os.path.relpath(dirpath, root_dir)
        if relative_path == ".":
            current_dict = structure
        else:
            path_parts = relative_path.split(os.sep)
            current_dict = structure
            for part in path_parts:
                current_dict = current_dict.setdefault(part, {})

        # Add files, excluding the ones that match the exclude patterns
        for filename in filenames:
            if not should_exclude(filename):
                current_dict[filename] = None

    return structure

def print_structure(structure: dict, indent: int = 0):
    """
    Print the directory structure in a readable, indented format.
    """
    for key, value in structure.items():
        prefix = "    " * indent
        if isinstance(value, dict):
            print(f"{prefix}{key}/")
            print_structure(value, indent + 1)
        else:
            print(f"{prefix}{key}")

if __name__ == "__main__":
    # Specify the root directory you want to reflect
    root_directory = os.getcwd()

    # Get the directory structure, excluding specified patterns
    project_structure = get_directory_structure(root_directory)

    # Print the directory structure
    print("Project structure (excluding specified patterns):")
    print_structure(project_structure)

    # Generate a dynamic filename with the current date and time
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"project_structure_DYNAMIC_creation_{timestamp}.json"

    # Write the structure to a JSON file
    with open(output_filename, "w", encoding='utf-8') as f:
        json.dump(project_structure, f, indent=4, ensure_ascii=False)

    print(f"\nThe filtered project structure has been saved to '{output_filename}'.")
