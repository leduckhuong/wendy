import asyncio

from telegram_listener import client

async def main():
    await client.start()    # Bắt đầu đăng nhập
    
    await client.run_until_disconnected()   # Lắng nghe liên tục từ telegram

asyncio.run(main())