import os
import yaml  # type: ignore
import configparser
import re
import shutil
import rarfile  # type: ignore
import pyzipper # type: ignore
import py7zr # type: ignore
import redis # type: ignore
from datetime import date


config = configparser.ConfigParser()
config.read('config.ini')

data_rules_path = config['RULES']['DATA_RULES']
dist_dir = config['DIST']['DIST_DIR']
extract_dir = config['EXTRACT']['EXTRACT_DIR']

r = redis.Redis()

# libs
def write_log(file_path, log):
    if os.path.exists(file_path):
        with open(file_path, 'a') as f:
            f.write(f'{log}\n')

def load_rules_from_yaml(rule_path):
    with open(rule_path, 'r') as file:
        rules = yaml.safe_load(file)
    return rules['line_rules']

data_rules = load_rules_from_yaml(data_rules_path)

def get_data_from_text(message_text):
    for rule in data_rules:
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

# end libs

async def read_file(file_path):
    try: 
        _, file_extension = os.path.splitext(file_path)
        if file_extension == '.txt':
            return await read_file_txt(file_path)
        elif file_extension in ['.rar', '.zip']:
            extract_file(file_path, file_extension)
        else:
            print(f'Unsupported file type: {file_extension} (utils.py:read_file:34)')
            return None
    except Exception as e:
        print(f'Error reading file: {str(e)} (utils.py:read_file:38)')
        return None

# Nhóm hàm đọc file 
async def read_file_txt(file_path):
    print(f'Reading file {file_path}')
    try: 
        with open(file_path, 'r') as file_txt:
            for line in file_txt:
                line = line.strip()
                get_data_from_text(line)
        return file_path
    except Exception as e:
        print(f'Error indexing document: {e} (utils.py:read_file_txt:379)')
        return None

def remove_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f'File {file_path} removed successfully.')
        else:
            print(f'File {file_path} does not exist.')
    except Exception as e:
        print(f'Error removing file: {str(e)} (utils.py:remove_file:392)')

def flatten_extracted_files(root_dir):
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

def extract_file(file_path, extension):
    try: 
        if extension == '.rar':
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)
        elif extension == '.zip':
            with pyzipper.AESZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif (extension == '.7z'):
            with py7zr.SevenZipFile(file_path, mode='r', password="") as archive:
                archive.extractall(path=extract_dir)
        else:
            print(f'Unsupported file type: {extension} (utils.py:extract_file:406)')
            return None
        extract_file_tmp = flatten_extracted_files(extract_dir)
        for file in extract_file_tmp:
            r.publish("file_channel", file)
        return file_path
    except Exception as e:
        print(f'Error extracting file: {str(e)} (utils.py:extract_file:409)')
        return None
