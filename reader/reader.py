import os
import sys
import configparser
import redis  # type: ignore

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import (
    read_file,
    remove_file
)

config = configparser.ConfigParser()


r = redis.Redis()
pubsub = r.pubsub()
pubsub.subscribe("file_channel")

async def start():
    print("Reader started, listening for new file signals...")
    for message in pubsub.listen():
        if message["type"] == "message":
            file_path = message["data"].decode()
            print(f"Get a new file signals: {file_path}")
            if os.path.exists(file_path):
                await read_file(file_path)
                remove_file(file_path)
            else:
                continue

