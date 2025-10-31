import os
import sys
import asyncio
import signal
import configparser
import redis.asyncio as redis  # type: ignore
from typing import Optional
from asyncio import Semaphore, sleep

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import (
    read_file,
    remove_file,
    write_log
)

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Logging configuration
log_file_run = config['LOGGING']['LOG_FILE_RUN']
log_file_error = config['LOGGING']['LOG_FILE_ERROR']

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_pool = redis.ConnectionPool.from_url(REDIS_URL, max_connections=5, decode_responses=True)

# Processing configuration
MAX_CONCURRENT_PROCESSING = int(os.getenv('MAX_CONCURRENT_PROCESSING', '3'))
PROCESSING_SEMAPHORE = Semaphore(MAX_CONCURRENT_PROCESSING)

# Global state
shutdown_event = asyncio.Event()
processing_stats = {
    'files_processed': 0,
    'errors': 0,
    'start_time': None
}

async def get_redis_client() -> redis.Redis:
    """Get Redis client from connection pool"""
    return redis.Redis(connection_pool=redis_pool)

async def subscribe_to_channel(channel: str) -> Optional[redis.Redis]:
    """Subscribe to Redis channel with error handling"""
    try:
        r = await get_redis_client()
        pubsub = r.pubsub()
        await pubsub.subscribe(channel)
        print(f'Successfully subscribed to channel: {channel}')
        return pubsub
    except Exception as e:
        print(f'Failed to subscribe to channel {channel}: {e}')
        write_log(log_file_error, f'Redis subscription error: {e}\n')
        return None

async def process_file_message(file_path: str):
    """Process a single file message with rate limiting"""
    async with PROCESSING_SEMAPHORE:
        try:
            print(f"Processing file: {file_path}")

            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return

            # Process the file
            result = await read_file(file_path)
            if result:
                # Remove processed file
                remove_file(file_path)
                processing_stats['files_processed'] += 1
                print(f"Successfully processed: {file_path}")
                write_log(log_file_run, f'Processed file: {file_path}\n')
            else:
                processing_stats['errors'] += 1
                print(f"Failed to process: {file_path}")
                write_log(log_file_error, f'Failed to process file: {file_path}\n')

        except Exception as e:
            processing_stats['errors'] += 1
            error_msg = f'Error processing file {file_path}: {e}'
            print(error_msg)
            write_log(log_file_error, f'{error_msg}\n')

async def listen_for_messages():
    """Async message listener with reconnection logic"""
    channel = "file_channel"
    max_retries = 5
    retry_delay = 5

    while not shutdown_event.is_set():
        pubsub = None
        try:
            print("Attempting to connect to Redis...")
            pubsub = await subscribe_to_channel(channel)

            if not pubsub:
                await sleep(retry_delay)
                continue

            print("Reader started, listening for new file signals...")

            # Listen for messages asynchronously
            while not shutdown_event.is_set():
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

                    if message and message["type"] == "message":
                        file_path = message["data"]
                        print(f"Received file signal: {file_path}")

                        # Process file asynchronously
                        asyncio.create_task(process_file_message(file_path))

                except Exception as e:
                    print(f'Error receiving message: {e}')
                    break

        except Exception as e:
            print(f'Redis connection error: {e}')
            write_log(log_file_error, f'Redis connection error: {e}\n')

        finally:
            if pubsub:
                try:
                    await pubsub.unsubscribe()
                    await pubsub.aclose()
                except Exception as e:
                    print(f'Error closing pubsub: {e}')

            if not shutdown_event.is_set():
                print(f'Retrying connection in {retry_delay} seconds...')
                await sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # Exponential backoff, max 60s

async def print_stats():
    """Print processing statistics periodically"""
    while not shutdown_event.is_set():
        await sleep(60)  # Print stats every minute
        if processing_stats['files_processed'] > 0 or processing_stats['errors'] > 0:
            print(f"Stats - Processed: {processing_stats['files_processed']}, Errors: {processing_stats['errors']}")

async def shutdown_handler():
    """Handle graceful shutdown"""
    def signal_handler(signum, frame):
        print(f'Received signal {signum}, initiating graceful shutdown...')
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await shutdown_event.wait()
    print('Reader shutdown complete.')

async def start():
    """Main entry point"""
    try:
        processing_stats['start_time'] = asyncio.get_event_loop().time()

        print('Starting Telegram Reader...')

        # Start shutdown handler
        shutdown_task = asyncio.create_task(shutdown_handler())

        # Start stats printer
        stats_task = asyncio.create_task(print_stats())

        # Start message listener
        listener_task = asyncio.create_task(listen_for_messages())

        # Wait for shutdown
        await shutdown_event.wait()

        # Cancel background tasks
        listener_task.cancel()
        stats_task.cancel()
        shutdown_task.cancel()

        try:
            await listener_task
            await stats_task
            await shutdown_task
        except asyncio.CancelledError:
            pass

        # Final stats
        print(f"Final stats - Processed: {processing_stats['files_processed']}, Errors: {processing_stats['errors']}")

    except Exception as e:
        error_msg = f'Critical error in reader: {e}'
        print(error_msg)
        write_log(log_file_error, f'{error_msg}\n')
        raise

if __name__ == "__main__":
    asyncio.run(start())

