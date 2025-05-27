import redis
import time

r = redis.Redis()

def download_file(filename):
    print(f"Downloading {filename}...")
    time.sleep(2)  # Giả lập download
    with open(f"./{filename}", "w") as f:
        f.write("This is the file content")
    print(f"Downloaded {filename}")
    r.publish("file_channel", filename)

download_file("requirements.txt")
