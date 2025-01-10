import os
import asyncio
import configparser
from telethon import TelegramClient, events

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

async def main():
    await client.start()    # Bắt đầu đăng nhập
    
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        name = dialog.name  
        chat_id = dialog.id 

        # Phân loại loại chat
        if getattr(entity, 'broadcast', False):
            print(f"Kênh (Channel): {name} (ID: {chat_id})")
        elif getattr(entity, 'megagroup', False):
            print(f"Nhóm (Group): {name} (ID: {chat_id})")
        elif getattr(entity, 'bot', False):
            print(f"Bot: {name} (ID: {chat_id})")
        else:
            print(f"Chat riêng (Private Chat): {name} (ID: {chat_id})")

    await client.run_until_disconnected()   # Lắng nghe liên tục từ telegram

asyncio.run(main())

