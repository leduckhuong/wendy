import os
import asyncio
import configparser
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaDocument

from utils import get_file_hash_before_download, check_file_in_history, download_file_from_media, read_file


config = configparser.ConfigParser()
config.read('config.ini')

# Thông tin đăng nhập Telegram của bạn
api_id = config['TELE_API']['APP_ID']
api_hash = config['TELE_API']['HASH_ID']
phone = config['TELE_API']['PHONE']
username = config['TELE_API']['USERNAME']

session_dir = './sessions'
os.makedirs(session_dir, exist_ok=True)

# Tạo client Telegram với đường dẫn lưu session file
session_file = f'{session_dir}/{username}'
client = TelegramClient(session_file, api_id, api_hash)

download_dir = './storage'
os.makedirs(download_dir, exist_ok=True)

history_read = './history_read.txt'
history_downloaded = './history_downloaded.txt'

@client.on(events.NewMessage)
async def handle_event(event):
    try:
        message = event.message

        # Lấy id đoạn chat

        chat_id = None

        if hasattr(message.peer_id, 'user_id'):
            chat_id = message.peer_id.user_id
        if hasattr(message.peer_id, 'chat_id'):
            chat_id = message.peer_id.chat_id
        if hasattr(message.peer_id, 'channel_id'):
            chat_id = message.peer_id.channel_id

        if chat_id is not None:
            # Nếu message là file thì xử lý trong block if bên dưới
            if isinstance(message.media, MessageMediaDocument):
                file_hash = await get_file_hash_before_download(client, message)
                if file_hash is None:
                    return 
                if check_file_in_history(history_downloaded, file_hash):
                    return
                file_path = await download_file_from_media(client, message, download_dir, file_hash)
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

