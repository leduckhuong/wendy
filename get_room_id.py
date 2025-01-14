import os
import asyncio
import configparser
from telethon import TelegramClient
from pymongo import MongoClient 

config = configparser.ConfigParser()
config.read('config.ini')

# Thông tin đăng nhập Telegram của bạn
api_id = config['TELE_API']['APP_ID']
api_hash = config['TELE_API']['HASH_ID']
phone = config['TELE_API']['PHONE']
username = config['TELE_API']['USERNAME']

# Kết nối MongoDB
client = MongoClient(config['MONGO_API']['M0NGO_URI'])
db = client[config['MONGO_API']['MONGO_CL_DATA']]
collection = db[config['MONGO_API']['MONGO_CL_ROOM']]

# Đảm bảo thư mục session tồn tại
os.makedirs('./sessions', exist_ok=True)

# Tạo client Telegram với đường dẫn lưu session file
session_file = './sessions/' + username
client = TelegramClient(session_file, api_id, api_hash)

def saveId(room_id, room_name, room_type):
    try:
        if room_id and room_name and room_type:
            document = {'room_id': room_id, 'room_name': room_name, 'room_type': room_type}
            collection.insert_one(document)
    except Exception as e:
        print(f'Error saving ID: {str(e)}')

async def main():
    await client.start()    # Bắt đầu đăng nhập
    
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        name = dialog.name  
        chat_id = dialog.id 

        # Phân loại loại chat
        if getattr(entity, 'broadcast', False):
            print(f"Kênh (Channel): {name} (ID: {chat_id})")
            saveId(chat_id, name, 'broadcast')
        elif getattr(entity, 'megagroup', False):
            print(f"Nhóm (Group): {name} (ID: {chat_id})")
            saveId(chat_id, name, 'megagroup')
        elif getattr(entity, 'bot', False):
            print(f"Bot: {name} (ID: {chat_id})")
            saveId(chat_id, name, 'bot')
        else:
            print(f"Chat riêng (Private Chat): {name} (ID: {chat_id})")
            saveId(chat_id, name, 'private')

asyncio.run(main())

