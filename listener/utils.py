import os
import configparser
import re
import yaml
from datetime import date


config = configparser.ConfigParser()
config.read('config.ini')

history_downloaded = config['HISTORY']['HISTORY_DOWNLOADED_FILE']

storage_dir = config['STORAGE']['STORAGE_DIR']

log_file_run = config['LOGGING']['LOG_FILE_RUN']
log_file_error = config['LOGGING']['LOG_FILE_ERROR']

white_file_types = config['WHITELIST']['WHITELIST_FILE_TYPES']

data_rules_path = config['RULES']['DATA_RULES']
dist_dir = config['DIST']['DIST_DIR']

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

# Hàm thêm line vào file
def append_line_to_file(history_file, file_name):
    try:
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(f'{file_name}\n')

    except Exception as e:
        print(f'Error marking file download: {str(e)} (utils.py:append_line_to_file:69)')
        write_log(log_file_error, f'Error marking file download: {str(e)}  (utils.py:append_line_to_file:70)\n')


# Hàm kiểm tra xem tên file đã tồn tại trong file history chưa
def check_file_in_history(size, file_name):
    if check_valid_file_extension(file_name) is False:
        return True
    if size == 0 or file_name == '':
        return True
    try:
        tmp_path = str(size) + '-' + file_name
        # Kiểm tra file có tồn tại không
        if not os.path.exists(history_downloaded):
            return False

        # Mở và đọc file
        with open(history_downloaded, 'r', encoding='utf-8') as f:
            content = f.read()
            if tmp_path in content:
                return True
    except Exception as e:
        print(f'Error checking file existence: {str(e)}  (utils.py:check_file_in_history:108)')
        write_log(log_file_error, f'Error: {str(e)}   (utils.py:check_file_in_history:109)\n')
        return True


# Hàm kiểm tra xem file có đúng định dạng được chỉ định không, nếu không chỉ định extension nào sẽ chấp nhận mọi kiểu file
def check_valid_file_extension(file):
    _, file_extension = os.path.splitext(file)
    return file_extension in white_file_types

# Hàm callback trả về % quá trình tải file
async def progress_callback(current, total):
    percentage = (current / total) * 100
    print(f'{current}/{total} bytes ({percentage:.2f}%) (utils.py:progress_callback:223)')
    write_log(log_file_run, f'{current}/{total} bytes ({percentage:.2f}%) (utils.py:progress_callback:224)\n')


# Hàm tải file 
async def download_file_from_media(client, message):
    try:
        size = message.media.document.size
        file_name_tmp = message.media.document.attributes[0].file_name
        file_name = str(size) + '-' + file_name_tmp
        download_path = os.path.join(storage_dir, file_name)
        # Bắt đầu tải file từ message 
        file_path = await client.download_media(
            message.media,
            file=download_path,
            progress_callback=progress_callback
        )
        if file_path is not None:
            append_line_to_file(history_downloaded, file_path)
        return file_path
            
    except Exception as e:
        print(f'Error during download: {str(e)} (utils.py:download_file_from_media:250)')
        write_log(log_file_error, f'Error during download: {str(e)} (utils.py:download_file_from_media:251)\n')
        return None
    

