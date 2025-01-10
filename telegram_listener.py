import os
import asyncio
import configparser
from telethon import TelegramClient, events

from utils import download_message_media, read_file, append_line_to_file, get_dict_from_message


config = configparser.ConfigParser()
config.read('config.ini')

# Thông tin đăng nhập Telegram của bạn
api_id = config['TELE_API']['APP_ID']
api_hash = config['TELE_API']['HASH_ID']
phone = config['TELE_API']['PHONE']
username = config['TELE_API']['USERNAME']

# Đảm bảo thư mục session tồn tại
os.makedirs('./sessions', exist_ok=True)

# Tạo client Telegram với đường dẫn lưu session file
session_file = './sessions/' + username
client = TelegramClient(session_file, api_id, api_hash)

os.makedirs('./storage', exist_ok=True)

download_dir = './storage'
history_read = './history_read.txt'

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
            # Chuyển message từ kiểu instance sang kiểu dictionary
            msg_dict = await get_dict_from_message(chat_id, message)
            if msg_dict is not None:
                # Tải file từ message
                file_path = await download_message_media(client, chat_id, msg_dict, download_dir)
                # Thêm độ trễ 1 giây giữa mỗi lần tải file
                await asyncio.sleep(1)
                if file_path:
                    print(f"Downloaded successfully: {file_path}")
                    # Đọc file
                    await read_file(chat_id ,file_path)
                    # Đánh dấu đã đọc
                    print(f"Read successfully: {file_path}")
                else:
                    print("Downloaded failed")# Tải file về
                
    except Exception as e:
        print(f'Error in event handler: {str(e)}')
        import traceback
        print("Full error:", traceback.format_exc()) 

