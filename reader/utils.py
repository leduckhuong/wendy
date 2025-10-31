import os
import configparser
import redis.asyncio as redis
from shared_utils import (
    read_file_txt,
    remove_file,
    extract_file,
    write_log
)

config = configparser.ConfigParser()
config.read('config.ini')

extract_dir = config['EXTRACT']['EXTRACT_DIR']

# Reader-specific functions

async def read_file(file_path: str):
    """Process file based on extension"""
    try:
        _, file_extension = os.path.splitext(file_path)
        if file_extension == '.txt':
            return await read_file_txt(file_path)
        elif file_extension in ['.rar', '.zip', '.7z']:
            return await extract_and_publish(file_path, file_extension)
        else:
            print(f'Unsupported file type: {file_extension}')
            return None
    except Exception as e:
        error_msg = f'Error reading file: {str(e)}'
        print(error_msg)
        return None

async def extract_and_publish(file_path: str, extension: str):
    """Extract archive and publish extracted files to Redis"""
    try:
        # Extract the file
        result = extract_file(file_path, extension)
        if result:
            # Import here to avoid circular imports
            import redis.asyncio as redis
            from shared_utils import flatten_extracted_files

            # Get Redis client
            REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
            r = redis.Redis.from_url(REDIS_URL)

            # Get extracted files and publish to Redis
            extract_file_tmp = flatten_extracted_files(extract_dir)
            for extracted_file in extract_file_tmp:
                try:
                    await r.publish("file_channel", extracted_file)
                    print(f'Published extracted file to Redis: {extracted_file}')
                except Exception as e:
                    print(f'Error publishing extracted file {extracted_file}: {e}')

            await r.aclose()
            return file_path
        else:
            return None

    except Exception as e:
        error_msg = f'Error extracting and publishing file: {str(e)}'
        print(error_msg)
        return None
