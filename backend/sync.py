from setup import fromdate, todate
import logging
import os
import json
import pandas as pd
from jsonpath_ng import jsonpath, parse
import aiohttp
import asyncio
import backoff

logger = logging.getLogger()

@backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=5)
async def fetch_json(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

async def schedule(session, sem, year, month, day):
    filename = f'../data/schedule/{year}/{year}-{month:02d}-{day:02d}.json'

    # Check for existing logic if we want to skip existing? 
    # Original code fetched always. We'll stick to that.
    
    async with sem:
        logger.info(f'Sync schedule day {year}-{month:02d}-{day:02d}')
        url = f'https://statsapi.mlb.com/api/v1/schedule?language=en&sportId=1&date={month:02d}/{day:02d}/{year}'
        try:
            data = await fetch_json(session, url)
            if any([match.value for match in parse('totalGames').find(data)]):
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, 'w') as outfile:
                    json.dump(data, outfile)
        except Exception as e:
            logging.error(f"Error syncing schedule {year}-{month}-{day}: {e}", exc_info=True)

async def sync_game(session, sem, year, gamepk):
    filename = f'../data/games/{year}/{gamepk}.json'
    if not os.path.isfile(filename):
        async with sem:
            logger.info(f'Sync game {gamepk}')
            url = f'https://statsapi.mlb.com/api/v1/game/{gamepk}/playByPlay'
            try:
                data = await fetch_json(session, url)
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, 'w') as outfile:
                    json.dump(data, outfile)
            except Exception as e:
                logging.error(f"Error syncing game {gamepk}: {e}", exc_info=True)

async def games(session, sem, year, month, day):
    filename = f'../data/schedule/{year}/{year}-{month:02d}-{day:02d}.json'
    
    if os.path.isfile(filename):
        try:
            with open(filename, 'r') as infile:
                data = json.loads(infile.read())
            
            games_list = data["dates"][0]["games"] if data.get("dates") else []
            tasks = []
            
            for game in games_list:
                if game["status"]['detailedState'] == 'Final':
                    gamepk = game["gamePk"]
                    tasks.append(sync_game(session, sem, year, gamepk))
            
            if tasks:
                await asyncio.gather(*tasks)
                
        except Exception as e:
            logging.error(e, exc_info=True)

async def process_day(session, sem, year, month, day):
    await schedule(session, sem, year, month, day)
    await games(session, sem, year, month, day)

async def start():
    logger.info('Start sync (Async)')
    global fromdate, todate

    sem = asyncio.Semaphore(5) # Concurrency limit

    async with aiohttp.ClientSession() as session:
        tasks = []
        for d in pd.date_range(fromdate, todate):
            tasks.append(process_day(session, sem, d.year, d.month, d.day))
            
        await asyncio.gather(*tasks)

    logger.info('Done sync')

logger.info('Loaded sync')

if __name__ == "__main__":
    asyncio.run(start())
