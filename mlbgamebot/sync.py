from setup import fromdate, todate
import logging
import os
import requests
import json
import pandas as pd
from jsonpath_ng import jsonpath, parse

logger = logging.getLogger()

def schedule(year, month, day):

    filename = f'data/schedule/{year}/{year}-{month:02d}-{day:02d}.json'

    try:

        logger.info(f'Sync schedule day {year}-{month:02d}-{day:02d}')
        url = f'https://statsapi.mlb.com/api/v1/schedule?language=en&sportId=1&date={month:02d}/{day:02d}/{year}'
        req = requests.get(url)
        data = req.json()
        if any([match.value for match in parse('totalGames').find(data)]):
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as outfile:
                json.dump(data, outfile)

    except Exception as e:
        logging.error(e, exc_info=True)


def games(year, month, day):

    filename = f'data/schedule/{year}/{year}-{month:02d}-{day:02d}.json'
    
    if os.path.isfile(filename):
        try:
            with open(filename, 'r') as infile:
                data = json.loads(infile.read())
                games = data["dates"][0]["games"] if data.get("dates") else []

                for game in games:
                    if game["status"]['detailedState'] == 'Final':
                        gamepk = game["gamePk"]
                        filename = f'data/games/{year}/{gamepk}.json'
                        if not os.path.isfile(filename):
                            logger.info(f'Sync game {gamepk}')
                            url = f'https://statsapi.mlb.com/api/v1/game/{gamepk}/playByPlay'
                            req = requests.get(url)
                            data = req.json()
                            os.makedirs(os.path.dirname(
                                filename), exist_ok=True)
                            with open(filename, 'w') as outfile:
                                json.dump(data, outfile)
                                
        except Exception as e:
            logging.error(e, exc_info=True)


def start():
    logger.info('Start sync')

    global fromdate, todate

    try:

        for d in pd.date_range(fromdate, todate):
            schedule(d.year, d.month, d.day)
            games(d.year, d.month, d.day)

    except Exception as err:
        logger.error(err)

    logger.info('Done sync')


logger.info('Loaded sync')


if __name__ == "__main__":
    start()
