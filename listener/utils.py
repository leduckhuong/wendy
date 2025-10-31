import os
import configparser
from telethon import TelegramClient
from shared_utils import (
    check_file_in_history,
    append_line_to_file,
    progress_callback,
    write_log
)

config = configparser.ConfigParser()
config.read('config.ini')

history_downloaded = config['HISTORY']['HISTORY_DOWNLOADED_FILE']
storage_dir = config['STORAGE']['STORAGE_DIR']
log_file_run = config['LOGGING']['LOG_FILE_RUN']
log_file_error = config['LOGGING']['LOG_FILE_ERROR']

# Listener-specific functions

async def download_file_from_media(client: TelegramClient, message) -> str:
    """Download file from Telegram media message"""
    try:
        size = message.media.document.size
        file_name_tmp = message.media.document.attributes[0].file_name
        file_name = str(size) + '-' + file_name_tmp
        download_path = os.path.join(storage_dir, file_name)

        # Download file from message
        file_path = await client.download_media(
            message.media,
            file=download_path,
            progress_callback=progress_callback
        )

        if file_path is not None:
            append_line_to_file(history_downloaded, file_path)

        return file_path

    except Exception as e:
        error_msg = f'Error during download: {str(e)}'
        print(error_msg)
        write_log(log_file_error, f'{error_msg}\n')
        return None
    

