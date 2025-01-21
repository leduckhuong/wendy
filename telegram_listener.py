import os
import asyncio
import configparser
from telethon import TelegramClient, events # type: ignore
from telethon.tl.types import MessageMediaDocument # type: ignore

from utils import get_file_hash_before_download, check_file_in_history, download_file_from_media, read_file


config = configparser.ConfigParser()
config.read('config.ini')

# Thông tin đăng nhập Telegram của bạn
# Thông tin API
API_1 = {
    "id": 1,
    "api_id": config['TELE_API_1']['APP_ID'],
    "api_hash": config['TELE_API_1']['HASH_ID'],
    "phone": config['TELE_API_1']['PHONE'],
    "username": config['TELE_API_1']['USERNAME']
}

API_2 = {
    "id": 1,
    "api_id": config['TELE_API_2']['APP_ID'],
    "api_hash": config['TELE_API_2']['HASH_ID'],
    "phone": config['TELE_API_2']['PHONE'],
    "username": config['TELE_API_2']['USERNAME']
}

session_dir = './sessions'
os.makedirs(session_dir, exist_ok=True)

# Tạo client1 Telegram với đường dẫn lưu session file
session_file1 = f'{session_dir}/{API_1["username"]}'
client1 = TelegramClient(session_file1, API_1['api_id'], API_1['api_hash'])

# Tạo client Telegram với đường dẫn lưu session file
session_file2 = f'{session_dir}/{API_2["username"]}'
client2 = TelegramClient(session_file2, API_2['api_id'], API_2['api_hash'])

download_dir = './storage'
os.makedirs(download_dir, exist_ok=True)

history_read = './history_read.txt'
history_downloaded = './history_downloaded.txt'

@client1.on(events.NewMessage)
async def handle_event(event):
    try:
        message = event.message

        # Nếu message là file thì xử lý trong block if bên dưới
        if isinstance(message.media, MessageMediaDocument):
            file_hash = await get_file_hash_before_download(client1, message)
            if file_hash is None:
                return 
            if check_file_in_history(history_downloaded, file_hash):
                return
            file_path = await download_file_from_media(client1, message, download_dir, file_hash)
            # Thêm độ trễ 1 giây giữa mỗi lần tải file
            await asyncio.sleep(1)
            if file_path:
                # Đọc file
                await read_file(file_path)
                
            else:
                print("Downloaded failed")# Tải file về
                
    except Exception as e:
        print(f'Error in event handler: {str(e)}')
        import traceback
        print("Full error:", traceback.format_exc()) 
    
@client2.on(events.NewMessage)
async def handle_event(event):
    try:
        message = event.message

        # Nếu message là file thì xử lý trong block if bên dưới
        if isinstance(message.media, MessageMediaDocument):
            file_hash = await get_file_hash_before_download(client2, message)
            if file_hash is None:
                return 
            if check_file_in_history(history_downloaded, file_hash):
                return
            file_path = await download_file_from_media(client2, message, download_dir, file_hash)
            # Thêm độ trễ 1 giây giữa mỗi lần tải file
            await asyncio.sleep(1)
            if file_path:
                # Đọc file
                await read_file(file_path)
                
            else:
                print("Downloaded failed")# Tải file về
                
    except Exception as e:
        print(f'Error in event handler: {str(e)}')
        import traceback
        print("Full error:", traceback.format_exc()) 

