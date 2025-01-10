// Kết nối với API Telegram: TelegramClient

from telethon import TelegramClient

api_id = 'your_api_id'
api_hash = 'your_api_hash'

client = TelegramClient('session_name', api_id, api_hash)

===============
// Đăng nhập

await client.start()

===============
// Nhận tin nhắn

messages = await client.get_messages('username_or_chat_id', limit=10)
for message in messages:
    print(message.text)

===============
// Lắng nghe sự kiện

from telethon import events

@client.on(events.NewMessage(pattern='(?i)hello'))
async def handler(event):
    await event.reply('Hi there!')

===============
// Tải lên và tải xuống tệp

await client.send_file('username_or_chat_id', 'path/to/file.jpg')

await client.download_media(message, 'path/to/save')

await client.add_participant('group_username', 'user_username')

==============
// Chạy bất đồng bộ
with client:
    client.run_until_disconnected()


