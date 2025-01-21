import os
import configparser
import asyncio
from telethon import TelegramClient # type: ignore
from telethon.errors import SessionPasswordNeededError, ChannelPrivateError, ChannelInvalidError # type: ignore
from telethon.tl.functions.messages import GetHistoryRequest # type: ignore
from telethon.tl.types import MessageMediaDocument # type: ignore

from utils import (
    check_file_in_history, get_channel_entity, 
    download_file_from_media, read_file, 
    get_file_hash_before_download, get_room_link_from_message,
    get_room_id
)


# Reading Configs
config = configparser.ConfigParser()
config.read('config.ini')

# Thông tin đăng nhập Telegram của bạn
api_id = config['TELE_API_1']['APP_ID']
api_hash = config['TELE_API_1']['HASH_ID']
phone = config['TELE_API_1']['PHONE']
username = config['TELE_API_1']['USERNAME']

download_dir = './storage'
history_read = './history_read.txt'
history_downloaded = './history_downloaded.txt'

session_dir = './sessions'

# Đảm bảo thư mục session tồn tại
os.makedirs(session_dir, exist_ok=True)

os.makedirs(download_dir, exist_ok=True)

# Tạo client Telegram với đường dẫn lưu session file
session_file = f'{session_dir}/{username}'

client = TelegramClient(session_file, api_id, api_hash)

async def run(phone):
    try:
        await client.start()
        print('Client Created')
        
        # Ensure authorization
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            try:
                await client.sign_in(phone, input('Enter the code: '))
            except SessionPasswordNeededError:
                await client.sign_in(password=input('Password: '))

        me = await client.get_me()
        print(f'Logged in as: {me.username if me.username else me.first_name}')
        
        # list_room_ids = await get_room_id(client)
        # for chat_id in list_room_ids:

        chat_id = 1190150661

        print(f'Chat id: {chat_id}')

        chat = await get_channel_entity(client, chat_id)
        
        offset_id = 0
        limit = 100
        all_messages = []
        total_messages = 0
        total_count_limit = 0

        while True:
            history = await client(GetHistoryRequest(
                peer=chat,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            
            if not history.messages:
                break
            
            messages = history.messages
            for message in messages:
                all_messages.append(message)
            
            offset_id = messages[len(messages) - 1].id
            total_messages = len(all_messages)

            if total_count_limit != 0 and total_messages >= total_count_limit:
                break
        if all_messages:
            for message in all_messages:
                try:
                    if isinstance(message.media, MessageMediaDocument):
                        file_hash = await get_file_hash_before_download(client, message)
                        if file_hash is None:
                            continue 
                        if check_file_in_history(history_downloaded, file_hash):
                            continue
                        file_path = await download_file_from_media(client, message, download_dir, file_hash)
                        # Thêm độ trễ 1 giây giữa mỗi lần tải file
                        await asyncio.sleep(1)
                        if file_path:
                            # Đọc file
                            await read_file(file_path)
                        else:
                            print("Downloaded failed")# Tải file về
                    else:
                        await get_room_link_from_message(message)
                except Exception as e:
                    print(f'Error downloading {e}')
        else:
            print('No messages were retrieved')

    except ChannelPrivateError:
        print('ERROR: This is a private channel. Please:')
        print('1. Join the channel first')
        print('2. Make sure you are using the correct channel ID')
        print('3. Check if you have been banned or removed from the channel')
    except ChannelInvalidError:
        print('ERROR: Invalid channel. Please:')
        print('1. Verify the channel ID is correct')
        print('2. Make sure the channel still exists')
        print('3. Try getting the channel ID from the channels"s URL')
    except ValueError as e:
        print(f'ERROR: Invalid channel ID format: {str(e)}')
        print('Tips:')
        print('1. Try using the channel username if it is public')
        print('2. Make sure you are copying the full channel ID')
        print('3. If using a channel URL, make sure to use only the numeric ID part')
    except Exception as e:
        print(f'Unexpected error: {str(e)}')
    finally:
        await client.disconnect() 

async def main():
    await client.start()    # Bắt đầu đăng nhập
    await run('+84 345525359')

asyncio.run(main())
