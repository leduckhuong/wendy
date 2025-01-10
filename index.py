from telethon import TelegramClient, events

api_id = 29117059
api_hash = '9ec5fb255a295e7a8bf507c9a7922efe'
session_name = '@mrhellomeo'

client = TelegramClient(session_name, api_id, api_hash)

async def main():
    await client.start()
    print('Connected succesfull')
    await client.disconnect()

client.loop.run_until_complete(main)
