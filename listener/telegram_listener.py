import os
import asyncio
import configparser
from datetime import datetime
from telethon import TelegramClient, events # type: ignore
from telethon.tl.types import MessageMediaDocument # type: ignore

from utils import ( 
    get_file_hash_before_download, 
    check_file_in_history, 
    download_file_from_media,
    get_room_link_from_message
)

from libs import write_log

config = configparser.ConfigParser()
config.read('config.ini')

API_1 = {
    "id": 1,
    "api_id": config['TELE_API_1']['APP_ID'],
    "api_hash": config['TELE_API_1']['HASH_ID'],
    "phone": config['TELE_API_1']['PHONE'],
    "username": config['TELE_API_1']['USERNAME']
}

API_2 = {
    "id": 2,
    "api_id": config['TELE_API_2']['APP_ID'],
    "api_hash": config['TELE_API_2']['HASH_ID'],
    "phone": config['TELE_API_2']['PHONE'],
    "username": config['TELE_API_2']['USERNAME']
}

log_file_run = config['LOGGING']['LOG_FILE_RUN']
log_file_error = config['LOGGING']['LOG_FILE_ERROR']

session_dir = config['SESSION']['SESSION_DIR']
os.makedirs(session_dir, exist_ok=True)

session_file1 = f'{session_dir}/{API_1["username"]}'
client1 = TelegramClient(session_file1, API_1['api_id'], API_1['api_hash'])

session_file2 = f'{session_dir}/{API_2["username"]}'
client2 = TelegramClient(session_file2, API_2['api_id'], API_2['api_hash'])

storage_dir = config['STORAGE']['STORAGE_DIR']
os.makedirs(storage_dir, exist_ok=True)

history_downloaded = config['HISTORY']['HISTORY_DOWNLOADED_FILE']

async def handle_newMessage_Client(event, client):
    try:
        message = event.message
        print('Has received a new message.  (telegram_listener.py:handle_newMessage_Client:57)')
        # if message is file
        if isinstance(message.media, MessageMediaDocument):
            file_hash = await get_file_hash_before_download(client, message)
            if file_hash is None:
                return 
            if check_file_in_history(history_downloaded, file_hash):
                return
            await download_file_from_media(client, message, storage_dir, file_hash)
            # add delay 1 second between each file download
            await asyncio.sleep(1)

        else:
            await get_room_link_from_message(message)
                
    except Exception as e:
        print(f'Error in event handler: {str(e)} (telegram_listener.py:handle_newMessage:73)')
        write_log(log_file_error, f'Error: {str(e)} (telegram_listener.py:handle_newMessage:74)\n')

@client1.on(events.NewMessage)
async def handle_newMessage(event):
    print('Start at client 1.  (telegram_listener.py:handle_newMessage:79)')
    write_log(log_file_run, 'Start at client 1 (telegram_listener.py:handle_newMessage:80)\n')
    await handle_newMessage_Client(event, client1)
    
@client2.on(events.NewMessage)
async def handle_newMessage(event):
    print('Start at client 2.  (telegram_listener.py:handle_newMessage:85)')
    write_log(log_file_run, 'Start at client 2 (telegram_listener.py:handle_newMessage:86)\n')
    await handle_newMessage_Client(event, client2)

def base_time():
    now = datetime.now()
    return 1 if now.minute < 30 else 2


async def monitor_timeout(client, timeout_seconds):
    try:
        await asyncio.sleep(timeout_seconds)
        if client.is_connected:
            print('Timeout reached. Disconnecting client.  (telegram_listener.py:monitor_timeout:94)')
            write_log(log_file_run, 'Timeout reached. Disconnecting client (telegram_listener.py:monitor_timeout:95)\n')
            await client.disconnect()
    except Exception as e:
        print(f'Error in monitor_timeout: {str(e)} (telegram_listener.py:monitor_timeout:102)')
        write_log(log_file_error, f'Error: {str(e)} (telegram_listener.py:monitor_timeout:103)\n')

async def start_client_with_timeout(client, client_name, timeout_seconds):
    try:
        print(f'Starting server {client_name} (telegram_listener.py:start_client_with_timeout:108)')
        write_log(log_file_run, f'Starting server {client_name}  (telegram_listener.py:start_client_with_timeout:109)\n')
        await client.start()
        timeout_task = asyncio.create_task(monitor_timeout(client, timeout_seconds))
        await client.run_until_disconnected()
        await timeout_task  # Đảm bảo task timeout hoàn thành
    except Exception as e:
        print(f'Error in {client_name}: {e}  (telegram_listener.py:start_client_with_timeout:114)')
        write_log(log_file_error, f'Error: {str(e)}  (telegram_listener.py:start_client_with_timeout:115)\n')
    finally:
        if client.is_connected:
            await client.disconnect()
        print(f'Disconnected {client_name}  (telegram_listener.py:start_client_with_timeout:119)')
        write_log(log_file_run, f'Disconnected {client_name}  (telegram_listener.py:start_client_with_timeout:120)\n')

async def start():
    timeout_seconds = 60*30  # Ngắt sau 30 phút
    while True:
        try:
            if base_time() == 1:
                await client2.disconnect()  # Đảm bảo client2 đã ngắt
                await start_client_with_timeout(client1, 'client1', timeout_seconds)
            else:
                await client1.disconnect()  # Đảm bảo client1 đã ngắt
                await start_client_with_timeout(client2, 'client2', timeout_seconds)
        except Exception as e:
            print(f'Error in main loop: {e} (telegram_listener.py:start:133)')
            write_log(log_file_error, f'Error: {str(e)} (telegram_listener.py:start:134)\n')
        await asyncio.sleep(1)