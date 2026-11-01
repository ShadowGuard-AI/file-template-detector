import argparse
import logging
import pathlib
import re
import os
import stat
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Identifies if a file conforms to a known template format.")
    parser.add_argument("file_path", type=str, help="The path to the file to analyze.")
    parser.add_argument("template_path", type=str, help="The path to the template file.")
    parser.add_argument("--log_level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the logging level.")
    return parser.parse_args()

def compare_file_to_template(file_path, template_path):
    """
    Compares a file to a template definition.

    Args:
        file_path (str): The path to the file to analyze.
        template_path (str): The path to the template file.

    Returns:
        bool: True if the file conforms to the template, False otherwise.
    """
    try:
        # Check if files exist and are readable
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return False
        if not os.path.exists(template_path):
            logging.error(f"Template file not found: {template_path}")
            return False

        if not os.access(file_path, os.R_OK):
            logging.error(f"Cannot read file: {file_path} - insufficient permissions.")
            return False

        if not os.access(template_path, os.R_OK):
            logging.error(f"Cannot read template file: {template_path} - insufficient permissions.")
            return False
        
        # Both files are read with undecodable bytes dropped. A binary file
        # can therefore conform to a template written against its surviving
        # text, which is a lenient reading I keep for config style files.
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            file_content = f.readlines()

        with open(template_path, 'r', encoding='utf-8', errors='ignore') as t:
            template_content = t.readlines()

        # Line count must match exactly. A file with extra or missing
        # lines does not conform, and a zero line file does not conform
        # to a non-empty template.
        if len(file_content) != len(template_content):
            logging.warning(f"File and template have different number of lines: file has {len(file_content)}, template has {len(template_content)}.")
            return False

        match = True
        for i in range(len(file_content)):
            # Both lines are stripped before any comparison, so leading and
            # trailing whitespace can never make a file fail its template. A
            # template that cares about indentation cannot say so in this format.
            template_line = template_content[i].strip()
            file_line = file_content[i].strip()

            # If template line is a regex, check file line against it.  Otherwise, do exact match.
            # re.match anchors at the start of the line only. A REGEX line
            # constrains how the file line begins, not what it contains overall,
            # unless the pattern itself ends with a dollar anchor. A pattern that
            # fails to compile raises, is caught by the outer handler, and comes
            # back as a plain non conformance: a broken template and a wrong file
            # print the same verdict.
            if template_line.startswith("REGEX:"):
                regex = template_line[6:].strip() #Extract the regex
                if not re.match(regex, file_line):
                    logging.warning(f"Line {i+1} does not match the regex: {regex}")
                    match = False
                    break
            elif template_line != file_line:
                logging.warning(f"Line {i+1} does not match. Template: {template_line}, File: {file_line}")
                match = False
                break

        # Either mismatch path breaks out at the first bad line. The verdict is
        # exact, but the report names one line only, however many more differ.
        return match


    except FileNotFoundError:
        logging.error("File not found during comparison.")
        return False
    except Exception as e:
        logging.exception(f"An error occurred during comparison: {e}")
        return False

def log_file_warnings(filepath):
    """
    Logs warnings about the file without blocking the comparison.
    Ownership is never a reason to refuse a file: ordinary users own
    the files this tool exists to check. A symlink, world writable
    permissions, and a large size are logged as warnings, and the
    comparison runs anyway.
    Args:
        filepath (str): The path to the file.
    """

    try:
        file_path = pathlib.Path(filepath)

        if file_path.is_symlink():
            logging.warning(f"File is a symbolic link: {filepath}. Comparing anyway.")

        st = file_path.stat()
        permissions = stat.filemode(st.st_mode)
        if st.st_mode & stat.S_IWOTH:
            logging.warning(f"File has world-writable permissions: {filepath} ({permissions}). Comparing anyway.")

        file_size = st.st_size
        max_size = 10 * 1024 * 1024  # 10 MB limit
        if file_size > max_size:
            logging.warning(f"File exceeds maximum allowed size ({file_size} bytes > {max_size} bytes): {filepath}. Comparing anyway.")

    except Exception as e:
        logging.error(f"Error during file checks for {filepath}: {e}")


def main():
    """
    Main function to execute the file template detector.
    """
    args = setup_argparse()

    # Set logging level
    logging.getLogger().setLevel(args.log_level.upper())

    # Input validation
    file_path = args.file_path
    template_path = args.template_path

    if not isinstance(file_path, str):
        logging.error("File path must be a string.")
        sys.exit(1)

    if not isinstance(template_path, str):
        logging.error("Template path must be a string.")
        sys.exit(1)

    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        sys.exit(1)

    if not os.path.exists(template_path):
        logging.error(f"Template file not found: {template_path}")
        sys.exit(1)

    log_file_warnings(file_path)

    # Call the comparison function
    if compare_file_to_template(file_path, template_path):
        logging.info("File conforms to the template.")
        sys.exit(0)
    else:
        logging.warning("File does NOT conform to the template.")
        sys.exit(1)

if __name__ == "__main__":
    # Usage Examples:
    # 1. Basic Usage:
    # python main.py config.txt template.txt
    #
    # 2. With Debug Logging:
    # python main.py config.txt template.txt --log_level DEBUG
    #
    # Template examples:
    # Add "REGEX:^Version: \d+\.\d+$"  to template.txt to check the corresponding line in config.txt is a version number
    main()