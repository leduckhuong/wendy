import os
import re
import yaml
import pyzipper
import rarfile
import py7zr
from datetime import datetime
import configparser

from openpyxl import load_workbook
import csv

from telethon.errors import ChannelPrivateError, ChannelInvalidError
from telethon.tl.types import  PeerChat, PeerChannel, MessageMediaDocument

from pymongo import MongoClient

config = configparser.ConfigParser()
config.read('config.ini')

history_read = './history_read.txt'


# Hàm thêm line vào file
def append_line_to_file(history_file, file_name):
    try:
        # Kiểm tra nếu file chưa tồn tại, tạo file rỗng
        if not os.path.exists(history_file):
            with open(history_file, 'w', encoding='utf-8') as f:
                pass  # Tạo file rỗng nếu chưa tồn tại

        # Nếu file_name chưa có, ghi thêm vào cuối file
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(f'{file_name}\n')
        # print(f'Marked {file_name} as downloaded.')

    except Exception as e:
        print(f'Error marking file download: {str(e)}')


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


# Hàm kiểm tra mail có thuộc miền chỉ định không, nếu không chỉ định email nào thì mặc định là mọi miền 
mail_extensions = []
def check_custom_mail(mail):
    if len(mail_extensions) == 0:
        return True
    return any(mail.endswith(suffix) for suffix in mail_extensions)


# Hàm kiểm tra xem tên file đã tồn tại trong file history chưa
def check_file_in_history(history_file, path):
    try:
        # Kiểm tra file có tồn tại không
        if not os.path.exists(history_file):
            return False

        # Mở và đọc file
        with open(history_file, 'r', encoding='utf-8') as f:
            content = f.read()
            file_name = os.path.basename(path)
            if file_name in content:
                return True
    except Exception as e:
        print(f'Error checking file existence: {str(e)}')
    return False


# Hàm kiểm tra xem file có đúng định dạng được chỉ định không, nếu không chỉ định extension nào sẽ chấp nhận mọi kiểu file
file_extensions = ['.txt']
def check_file_valid(file):
    _, file_extension = os.path.splitext(file)
    return file_extension in file_extensions


# Đọc file YAML để lấy các quy tắc regex
rules_file='./line_rules.yaml'
def load_rules_from_yaml(rule_path):
    with open(rule_path, 'r') as file:
        rules = yaml.safe_load(file)
    return rules['line_rules']

# Hàm kiểm tra định dạng của line
def check_line_format(rules, line):

    # Duyệt qua từng quy tắc trong danh sách
    for rule in rules:
        for rule_name, rule_pattern in rule.items():
            x = re.match(rule_pattern, line) 
            if x:
                return [rule_name, x]  # Trả về tên quy tắc đã khớp
    
    print('Not matching rule')
    return None  # Không có quy tắc nào khớp

# Kiểm tra block dữ liệu trong file
def check_file_format(path):
    with open(path) as file:
        separate_line,separate_line2 = 0,0
        for line in file:
            if line.strip() == '':
                separate_line = separate_line + 1
            if line.strip() == '===============':
                separate_line2 = separate_line2 + 1
            if separate_line == 4:
                return 2
            if separate_line2 == 4:
                return 3
        return 1 

# Hàm kiểm tra khung giờ
def check_peak_time():
    current_hour = datetime.now().hour
    # Giả sử giờ cao điểm là 18:00 đến 21:00 (3 giờ)
    # Giờ ít lưu lượng là từ 00:00 đến 06:00 và 06:00 đến 12:00
    if 18 <= current_hour <= 21:
        return True  # Là giờ cao điểm, sẽ đọc file
    return False


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


# Nhóm hàm extract file
async def extract_zip(zip_file_path, extract_file_path, password=None):
    try:
        # Tạo thư mục đích nếu chưa có
        os.makedirs(extract_file_path, exist_ok=True)

        # Lấy danh sách các tệp và thư mục trước khi giải nén
        before_extract = set(os.listdir(extract_file_path))

        print(f'Before extract file: {before_extract}')

        # Giải nén vào thư mục đích
        with pyzipper.AESZipFile(zip_file_path, 'r') as zip_ref:
            if password:
                zip_ref.extractall(extract_file_path, pwd=password.encode('utf-8'))
            else:
                zip_ref.extractall(extract_file_path)
        
        print('Extract successful')

        # Lấy danh sách các tệp và thư mục sau khi giải nén
        after_extract = set(os.listdir(extract_file_path))

        print(f'After extract file: {after_extract}')

        # Tìm sự khác biệt giữa hai danh sách: các tệp mới giải nén
        new_files = after_extract - before_extract
        print(f'New extract file: {new_files}')

        # Đổi tên file 
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
        
        print(f'Extract file zip renamed_files: {renamed_files}')

        for file_path in renamed_files:
            if check_file_in_history(history_read, file_path):
                print(f'Extract file zip file_path: {file_path}')
                os.remove(f'./storage/{file_path}')
        # os.remove(zip_file_path)
        return renamed_files

    except RuntimeError as e:
        if 'password required' in str(e).lower():
            print('This zip file requires a password.')
        elif 'bad password' in str(e).lower():
            print('The password is incorrect.')
        else:
            print(f'RuntimeError: {str(e)}')
    except Exception as e:
        print(f'Error: {str(e)}')
    print('Can not extract zip file')
    return None

async def extract_rar(rar_file_path, extract_file_path, password=None):
    try:
        os.makedirs(extract_file_path, exist_ok=True)
        
        before_extract = sett(os.listdir(extract_file_path))

        with rarfile.RarFile(rar_file_path, 'r') as rar_ref:
            if password:
                rar_ref.extractall(extract_file_path, pwd=password)
            else:
                rar_ref.extractall(extract_file_path)

        # print('Extract successful')

        # Lấy danh sách các tệp và thư mục sau khi giải nén
        after_extract = set(os.listdir(extract_file_path))

        # Tìm sự khác biệt giữa hai danh sách: các tệp mới giải nén
        new_files = after_extract - before_extract

        # Đổi tên file 
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
        
        print(f'Extract file zip renamed_files: {renamed_files}')

        for file_path in renamed_files:
            if check_file_in_history(history_read, file_path):
                print(f'Extract file zip file_path: {file_path}')
                os.remove(f'./storage/{file_path}')

        # os.remove(zip_file_path)
        return renamed_files

    except rarfile.BadRarFile as e:
        print('The RAR file is corrupted.')
    except rarfile.RarWrongPassword:
        print('The password is incorrect.')
    except Exception as e:
        print(f'Error: {str(e)}')

async def extract_7z(sevenz_file_path, extract_file_path, password=None):
    try:
        os.makedirs(extract_file_path, exist_ok=True)
        with py7zr.SevenZipFile(sevenz_file_path, mode='r', password=password) as archive:
            archive.extractall(path=extract_file_path)

        # print('Extract successful')

        # Lấy danh sách các tệp và thư mục sau khi giải nén
        after_extract = set(os.listdir(extract_file_path))

        # Tìm sự khác biệt giữa hai danh sách: các tệp mới giải nén
        new_files = after_extract - before_extract
        
        # Đổi tên file 
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
        
        print(f'Extract file zip renamed_files: {renamed_files}')

        for file_path in renamed_files:
            if check_file_in_history(history_read, file_path):
                print(f'Extract file zip file_path: {file_path}')
                os.remove(f'./storage/{file_path}')

        # os.remove(zip_file_path)
        return renamed_files

    except py7zr.Bad7zFile:
        print('The 7z file is corrupted.')
    except RuntimeError as e:
        if 'incorrect password' in str(e).lower():
            print('The password is incorrect.')
        else:
            print(f'RuntimeError: {str(e)}')
    except Exception as e:
        print(f'Error: {str(e)}')

async def extract_file(file_path, extract_file_path):
    _, file_extension = os.path.splitext(file_path)
    path_file_extract = None
    if (file_extension == '.zip'):
        path_file_extract = await extract_zip(file_path, extract_file_path)
    if (file_extension == '.rar'):
        path_file_extract = await extract_rar(file_path, extract_file_path)
    if (file_extension == '.7z'):
        path_file_extract = await extract_7z(file_path, extract_file_path)
    return list(path_file_extract)

# Hàm trả về message kiểu dict
history_downloaded = './history_downloaded.txt'
async def get_dict_from_message(chat_id, message):
    # Kiểm tra nếu message là instance thì OK
    if isinstance(message.media, MessageMediaDocument):
        file_name = None
        # lấy tên file
        for attribute in message.media.document.attributes:
            if hasattr(attribute, 'file_name'):
                file_name = f'{chat_id}-{attribute.file_name}'
                break
        # file không có tên thì đặt tên file bằng document_{message.id}
        if not file_name:
            file_name = f'{chat_id}-{message.id}'
        # Kiểm tra xem file đã từng được download chưa
        if not check_file_in_history(history_downloaded, file_name):
            msg_dict = message.to_dict()
            msg_dict['file_name'] = file_name
            
            if hasattr(message.peer_id, 'user_id'):
                msg_dict['user_id'] = chat_id
            elif hasattr(message.peer_id, 'chat_id'):
                msg_dict['chat_id'] = chat_id
            elif hasattr(message.peer_id, 'channel_id'):
                msg_dict['channel_id'] = chat_id
            return msg_dict
        print(f'File {file_name} alreadys exist')
        return None


# Hàm callback trả về % quá trình tải file
async def progress_callback(current, total):
    percentage = (current / total) * 100
    print(f'{current}/{total} bytes ({percentage:.2f}%)')


# Hàm tải file 
async def download_file_from_media(client, chat_id, message, download_dir='./storage'):
    try:
        # Tạo storage nếu không tồn tại 
        os.makedirs(download_dir, exist_ok=True)

        # Nếu chat_id là kiểu số nguyên (user_id, chat_id, hoặc channel_id), chuyển đổi thành đối tượng Peer thích hợp
        peer_chat_id = None
        if 'user_id' in message:
            peer_chat_id = message['user_id']
        if 'chat_id' in message:
            peer_chat_id = PeerChat(message['chat_id'])
        if 'channel_id' in message:
            peer_chat_id = PeerChannel(message['channel_id'])
        if peer_chat_id == None:
            print('Không có thông tin hợp lệ trong message để xác định Peer')
            return None
        
        # Lấy tin nhắn gốc sử dụng đối tượng Peer phù hợp
        original_message = await client.get_messages(peer_chat_id, ids=message['id'])
            
        if not original_message or not original_message.media:
            print('No media found in original message')
            return None
        # print(f'peer_chat_id: {type(peer_chat_id)}')
        # Get file name
        file_name = None
        if hasattr(original_message.media, 'document') and original_message.media.document:
            for attribute in original_message.media.document.attributes:
                if hasattr(attribute, 'file_name'):
                    file_name = str(chat_id) + '-' +  attribute.file_name
                    break
        
        if not file_name:
            return None
            
        if check_file_valid(file_name):
            download_path = os.path.join(download_dir, file_name)
            print(f'Downloading file: {file_name}')
            # Download using original message object
            file_path = await client.download_media(
                original_message.media,
                file=download_path,
                progress_callback=progress_callback
            )
            
            if file_path:
                # print(f'Successfully downloaded to: {file_path}')
                append_line_to_file('./history_downloaded.txt', file_name)
                return file_path
            else:
                print(f'Download failed for: {file_name}')
                return None
            
    except Exception as e:
        print(f'Error during download: {str(e)}')
        import traceback
        print('Full error:', traceback.format_exc())
        return None


# Hàm đọc file
async def read_file(chat_id , path):
    try:
        if os.path.isfile(path):
            print('read_file file is file')
            file_name = os.path.basename(path)
            if path.count('/') == 2:
                file_path = path
            else:
                index_file_name = path.index(file_name)
                path_dir = path[:index_file_name]
                file_path = f'{chat_id}-{file_name}'

            if not check_file_in_history(history_read, file_path):
                if not check_compress_file(path):
                    if check_file_valid(path):
                        _, file_extension = os.path.splitext(path)
                        if file_extension == '.txt':
                            file_format = check_file_format(path)
                            if file_format == 1:
                                with open(path, 'r') as file_txt:
                                    for line in file_txt:
                                        line = line.strip()

                                        # Tải các quy tắc từ file YAML
                                        rules = load_rules_from_yaml(rules_file)
                                        line_match = check_line_format(rules, line)
                                        if line_match[0]=='rule1':
                                            print('Matched rule 1')
                                            print('URL:', line_match[1].group(1))
                                            print('User:', line_match[1].group(2))
                                            print('Password:', line_match[1].group(3))
                                            # await save_data(chat_id, path, base_url, mail, password, '', '')
                                        if line_match[0]=='rule2':
                                            print('Matched rule 2')
                                            print('URL:', line_match[1].group(1))
                                            print('User:', line_match[1].group(2))
                                            print('Password:', line_match[1].group(3))
                                            # await save_data(chat_id, path, base_url, mail, password, '', '')
                                        if line_match[0]=='rule3':
                                            print('Matched rule 3')
                                            print('User:', line_match[1].group(1))
                                            print('Password:', line_match[1].group(2))
                                            print('URL:', line_match[1].group(3))
                                            # await save_data(chat_id, path, base_url, mail, password, '', '')
                                        if line_match[0]=='rule4':
                                            print('Matched rule 4')
                                            print('User:', line_match[1].group(1))
                                            print('Password:', line_match[1].group(2))
                                            # await save_data(chat_id, path, '', mail, password, '', '')
                
                            elif file_format == 2:
                                with open(path) as file:
                                    content = file.read()  
                                    block = content.split('\n\n')  
                                    for item in block:
                                        url, mail, password = '','',''
                                        lines_item = item.split('\n')
                                        for line_item in lines_item:
                                            pos1 = line_item.find(':')
                                            if 'url' in line_item:
                                                url = line_item[pos1+1:]
                                            if 'login' in line_item:
                                                mail = line_item[pos1+1:]
                                            if 'password' in line_item:
                                                password = line_item[pos1+1:]
                                        print('Url: ', url)
                                        print('Mail: ', mail)
                                        print('Password: ', password)
                
                            # elif file_format == 3:
                            #     with open(path) as file:
                            #         content = file.read()  
                            #         block = content.split('\n===============')
                            #         for item in block:
                            #             url, mail, password = '', '', ''
                            #             lines_item = item.split('\n')
                            #             for line_item in lines_item:
                            #                 pos1 = line_item.find(':')
                            #                 if 'URL' in line_item:
                            #                     url = line_item[pos1 + 1:].strip()
                            #                 if 'Mail' in line_item:
                            #                     mail = line_item[pos1 + 1:].strip()
                            #                 if 'Password' in line_item:
                            #                     password = line_item[pos1 + 1:].strip()
                            #             print('Url: ', url)
                            #             print('Mail: ', mail)
                            #             print('Password: ', password)

                            if path.count('/') == 2:
                                print('append 1')
                                append_line_to_file(history_read, path)
                            # else:
                            #     index_file_name = path.index(file_name)
                            #     path_dir = path[:index_file_name]
                            #     print('append 2')
                            #     append_line_to_file(history_read, path_dir +file_name)
                            return path
                # else:  # Nếu là file nén
                    # Đường dẫn giải nén
                    # extract_dir = './storage/'
                    # list_extract = await extract_file(path, extract_dir)
                    # if list_extract:

                        # Sau khi giải nén, đọc nội dung các file trong thư mục đã giải nén
                        # for extract_path_item in list_extract:
                        #     item_path = os.path.join(extract_dir, extract_path_item)
                        #     await read_file(chat_id, item_path)

                # Xóa file sau khi đã đọc và xử lý
                # os.remove(path)
                # print(f'File {path} has been processed and deleted.')

    #     elif os.path.isdir(path):
    #         for item in os.listdir(path):
    #             item_path = os.path.join(path, item)
    #             await read_file(chat_id, item_path)
    #     return None
    except Exception as e:
        print(f'Error: {e}')
        return None

# Nhóm hàm đọc file 
# Đọc file xlsx
def read_table_xlsx(path):
    workbook = load_workbook(filename=path, data_only=True)
    sheet = workbook.active  # Hoặc bạn có thể chỉ định sheet cụ thể

    columns = [cell.value for cell in sheet[1]]

    require_columns = ['CUSTOMER_NAME', 'BIRTH_DATE', 'PHONE', 'EMAIL', 'PASSWORD']
    valid_columns = [col for col in columns if col in require_columns]

    if valid_columns:
    
        for row in sheet.iter_rows(min_row=2, values_only=True): 
            row_data = {col: row[i] for i, col in enumerate(columns) if col in valid_columns}

            if row_data['EMAIL'] is not None:
                if check_custom_mail(row_data['EMAIL']):
                    if 'BIRTH_DATE' in row_data and isinstance(row_data['BIRTH_DATE'], datetime):
                        row_data['BIRTH_DATE'] = row_data['BIRTH_DATE'].strftime('%d/%m/%Y')
                    print(row_data)
    else:
        print('Không có cột nào trong danh sách yêu cầu tồn tại trong file.')

# Đọc file csv
def read_table_csv(path):
    with open(path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            print(row)


# Hàm lưu dữ liệu
async def save_data(channel, filename, url, user, password, name, phone):
    try:
        if user != '' and password != '':
            document = {'channel': channel, 'filename': filename, 'user': user, 'pass': password}
            if url != '':
                document['url'] = url 
            if name != '':
                document['name'] = name
            if phone != '':
                document['phone'] = phone
            
            collection.insert_one(document)

    except Exception as e:
        print(f'Error: {e}')


# Kết nối MongoDB
client = MongoClient(config['MONGO_API']['M0NGO_URI'])
db = client[config['MONGO_API']['MONGO_DB']]
collection = db[config['MONGO_API']['MONGO_CL']]

# Hàm lưu dữ liệu
async def save_data(channel, filename, url, user, password, name, phone):
    try:
        if user != '' and password != '':
            document = {'channel': channel, 'filename': filename, 'user': user, 'pass': password}
            if url != '':
                document['url'] = url 
            if name != '':
                document['name'] = name
            if phone != '':
                document['phone'] = phone
            
            collection.insert_one(document)

    except Exception as e:
        print(f'Error: {e}')

