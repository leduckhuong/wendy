import asyncio
import configparser
from telegram_listener import start

from utils import write_log

config = configparser.ConfigParser()
config.read('config.ini')

log_file_run = config['LOGGING']['LOG_FILE_RUN']
log_file_error = config['LOGGING']['LOG_FILE_ERROR']


async def main():
    try:
        await start()
    except Exception as e:
        write_log(log_file_error, f'Error: {str(e)} (index.py:main:19)\n')
    else:
        write_log(log_file_run, f'Listener started(index.py:main:21)\n')


if __name__ == '__main__':
    asyncio.run(main())
