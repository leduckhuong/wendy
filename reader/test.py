# reader.py
import redis

r = redis.Redis()
pubsub = r.pubsub()
pubsub.subscribe("file_channel")  # Đăng ký kênh

print("Đang lắng nghe thông báo từ 'file_channel'...")

for message in pubsub.listen():
    if message["type"] == "message":
        filename = message["data"].decode()
        print(f"📥 Nhận được tín hiệu file mới: {filename}")
      