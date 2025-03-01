# File: utils/find_project_root.py

import os

def find_project_root(starting_dir, target_folder_name='ai_finance'): #ai_smif_v3'):
    current_dir = starting_dir
    while True:
        if os.path.basename(current_dir) == target_folder_name:
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached the root of the filesystem
            raise FileNotFoundError(f"Could not find {target_folder_name} in the directory hierarchy.")
        current_dir = parent_dir
