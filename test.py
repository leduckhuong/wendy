import os
import configparser
import asyncio
from telethon import TelegramClient # type: ignore
from telethon.errors import SessionPasswordNeededError, ChannelPrivateError, ChannelInvalidError # type: ignore
from telethon.tl.functions.messages import GetHistoryRequest # type: ignore
from telethon.tl.types import MessageMediaDocument # type: ignore

from utils import (
    write_log,
    get_channel_entity, 
    get_room_link_from_message,
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

log_file_run = './logs/run.log'
log_file_error = './logs/error.log'

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
        write_log(log_file_run, 'Client Started\n')
        
        # Ensure authorization
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            try:
                await client.sign_in(phone, input('Enter the code: '))
            except SessionPasswordNeededError:
                await client.sign_in(password=input('Password: '))

        me = await client.get_me()
        print(f'Logged in as: {me.username if me.username else me.first_name}')
        write_log(log_file_run, f'Logged in as: {me.username if me.username else me.first_name}\n')
        list_room_ids = await get_room_id(client)
        for chat_id in list_room_ids:
            print(f'Chat id: {chat_id}')
            write_log(log_file_run, f'Chat id: {chat_id}\n')

            # Xử lý ngoại lệ khi lấy entity
            try:
                chat = await get_channel_entity(client, chat_id)
            except Exception as e:
                print(f"Error getting channel entity for {chat_id}: {e}")
                write_log(log_file_error, f"Error getting channel entity for {chat_id}: {e}\n")
                continue  # Bỏ qua chat_id này và tiếp tục vòng lặp

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
                all_messages.extend(messages)  # Tối ưu hóa lưu trữ

                offset_id = messages[-1].id  # Lấy ID tin nhắn cuối cùng
                total_messages = len(all_messages)

                if total_count_limit and total_messages >= total_count_limit:
                    break

            if all_messages:
                for message in all_messages:
                    print('passed')
                    try:
                        if message.media and not isinstance(message.media, MessageMediaDocument):
                            await get_room_link_from_message(message)
                    except Exception as e:
                        print(f'Error downloading {e}')
                        write_log(log_file_error, f'Error: {str(e)}\n')
            else:
                print('No messages were retrieved')
                write_log(log_file_error, 'No messages were retrieved\n')


    except ChannelPrivateError:
        print('ERROR: This is a private channel.')
        write_log(log_file_error, 'Error: This is a private channel.\n')
    except ChannelInvalidError:
        print('ERROR: Invalid channel.')
        write_log(log_file_error, 'Error: Invalid channel.\n')
    except ValueError as e:
        print(f'ERROR: Invalid channel ID format: {str(e)}')
        write_log(log_file_error, f'Error: Invalid channel ID format: {str(e)}\n')
    except Exception as e:
        print(f'Unexpected error: {str(e)}')
        write_log(log_file_error, f'Error: {str(e)}\n')
    finally:
        await client.disconnect() 

async def main():
    await client.start()    # Bắt đầu đăng nhập
    await run('+84 345525359')

asyncio.run(main())
