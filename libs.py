import os

def write_log(file_path, log):
    if os.path.exists(file_path):
        with open(file_path, 'a') as f:
            f.write(f'{log}\n')