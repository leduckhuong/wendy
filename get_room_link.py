import os
import asyncio
import configparser
from telethon import TelegramClient, events

from utils import load_rules_from_yaml, check_line_format


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


# Đọc file YAML để lấy các quy tắc regex
link_rules='./link_rules.yaml'

@client.on(events.NewMessage)
async def handle_event(event):
    try:
        message = event.message
        if message.media and hasattr(message.media, 'webpage') and message.media.webpage:
            url = message.media.webpage.url
            print(f"URL: {url}")
            rules = load_rules_from_yaml(link_rules)
            matches = check_line_format(rules, url)
            if matches:
                print(matches[1].group(0))
    except Exception as e:
        print(f'Error in event handler: {str(e)}')
        import traceback
        print("Full error:", traceback.format_exc()) 

async def main():
    await client.start()    # Bắt đầu đăng nhập
    
    await client.run_until_disconnected()   # Lắng nghe liên tục từ telegram

asyncio.run(main())

