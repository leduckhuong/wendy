import asyncio
from datetime import datetime
from telegram_listener import client1, client2

from utils import write_log

log_file_run = './logs/run.log'
log_file_error = './logs/error.log'

def base_time():
    now = datetime.now()
    return 1 if now.minute < 30 else 2


async def monitor_timeout(client, timeout_seconds):
    '''Ngắt kết nối sau một khoảng thời gian.'''
    try:
        await asyncio.sleep(timeout_seconds)
        if client.is_connected:
            print('Timeout reached. Disconnecting client.  (index.py:monitor_timeout:20)')
            write_log(log_file_run, 'Timeout reached. Disconnecting client (index.py:monitor_timeout:21)\n')
            await client.disconnect()
    except Exception as e:
        print(f'Error in monitor_timeout: {str(e)} (index.py:monitor_timeout:24)')
        write_log(log_file_error, f'Error: {str(e)} (index.py:monitor_timeout:25)\n')

async def start_client_with_timeout(client, client_name, timeout_seconds):
    '''Chạy client và tự động ngắt kết nối sau timeout.'''
    try:
        await client.start()
        print(f'Starting server {client_name} (index.py:start_client_with_timeout:31)')
        write_log(log_file_run, f'Starting server {client_name}  (index.py:start_client_with_timeout:32)\n')
        timeout_task = asyncio.create_task(monitor_timeout(client, timeout_seconds))
        await client.run_until_disconnected()
        await timeout_task  # Đảm bảo task timeout hoàn thành
    except Exception as e:
        print(f'Error in {client_name}: {e}  (index.py:start_client_with_timeout:37)')
        write_log(log_file_error, f'Error: {str(e)}  (index.py:start_client_with_timeout:38)\n')
    finally:
        if client.is_connected:
            await client.disconnect()
        print(f'Disconnected {client_name}  (index.py:start_client_with_timeout:42)')
        write_log(log_file_run, f'Disconnected {client_name}  (index.py:start_client_with_timeout:43)\n')


async def main():
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
            print(f'Error in main loop: {e} (index.py:main:57)')
            write_log(log_file_error, f'Error: {str(e)} (index.py:main:57)\n')
        await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
