import sync
import parse
import asyncio
import time

if __name__ == "__main__":

    while True:
        sync.start()
        asyncio.run(parse.start())
        asyncio.run(parse.daily())
        time.sleep(60)
