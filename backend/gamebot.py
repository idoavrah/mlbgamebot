import sync
import parse
import asyncio
import time

async def main():
    await sync.start()
    await parse.start()

if __name__ == "__main__":
    asyncio.run(main())
