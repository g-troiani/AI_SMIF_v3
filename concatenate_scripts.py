# File: concatenate_scripts.py

import os
import chardet

def should_exclude_file(filename):
    """
    Determines if a file should be excluded from concatenation.
    """
    exclude_patterns = [
        '.log', '.env', '.gitignore', '.DS_Store', 'Thumbs.db',
        '__pycache__', '.pyc', '.pyo', '.pyd', '.db', '.sqlite',
        '.swp', '.swo', '~', '.egg-info', 'venv', 'node_modules', '.git',
        '.idea', '.vscode', 'env', 'dist', 'build', '__pycache__.txt', '___pycache__',
        '.mypy_cache', '.pytest_cache', '.ipynb_checkpoints',

        # Now explicitly exclude package-lock.json:
        'package-lock.json'
    ]
    return any(filename.endswith(pattern) or pattern in filename for pattern in exclude_patterns)

def should_include_file(filename):
    """
    Determines if a file should be included in concatenation.
    """
    include_extensions = {
        '.py', '.js', '.css', '.html', '.json', '.ts', '.tsx', '.md'
    }
    return any(filename.endswith(ext) for ext in include_extensions)

def get_comment_syntax(file_type):
    """
    Returns the appropriate comment syntax for the given file type.
    """
    comment_styles = {
        'py': '#',
        'js': '//',
        'css': '/*',
        'html': '<!--',
        'json': '//',   # Using // for JSON files
        'ts': '//',     # TypeScript uses // like JS
        'tsx': '//',    # TSX uses JS/TS style comments
        'md': '<!--'    # Using HTML comment style for Markdown
    }

    comment_end_styles = {
        'css': ' */',
        'html': ' -->',
        'md': ' -->'
    }

    comment_start = comment_styles.get(file_type, '#')
    comment_end = comment_end_styles.get(file_type, '')
    return comment_start, comment_end

def read_file_content(file_path):
    """
    Reads the content of a file, attempting to detect its encoding.
    """
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding'] or 'utf-8'
        try:
            return raw_data.decode(encoding)
        except UnicodeDecodeError:
            return raw_data.decode('latin-1')
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def concatenate_scripts(target_folder):
    """
    Concatenates all included files within the target_folder into a single text file,
    overwriting any previous content each time. The output file will be named
    'CONCAT {target_folder_name}.txt'.
    """
    if not os.path.isdir(target_folder):
        print(f"Error: The folder '{target_folder}' does not exist.")
        return

    top_folder_name = os.path.basename(os.path.normpath(target_folder))

    # Skip creating a file if the folder name is __pycache__-like
    if top_folder_name.startswith("__pycache__"):
        print(f"Skipping folder '{top_folder_name}'.")
        return

    output_file_name = f"CONCAT {top_folder_name}.txt"
    output_file_path = os.path.join(os.getcwd(), output_file_name)

    # Hardcoded path to exclude (directory)
    HARDCODED_EXCLUDE_PATH = os.path.normpath(
        "/home/gian/Desktop/MDC program/ai_smif_v3/components/ui_module/frontend/node_modules"
    )

    # Use 'w' mode to ensure we always start fresh each run
    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# Module: {top_folder_name}\n\n")

        for root, dirs, files in os.walk(target_folder):
            # Exclude certain directories
            dirs[:] = [
                d for d in dirs
                if d not in ('__pycache__', 'venv', 'node_modules')
                and os.path.normpath(os.path.join(root, d)) != HARDCODED_EXCLUDE_PATH
            ]

            for file in sorted(files):
                # Skip if we're currently in the node_modules or pycache directory
                if (
                    '__pycache__' in root or
                    'venv' in root or
                    'node_modules' in root or
                    os.path.normpath(root) == HARDCODED_EXCLUDE_PATH
                ):
                    continue

                # Skip if file is excluded by pattern (now includes package-lock.json)
                if not should_include_file(file) or should_exclude_file(file):
                    continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path)
                file_type = os.path.splitext(file)[1][1:]
                comment_start, comment_end = get_comment_syntax(file_type)

                outfile.write(f"{comment_start} File: {rel_path}{comment_end}\n")
                outfile.write(f"{comment_start} Type: {file_type}{comment_end}\n\n")

                content = read_file_content(file_path)
                if content is not None:
                    outfile.write(content)
                    outfile.write("\n\n")
                else:
                    outfile.write(
                        f"{comment_start} Error: Unable to read file {file_path}{comment_end}\n\n"
                    )

    print(f"Scripts written into '{output_file_name}'.")


if __name__ == "__main__":
    # Fixed parent directory as 'components'
    parent_dir = "components"
    if not os.path.isdir(parent_dir):
        print(f"Error: The folder '{parent_dir}' does not exist.")
    else:
        # Loop over each sub-directory (component) in 'components'
        for component in os.listdir(parent_dir):
            component_path = os.path.join(parent_dir, component)
            if os.path.isdir(component_path):
                # For each component directory, produce an individual CONCAT file
                concatenate_scripts(component_path)




# # File: concatenate_scripts.py


# import os
# import chardet

# def should_exclude_file(filename):
#     """
#     Determines if a file should be excluded from concatenation.
#     """
#     exclude_patterns = [
#         '.log', '.env', '.gitignore', '.DS_Store', 'Thumbs.db',
#         '__pycache__', '.pyc', '.pyo', '.pyd', '.db', '.sqlite',
#         '.swp', '.swo', '~', '.egg-info', 'venv', 'node_modules', '.git',
#         '.idea', '.vscode', 'env', 'dist', 'build', '__pycache__.txt', '___pycache__',
#         '.mypy_cache', '.pytest_cache', '.ipynb_checkpoints',

#         # Now explicitly exclude package-lock.json:
#         'package-lock.json'
#     ]
#     return any(filename.endswith(pattern) or pattern in filename for pattern in exclude_patterns)

# def should_include_file(filename):
#     """
#     Determines if a file should be included in concatenation.
#     """
#     include_extensions = {
#         '.py', '.js', '.css', '.html', '.json', '.ts', '.tsx', '.md'
#     }
#     return any(filename.endswith(ext) for ext in include_extensions)

# def get_comment_syntax(file_type):
#     """
#     Returns the appropriate comment syntax for the given file type.
#     """
#     comment_styles = {
#         'py': '#',
#         'js': '//',
#         'css': '/*',
#         'html': '<!--',
#         'json': '//',   # Using // for JSON files
#         'ts': '//',     # TypeScript uses // like JS
#         'tsx': '//',    # TSX uses JS/TS style comments
#         'md': '<!--'    # Using HTML comment style for Markdown
#     }

#     comment_end_styles = {
#         'css': ' */',
#         'html': ' -->',
#         'md': ' -->'
#     }

#     comment_start = comment_styles.get(file_type, '#')
#     comment_end = comment_end_styles.get(file_type, '')
#     return comment_start, comment_end

# def read_file_content(file_path):
#     """
#     Reads the content of a file, attempting to detect its encoding.
#     """
#     try:
#         with open(file_path, 'rb') as file:
#             raw_data = file.read()
#         result = chardet.detect(raw_data)
#         encoding = result['encoding'] or 'utf-8'
#         try:
#             return raw_data.decode(encoding)
#         except UnicodeDecodeError:
#             return raw_data.decode('latin-1')
#     except Exception as e:
#         print(f"Error reading file {file_path}: {str(e)}")
#         return None

# def concatenate_scripts(target_folder):
#     """
#     Concatenates all included files within the target_folder into a single text file,
#     overwriting any previous content each time. The output file will be named
#     'CONCAT {target_folder_name}.txt'.
#     """
#     if not os.path.isdir(target_folder):
#         print(f"Error: The folder '{target_folder}' does not exist.")
#         return

#     top_folder_name = os.path.basename(os.path.normpath(target_folder))
#     output_file_name = f"CONCAT {top_folder_name}.txt"
#     output_file_path = os.path.join(os.getcwd(), output_file_name)

#     # Hardcoded path to exclude (directory)
#     HARDCODED_EXCLUDE_PATH = os.path.normpath(
#         "/home/gian/Desktop/MDC program/ai_smif_v3/components/ui_module/frontend/node_modules"
#     )

#     # Use 'w' mode to ensure we always start fresh each run
#     with open(output_file_path, 'w', encoding='utf-8') as outfile:
#         outfile.write(f"# Module: {top_folder_name}\n\n")

#         for root, dirs, files in os.walk(target_folder):
#             # Exclude certain directories
#             dirs[:] = [
#                 d for d in dirs
#                 if d not in ('__pycache__', 'venv', 'node_modules')
#                 and os.path.normpath(os.path.join(root, d)) != HARDCODED_EXCLUDE_PATH
#             ]

#             for file in sorted(files):
#                 # Skip if we're currently in the node_modules directory
#                 if (
#                     '__pycache__' in root or
#                     'venv' in root or
#                     'node_modules' in root or
#                     os.path.normpath(root) == HARDCODED_EXCLUDE_PATH
#                 ):
#                     continue

#                 # Skip if file is excluded by pattern (now includes package-lock.json)
#                 if not should_include_file(file) or should_exclude_file(file):
#                     continue

#                 file_path = os.path.join(root, file)
#                 rel_path = os.path.relpath(file_path)
#                 file_type = os.path.splitext(file)[1][1:]
#                 comment_start, comment_end = get_comment_syntax(file_type)

#                 outfile.write(f"{comment_start} File: {rel_path}{comment_end}\n")
#                 outfile.write(f"{comment_start} Type: {file_type}{comment_end}\n\n")

#                 content = read_file_content(file_path)
#                 if content is not None:
#                     outfile.write(content)
#                     outfile.write("\n\n")
#                 else:
#                     outfile.write(
#                         f"{comment_start} Error: Unable to read file {file_path}{comment_end}\n\n"
#                     )

#     print(f"Scripts written into '{output_file_name}'.")


# if __name__ == "__main__":
#     # Fixed parent directory as 'components'
#     parent_dir = "components"
#     if not os.path.isdir(parent_dir):
#         print(f"Error: The folder '{parent_dir}' does not exist.")
#     else:
#         # Loop over each sub-directory (component) in 'components'
#         for component in os.listdir(parent_dir):
#             component_path = os.path.join(parent_dir, component)
#             if os.path.isdir(component_path):
#                 # For each component directory, produce an individual CONCAT file
#                 concatenate_scripts(component_path)