import os
import asyncio
import signal
import configparser
from datetime import datetime, timedelta
import redis.asyncio as redis # type: ignore
from telethon import TelegramClient, events # type: ignore
from telethon.tl.types import MessageMediaDocument # type: ignore
from asyncio import Semaphore, sleep
from typing import Dict, Optional

from utils import (
    check_file_in_history,
    download_file_from_media,
    write_log,
    get_data_from_text
)

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# API Configurations
API_CONFIGS = [
    {
        "id": 1,
        "api_id": config['TELE_API_1']['APP_ID'],
        "api_hash": config['TELE_API_1']['HASH_ID'],
        "phone": config['TELE_API_1']['PHONE'],
        "username": config['TELE_API_1']['USERNAME']
    },
    {
        "id": 2,
        "api_id": config['TELE_API_2']['APP_ID'],
        "api_hash": config['TELE_API_2']['HASH_ID'],
        "phone": config['TELE_API_2']['PHONE'],
        "username": config['TELE_API_2']['USERNAME']
    }
]

# Logging configuration
log_file_run = config['LOGGING']['LOG_FILE_RUN']
log_file_error = config['LOGGING']['LOG_FILE_ERROR']

# Session directory
session_dir = config['SESSION']['SESSION_DIR']
os.makedirs(session_dir, exist_ok=True)

# Storage directory
storage_dir = config['STORAGE']['STORAGE_DIR']
os.makedirs(storage_dir, exist_ok=True)

# History file
history_downloaded = config['HISTORY']['HISTORY_DOWNLOADED_FILE']

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_pool = redis.ConnectionPool.from_url(REDIS_URL, max_connections=10, decode_responses=True)

# Rate limiting
RATE_LIMIT_SEMAPHORE = Semaphore(5)  # Max 5 concurrent downloads
DOWNLOAD_DELAY = 2  # seconds between downloads

# Global state
shutdown_event = asyncio.Event()
clients: Dict[int, TelegramClient] = {}
active_clients = set()

async def get_redis_client() -> redis.Redis:
    """Get Redis client from connection pool"""
    return redis.Redis(connection_pool=redis_pool)

async def publish_to_redis(channel: str, message: str) -> bool:
    """Publish message to Redis channel with error handling"""
    try:
        r = await get_redis_client()
        await r.publish(channel, message)
        await r.aclose()
        return True
    except Exception as e:
        print(f'Error publishing to Redis: {e}')
        write_log(log_file_error, f'Redis publish error: {e}\n')
        return False

async def handle_new_message(event, client_id: int, client: TelegramClient):
    """Enhanced message handler with rate limiting and error handling"""
    try:
        message = event.message
        client_name = f"client_{client_id}"

        if isinstance(message.media, MessageMediaDocument):
            # Rate limiting for downloads
            async with RATE_LIMIT_SEMAPHORE:
                file_size = message.media.document.size
                file_name = message.media.document.attributes[0].file_name

                if not check_file_in_history(file_size, file_name):
                    print(f'{client_name}: Downloading {file_name} ({file_size} bytes)')
                    write_log(log_file_run, f'{client_name}: Downloading {file_name}\n')

                    file_path = await download_file_from_media(client, message)
                    if file_path:
                        # Publish to Redis with retry
                        success = await publish_to_redis("file_channel", file_path)
                        if success:
                            print(f'{client_name}: Published {file_path} to Redis')
                        else:
                            print(f'{client_name}: Failed to publish {file_path}')
                    else:
                        print(f'{client_name}: Failed to download {file_name}')
                else:
                    print(f'{client_name}: File already processed {file_name}')

                # Rate limiting delay
                await sleep(DOWNLOAD_DELAY)

        else:
            # Process text messages
            if message.message:
                get_data_from_text(message.message)
                print(f'{client_name}: Processed text message')

    except Exception as e:
        client_name = f"client_{client_id}"
        error_msg = f'Error in {client_name} handler: {str(e)}'
        print(error_msg)
        write_log(log_file_error, f'{error_msg}\n')

# Create event handlers for each client
def create_event_handler(client_id: int):
    """Factory function to create unique event handlers"""
    async def handler(event):
        client = clients[client_id]
        await handle_new_message(event, client_id, client)
    return handler

async def initialize_clients():
    """Initialize and register all Telegram clients"""
    for api_config in API_CONFIGS:
        client_id = api_config["id"]
        session_file = f'{session_dir}/{api_config["username"]}'

        client = TelegramClient(
            session_file,
            api_config['api_id'],
            api_config['api_hash']
        )

        clients[client_id] = client

        # Register unique event handler for this client
        client.add_event_handler(
            create_event_handler(client_id),
            events.NewMessage
        )

        print(f'Initialized client {client_id} ({api_config["username"]})')

async def start_client(client_id: int) -> bool:
    """Start a single client with error handling"""
    client = clients[client_id]
    api_config = API_CONFIGS[client_id - 1]

    try:
        print(f'Starting client {client_id} ({api_config["username"]})')
        write_log(log_file_run, f'Starting client {client_id}\n')

        await client.start(phone=api_config['phone'])
        active_clients.add(client_id)

        print(f'Client {client_id} connected successfully')
        write_log(log_file_run, f'Client {client_id} connected\n')

        return True

    except Exception as e:
        error_msg = f'Failed to start client {client_id}: {e}'
        print(error_msg)
        write_log(log_file_error, f'{error_msg}\n')
        return False

async def monitor_client_health():
    """Monitor client health and restart failed clients"""
    while not shutdown_event.is_set():
        try:
            for client_id, client in clients.items():
                if client_id not in active_clients or not client.is_connected:
                    print(f'Client {client_id} is not connected, attempting restart...')
                    # Remove from active clients
                    active_clients.discard(client_id)

                    # Try to restart
                    success = await start_client(client_id)
                    if success:
                        print(f'Successfully restarted client {client_id}')
                    else:
                        print(f'Failed to restart client {client_id}')

            await sleep(30)  # Check every 30 seconds

        except Exception as e:
            print(f'Error in health monitor: {e}')
            write_log(log_file_error, f'Health monitor error: {e}\n')
            await sleep(10)

async def shutdown_handler():
    """Handle graceful shutdown"""
    def signal_handler(signum, frame):
        print(f'Received signal {signum}, initiating graceful shutdown...')
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Wait for shutdown signal
    await shutdown_event.wait()

    print('Shutting down clients...')
    for client_id, client in clients.items():
        try:
            if client.is_connected:
                await client.disconnect()
                print(f'Disconnected client {client_id}')
        except Exception as e:
            print(f'Error disconnecting client {client_id}: {e}')

async def start():
    """Main entry point - start all clients concurrently"""
    try:
        print('Initializing Telegram Listener...')
        await initialize_clients()

        # Start shutdown handler
        shutdown_task = asyncio.create_task(shutdown_handler())

        # Start health monitor
        health_task = asyncio.create_task(monitor_client_health())

        # Start all clients concurrently
        client_tasks = []
        for client_id in clients.keys():
            task = asyncio.create_task(start_client(client_id))
            client_tasks.append(task)

        # Wait for all clients to start
        await asyncio.gather(*client_tasks, return_exceptions=True)

        print('All clients started. Running indefinitely...')

        # Keep running until shutdown
        await shutdown_event.wait()

        # Cancel background tasks
        health_task.cancel()
        shutdown_task.cancel()

        try:
            await health_task
            await shutdown_task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        error_msg = f'Critical error in main: {e}'
        print(error_msg)
        write_log(log_file_error, f'{error_msg}\n')
        raise

if __name__ == "__main__":
    asyncio.run(start())