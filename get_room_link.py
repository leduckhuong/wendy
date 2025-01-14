import os
import asyncio
import configparser
from telethon import TelegramClient, events

from utils import get_dict_from_message, get_room_link_from_message


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

os.makedirs('./links', exist_ok=True)

history_read = './links.txt'



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
        print(f'Chat id: {chat_id}')

        if chat_id is not None:
            # Chuyển message từ kiểu instance sang kiểu dictionary
            msg_dict = await get_dict_from_message(chat_id, message)
            if msg_dict is not None and msg_dict['type'] == 'link':
                await get_room_link_from_message(msg_dict)
    except Exception as e:
        print(f'Error in event handler: {str(e)}')
        import traceback
        print("Full error:", traceback.format_exc()) 

async def main():
    await client.start()    # Bắt đầu đăng nhập
    
    await client.run_until_disconnected()   # Lắng nghe liên tục từ telegram

asyncio.run(main())

