import asyncio
from reader import start

async def main():
    try:
        await start()
    except Exception as e:
        print(f'Error: {str(e)} (index.py:main:15)')


if __name__ == '__main__':
    asyncio.run(main())
