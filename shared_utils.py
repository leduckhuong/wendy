"""
Shared utilities for Wendy Telegram Data Collection System
This module contains common functions used by both listener and reader components.
"""

import os
import re
import yaml
import configparser
import shutil
import rarfile  # type: ignore
import pyzipper  # type: ignore
import py7zr  # type: ignore
from datetime import date
from typing import List, Optional

# Configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Paths
log_file_run = config['LOGGING']['LOG_FILE_RUN']
log_file_error = config['LOGGING']['LOG_FILE_ERROR']
history_downloaded = config['HISTORY']['HISTORY_DOWNLOADED_FILE']
storage_dir = config['STORAGE']['STORAGE_DIR']
white_file_types = config['WHITELIST']['WHITELIST_FILE_TYPES']
data_rules_path = config['RULES']['DATA_RULES']
dist_dir = config['DIST']['DIST_DIR']
extract_dir = config['EXTRACT']['EXTRACT_DIR']

# Load rules
def load_rules_from_yaml(rule_path: str) -> dict:
    """Load rules from YAML file"""
    with open(rule_path, 'r') as file:
        return yaml.safe_load(file)

data_rules = load_rules_from_yaml(data_rules_path)

# Logging functions
def write_log(file_path: str, log: str) -> None:
    """Write log to file if path exists"""
    if os.path.exists(file_path):
        with open(file_path, 'a') as f:
            f.write(f'{log}\n')

# Data processing functions
def get_data_from_text(message_text: str) -> None:
    """Extract data from text using regex rules"""
    for rule in data_rules['line_rules']:
        regex = re.compile(rule['pattern'])
        matches = regex.findall(message_text)
        if matches:
            path_today = f'{dist_dir}/{date.today()}.txt'
            if not os.path.exists(path_today):
                with open(path_today, 'w') as f:
                    f.write('')
            with open(path_today, 'a') as f:
                for match in matches:
                    f.write(f'{match}\n')
            break

# File validation functions
def check_valid_file_extension(file: str) -> bool:
    """Check if file extension is in whitelist"""
    _, file_extension = os.path.splitext(file)
    return file_extension in white_file_types

def check_file_in_history(size: int, file_name: str) -> bool:
    """Check if file has been processed before"""
    if not check_valid_file_extension(file_name):
        return True
    if size == 0 or file_name == '':
        return True

    try:
        tmp_path = str(size) + '-' + file_name
        if not os.path.exists(history_downloaded):
            return False

        with open(history_downloaded, 'r', encoding='utf-8') as f:
            content = f.read()
            return tmp_path in content
    except Exception as e:
        error_msg = f'Error checking file existence: {str(e)}'
        print(error_msg)
        write_log(log_file_error, f'{error_msg}\n')
        return True

# History management
def append_line_to_file(history_file: str, file_name: str) -> None:
    """Add file to history"""
    try:
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(f'{file_name}\n')
    except Exception as e:
        error_msg = f'Error marking file download: {str(e)}'
        print(error_msg)
        write_log(log_file_error, f'{error_msg}\n')

# Progress callback for downloads
async def progress_callback(current: int, total: int) -> None:
    """Progress callback for file downloads"""
    percentage = (current / total) * 100
    print(f'{current}/{total} bytes ({percentage:.2f}%)')
    write_log(log_file_run, f'{current}/{total} bytes ({percentage:.2f}%) (shared_utils.py:progress_callback)\n')

# File processing functions
async def read_file_txt(file_path: str) -> Optional[str]:
    """Read and process text file"""
    print(f'Reading file {file_path}')
    try:
        with open(file_path, 'r') as file_txt:
            for line in file_txt:
                line = line.strip()
                get_data_from_text(line)
        return file_path
    except Exception as e:
        error_msg = f'Error indexing document: {e}'
        print(error_msg)
        return None

def remove_file(file_path: str) -> None:
    """Remove file with error handling"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f'File {file_path} removed successfully.')
        else:
            print(f'File {file_path} does not exist.')
    except Exception as e:
        error_msg = f'Error removing file: {str(e)}'
        print(error_msg)

def flatten_extracted_files(root_dir: str) -> List[str]:
    """Flatten directory structure after extraction"""
    extracted_files = []

    for current_dir, dirs, files in os.walk(root_dir, topdown=False):
        for file in files:
            src_path = os.path.join(current_dir, file)
            dest_path = os.path.join(root_dir, file)

            if os.path.abspath(src_path) == os.path.abspath(dest_path):
                extracted_files.append(dest_path)
                continue

            if os.path.exists(dest_path):
                base, ext = os.path.splitext(file)
                i = 1
                while os.path.exists(os.path.join(root_dir, f"{base}_{i}{ext}")):
                    i += 1
                dest_path = os.path.join(root_dir, f"{base}_{i}{ext}")

            shutil.move(src_path, dest_path)
            extracted_files.append(dest_path)

        if current_dir != root_dir and not os.listdir(current_dir):
            os.rmdir(current_dir)

    return extracted_files

def extract_file(file_path: str, extension: str) -> Optional[str]:
    """Extract archive files"""
    try:
        if extension == '.rar':
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)
        elif extension == '.zip':
            with pyzipper.AESZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif extension == '.7z':
            with py7zr.SevenZipFile(file_path, mode='r', password="") as archive:
                archive.extractall(path=extract_dir)
        else:
            print(f'Unsupported file type: {extension}')
            return None

        extract_file_tmp = flatten_extracted_files(extract_dir)
        return file_path

    except Exception as e:
        error_msg = f'Error extracting file: {str(e)}'
        print(error_msg)
        return None
