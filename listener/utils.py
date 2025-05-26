import os
import pyzipper # type: ignore
import rarfile # type: ignore
import py7zr # type: ignore
from datetime import datetime
import configparser
import hashlib
import re
import yaml

from telethon.tl.types import PeerChannel # type: ignore

from libs import write_log


config = configparser.ConfigParser()
config.read('config.ini')


history_read = config['HISTORY']['HISTORY_FILE']
history_downloaded = config['HISTORY']['HISTORY_DOWNLOADED_FILE']


log_file_run = config['LOGGING']['LOG_FILE_RUN']
log_file_error = config['LOGGING']['LOG_FILE_ERROR']

white_file_types = config['WHITELIST']['WHITELIST_FILE_TYPES']


async def get_file_hash_before_download(client, message):
    document = message.media.document
            
    # Tạo buffer để lưu toàn bộ dữ liệu
    file_data = bytearray()
    
    # Tải và lưu từng chunk
    async for chunk in client.iter_download(document, chunk_size=1024*1024):
        file_data.extend(chunk)
    
    # Tính hash từ data trong memory
    return hashlib.md5(file_data).hexdigest()

def get_file_hash_after_download(file_path, chunk_size=1024*1024):
    md5_hash = hashlib.md5()
    total_bytes = 0
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(chunk_size), b''):
            md5_hash.update(byte_block)
            total_bytes += len(byte_block)
    return md5_hash.hexdigest()

# Hàm thêm line vào file
def append_line_to_file(history_file, file_name):
    try:
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(f'{file_name}\n')

    except Exception as e:
        print(f'Error marking file download: {str(e)} (utils.py:append_line_to_file:69)')
        write_log(log_file_error, f'Error marking file download: {str(e)}  (utils.py:append_line_to_file:70)\n')


# Hàm kiểm tra đoạn chat có phải là nhóm hoặc channel không
def check_chat_type(chat_id):
    if str(chat_id).startswith('-100'):
        return True
    return False


# Hàm kiểm tra định dạng file có phải file nén không
compress_extensions = ['.zip', '.rar', '.7z']
def check_compress_file(file):
    _, file_extension = os.path.splitext(file)
    return file_extension in compress_extensions


# Hàm kiểm tra xem tên file đã tồn tại trong file history chưa
def check_file_in_history(history_file, file_hash):
    try:
        # Kiểm tra file có tồn tại không
        if not os.path.exists(history_file):
            return False

        # Mở và đọc file
        with open(history_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if file_hash in content:
                return True
    except Exception as e:
        print(f'Error checking file existence: {str(e)}  (utils.py:check_file_in_history:108)')
        write_log(log_file_error, f'Error: {str(e)}   (utils.py:check_file_in_history:109)\n')
    return False


# Hàm kiểm tra xem file có đúng định dạng được chỉ định không, nếu không chỉ định extension nào sẽ chấp nhận mọi kiểu file
def check_valid_file_extension(file):
    _, file_extension = os.path.splitext(file)
    return file_extension in white_file_types

# Hàm Rename tên file sau khi giải nén
async def rename_extract_file(extract_file_path, new_files):
    renamed_files = []
    for item in new_files:
        item_path = os.path.join(extract_file_path, item)

        if os.path.isfile(item_path):  # Nếu là file
            file_size = str(os.path.getsize(item_path)) 
            # Đổi tên file
            new_name = f'{file_size}-{item_path}'
            new_path = os.path.join(extract_file_path, new_name)
            os.rename(item_path, new_path)
            renamed_files.append(new_name)
        
        elif os.path.isdir(item_path):  # Nếu là thư mục
            # Đổi tên các file bên trong thư mục
            for root, _, files in os.walk(item_path):
                for file_name in files:
                    old_file_path = os.path.join(root, file_name)
                    # Lấy kích thước file
                    file_size = os.path.getsize(old_file_path)
                    # Tạo tên file mới
                    new_file_name = f'{file_size}-{file_name}'

                    new_file_path = os.path.join(root, new_file_name)
                    os.rename(old_file_path, new_file_path)
                    renamed_files.append(os.path.relpath(new_file_path, extract_file_path))

    return renamed_files

async def extract_file(file_path, extract_dir, password=None):
    try:
        os.makedirs(extract_dir, exist_ok=True)
        _, file_extension = os.path.splitext(file_path)
        before_extract = set(os.listdir(extract_dir))

        if (file_extension == '.zip'):   
            with pyzipper.AESZipFile(file_path, 'r') as zip_ref:
                if password:
                    zip_ref.extractall(extract_dir, pwd=password.encode('utf-8'))
                else:
                    zip_ref.extractall(extract_dir)
        elif (file_extension == '.rar'):
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                if password:
                    rar_ref.extractall(extract_dir, pwd=password)
                else:
                    rar_ref.extractall(extract_dir)
        elif (file_extension == '.7z'):
            with py7zr.SevenZipFile(file_path, mode='r', password=password) as archive:
                archive.extractall(path=extract_dir)

        after_extract = set(os.listdir(extract_dir))

        new_files = after_extract - before_extract

        # Đổi tên file 
        renamed_files = []
        for item in new_files:
            item_path = os.path.join(extract_dir, item)

            if os.path.isfile(item_path):  # Nếu là file
                file_hash = get_file_hash_after_download(item_path)
                # Đổi tên file
                new_name = f'{file_hash}-{item_path}'
                new_path = os.path.join(extract_dir, new_name)
                os.rename(item_path, new_path)
                renamed_files.append(new_name)
            
            elif os.path.isdir(item_path):  # Nếu là thư mục
                # Đổi tên các file bên trong thư mục
                root_dir = None
                for root, _, files in os.walk(item_path):
                    for file_name in files:
                        old_file_path = os.path.join(root, file_name)
                        # Lấy mã băm file
                        file_hash = get_file_hash_after_download(old_file_path)
                        # Tạo tên file mới
                        new_file_name = f'{file_hash}-{file_name}'

                        new_file_path = os.path.join('./storage', new_file_name)
                        os.rename(old_file_path, new_file_path)
                        renamed_files.append(os.path.relpath(new_file_path, extract_dir))
                    root_dir = root
                os.rmdir(root_dir)


        for file_path in renamed_files:
            if check_file_in_history(history_read, file_hash):
                print(f'Extract file zip file_path: {file_path} (utils.py:extract_file:208)')
                write_log(log_file_run, f'Extract file zip file_path: {file_path} (utils.py:extract_file:209)\n')
                file_path_full = f'./storage/{file_path}'
                if os.path.exists(file_path_full):
                    os.remove(file_path_full)
        return list(renamed_files)
        
    except Exception as e:
        print(f'Error: {str(e)} (utils.py:extract_file:216)')
        write_log(log_file_error, f'Error: {str(e)} (utils.py:extract_file:217)\n')
    return None

# Hàm callback trả về % quá trình tải file
async def progress_callback(current, total):
    percentage = (current / total) * 100
    print(f'{current}/{total} bytes ({percentage:.2f}%) (utils.py:progress_callback:223)')
    write_log(log_file_run, f'{current}/{total} bytes ({percentage:.2f}%) (utils.py:progress_callback:224)\n')


# Hàm tải file 
async def download_file_from_media(client, message, download_dir, file_hash):
    try:
        file_name = None
        if hasattr(message.media, 'document') and message.media.document:
            for attribute in message.media.document.attributes:
                if hasattr(attribute, 'file_name'):
                    file_name = str(file_hash) + '-' +  attribute.file_name
                    break
        file_path = None
        if check_valid_file_extension(file_name):
            download_path = os.path.join(download_dir, file_name)
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
    
# Hàm kiểm tra định dạng của line
def check_line_format(rules, line):
    # Duyệt qua từng quy tắc trong danh sách
    for rule in rules:
        for rule_name, rule_pattern in rule.items():
            x = re.findall(rule_pattern, line) 
            if x:
                return [rule_name, x]  # Trả về tên quy tắc đã khớp
    return None  # Không có quy tắc nào khớp

