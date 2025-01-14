import os
import configparser
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, ChannelPrivateError, ChannelInvalidError
from telethon.tl.functions.messages import GetHistoryRequest

from utils import get_channel_entity, get_dict_from_message, check_file_in_history, download_file_from_media, read_file, get_room_link_from_message


# Reading Configs
config = configparser.ConfigParser()
config.read('config.ini')

# Thông tin đăng nhập Telegram của bạn
api_id = config['TELE_API']['APP_ID']
api_hash = config['TELE_API']['HASH_ID']
phone = config['TELE_API']['PHONE']
username = config['TELE_API']['USERNAME']

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
        
        user_input_channel = input('enter entity(telegram URL or entity id):')
        
        # Get the channel entity
        my_channel = await get_channel_entity(client, user_input_channel)
        print(f'Successfully connected to channel: {getattr(my_channel, 'title', 'Unknown')}')
        
        offset_id = 0
        limit = 100
        all_messages = []
        total_messages = 0
        total_count_limit = 0

        while True:
            history = await client(GetHistoryRequest(
                peer=my_channel,
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

                chat_id = None

                if hasattr(message.peer_id, 'user_id'):
                    chat_id = message.peer_id.user_id
                elif hasattr(message.peer_id, 'chat_id'):
                    chat_id = message.peer_id.chat_id
                elif hasattr(message.peer_id, 'channel_id'):
                    chat_id = message.peer_id.channel_id
                    
                msg_dict = await get_dict_from_message(chat_id, message)
                if msg_dict is not None and (msg_dict['type'] == 'download' or msg_dict['type'] == 'link'):
                    all_messages.append(msg_dict)
            
            offset_id = messages[len(messages) - 1].id
            total_messages = len(all_messages)
            
            if total_count_limit != 0 and total_messages >= total_count_limit:
                break

        print(f'Total messages retrieved: {total_messages}')
        
        if all_messages:
            for message in all_messages:
                # Kiểm tra và lấy tên file
                try:
                    if message is not None and message['type'] == 'download':
                        file_name = message['file_name']
                        if not check_file_in_history(history_downloaded, file_name):
                            chat_id = None
                            if 'user_id' in message['peer_id']:
                                chat_id = message['peer_id']['user_id']
                            elif 'chat_id' in message['peer_id']:
                                chat_id = message['peer_id']['chat_id']
                            elif 'channel_id' in message['peer_id']:
                                chat_id = message['peer_id']['channel_id']
                            # attributes = message['media']['document'].get('attributes', [])
                            file_path = await download_file_from_media(client, chat_id, message, download_dir)
        
                            # print(f"Successfully downloaded: {file_path}")
                            # Thêm độ trễ 1 giây giữa mỗi lần tải file
                            await asyncio.sleep(1)

                            if file_path:
                                file_name = await read_file(chat_id ,file_path)
                                # if file_name:
                                #     # Đánh dấu đã đọc
                                #     append_line_to_file(history_read, file_name)
                                # print(f"Successfully read: {file_path}")
                            else:
                                print("Download failed")# Tải file về
                    if message is not None and message['type'] == 'link':
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
