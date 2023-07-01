import sync
import parse
import asyncio

if __name__ == "__main__":

    sync.start()
    asyncio.run(parse.start())
    asyncio.run(parse.daily())
