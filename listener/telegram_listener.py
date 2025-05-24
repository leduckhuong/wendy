import os
import asyncio
import configparser
from telethon import TelegramClient, events # type: ignore
from telethon.tl.types import MessageMediaDocument # type: ignore

from utils import ( 
    write_log,
    get_file_hash_before_download, 
    check_file_in_history, 
    download_file_from_media, 
    read_file, 
    get_room_link_from_message
)

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

history_read = config['HISTORY']['HISTORY_FILE']
history_downloaded = config['HISTORY']['HISTORY_DOWNLOADED_FILE']

async def handle_newMessage_Client(event, client):
    try:
        message = event.message
        # if message is file
        if isinstance(message.media, MessageMediaDocument):
            file_hash = await get_file_hash_before_download(client, message)
            if file_hash is None:
                return 
            if check_file_in_history(history_downloaded, file_hash):
                return
            file_path = await download_file_from_media(client, message, storage_dir, file_hash)
            # add delay 1 second between each file download
            await asyncio.sleep(1)
            if file_path:
                await read_file(file_path)
                
        else:
            await get_room_link_from_message(message)
                
    except Exception as e:
        print(f'Error in event handler: {str(e)} (telegram_listener.py:handle_newMessage:73)')
        write_log(log_file_error, f'Error: {str(e)} (telegram_listener.py:handle_newMessage:74)\n')

@client1.on(events.NewMessage)
async def handle_newMessage(event):
    await handle_newMessage_Client(event, client1)
    
@client2.on(events.NewMessage)
async def handle_newMessage(event):
    await handle_newMessage_Client(event, client2)

