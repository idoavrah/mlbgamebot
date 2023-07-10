import sync
import parse
import asyncio
import time

if __name__ == "__main__":

    sync.start()
    asyncio.run(parse.start())
    asyncio.run(parse.daily())
