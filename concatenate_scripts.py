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
        '.swp', '.swo', '~',
    ]
    return any(filename.endswith(pattern) or pattern in filename for pattern in exclude_patterns)

def should_include_file(filename):
    """
    Determines if a file should be included in concatenation.
    """
    include_extensions = {'.py', '.js', '.css', '.html'}
    return any(filename.endswith(ext) for ext in include_extensions)

def get_comment_syntax(file_type):
    """
    Returns the appropriate comment syntax for the given file type.
    """
    comment_styles = {
        'py': '#',
        'js': '//',
        'css': '/*',
        'html': '<!--'
    }
    comment_end_styles = {
        'css': ' */',
        'html': ' -->'
    }
    return comment_styles.get(file_type, '#'), comment_end_styles.get(file_type, '')

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

def concatenate_scripts(target_folder, exclude_dirs):
    """
    Concatenates all scripts within the target_folder into a single text file,
    excluding specified directories and their subdirectories.
    """
    # Normalize exclude_dirs to absolute paths
    exclude_dirs_abs = set()
    for ed in exclude_dirs:
        exclude_dir_abs = os.path.abspath(os.path.normpath(ed))
        exclude_dirs_abs.add(exclude_dir_abs)

    # Normalize the target_folder input
    target_folder_normalized = target_folder.replace('_', ' ').strip().upper()

    if target_folder_normalized == "ALL MODULES":
        # Get all top-level directories excluding excluded ones
        all_dirs = [
            d for d in os.listdir()
            if os.path.isdir(d) and not d.startswith('.')
        ]
        modules = []
        for d in all_dirs:
            dir_abs_path = os.path.abspath(d)
            # Exclude if the directory is in exclude_dirs or a subdirectory of one
            is_excluded = False
            for exclude_dir in exclude_dirs_abs:
                if dir_abs_path == exclude_dir or dir_abs_path.startswith(exclude_dir + os.sep):
                    is_excluded = True
                    break
            if not is_excluded:
                modules.append(d)
        output_file_name = "CONCAT ALL MODULES.txt"
    else:
        if not os.path.isdir(target_folder):
            print(f"Error: The folder '{target_folder}' does not exist.")
            return
        target_folder_abs = os.path.abspath(target_folder)
        # Exclude if the target_folder is in exclude_dirs
        if any(target_folder_abs == ed or target_folder_abs.startswith(ed + os.sep) for ed in exclude_dirs_abs):
            print(f"Error: The folder '{target_folder}' is excluded.")
            return
        modules = [target_folder]
        top_folder_name = os.path.basename(os.path.normpath(target_folder))
        output_file_name = f"CONCAT {top_folder_name}.txt"

    output_file_path = os.path.join(os.getcwd(), output_file_name)

    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        for module in modules:
            module_abs_path = os.path.abspath(module)
            outfile.write(f"# Module: {module}\n\n")
            for root, dirs, files in os.walk(module):
                root_abs_path = os.path.abspath(root)
                # Exclude directories
                dirs_to_keep = []
                for d in dirs:
                    dir_abs_path = os.path.abspath(os.path.join(root, d))
                    # Check if dir_abs_path should be excluded
                    is_excluded = False
                    for exclude_dir in exclude_dirs_abs:
                        if dir_abs_path == exclude_dir or dir_abs_path.startswith(exclude_dir + os.sep):
                            is_excluded = True
                            break
                    if not is_excluded:
                        dirs_to_keep.append(d)
                dirs[:] = dirs_to_keep  # Modify dirs in-place

                # Process files
                for file in sorted(files):
                    if should_include_file(file) and not should_exclude_file(file):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path)  # Get relative path
                        file_type = os.path.splitext(file)[1][1:]
                        comment_start, comment_end = get_comment_syntax(file_type)
                        
                        # Add file path and type with appropriate comment syntax
                        outfile.write(f"{comment_start} File: {rel_path}{comment_end}\n")
                        outfile.write(f"{comment_start} Type: {file_type}{comment_end}\n\n")
                        
                        content = read_file_content(file_path)
                        if content is not None:
                            outfile.write(content)
                            outfile.write("\n\n")
                        else:
                            outfile.write(f"{comment_start} Error: Unable to read file {file_path}{comment_end}\n\n")
        print(f"Scripts concatenated into '{output_file_name}'.")

if __name__ == "__main__":
    # Hardcoded target folder and excluded directories
    target_folder = "components/data_management_module"
    exclude_dirs = [
        'components/__pycache__',
        'tests',
        'migrations',
        'logs',
        #'node_modules',
        'components/backtesting_module',
        #'components/data_management_module',
        'components/integration_communication_module',
        'components/logging_monitoring_module',
        'components/portfolio_management_module',
        'components/reporting_analytics_module',
        'components/risk_management_module',
        'components/strategy_management_module',
        'components/trading_execution_engine',
        'components/ui_module/frontend/node_modules',
        '/dist/assets'
    ]  # Directories to exclude

    concatenate_scripts(target_folder, exclude_dirs)