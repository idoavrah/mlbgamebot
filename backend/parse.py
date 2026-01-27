from email.utils import parsedate
from unittest.result import failfast
from numpy import sign
from setup import fromdate, todate
from jsonpath_ng import jsonpath, parse
from pytz import timezone
import datetime
import evaluate
import logging
import glob
import os
import json
import asyncio
import pandas as pd
import feather as ftr
import pyarrow.feather as feather

logger = logging.getLogger()


async def start():

    logger.info("Start parse")

    GAME_COLUMNS = ['season', 'seriesDescription', 'officialDate', 'awayTeam', 'homeTeam', 'awayFinalScore', 'homeFinalScore', 'gamePk',
                    'eventNum', 'inning', 'half', 'atbat', 'balls', 'strikes', 'outs', 'pitches', 'awayScore', 'homeScore', 'event', 'result', 'venue', 'gameDescription']

    global fromdate, todate

    filename = ''

    for d in pd.date_range(fromdate, todate):

        year, month, day = d.year, d.month, d.day

        try:

            filename = f'../data/schedule/{year}/{year}-{month:02d}-{day:02d}.json'
            if not os.path.isfile(filename):
                continue

            with open(filename, 'r') as scheduleFile:
                data = json.load(scheduleFile)
                games = [match.value for match in parse(
                    'dates[*].games').find(data)][0]
                for game in games:
                    gamepk = game["gamePk"]

                    filename = f'../data/games/{year}/{gamepk}.json'
                    if not os.path.isfile(filename):
                        continue

                    with open(filename, 'r') as gameFile:
                        data = json.load(gameFile)

                        atbats = [match.value for match in parse(
                            'allPlays[*]').find(data)]

                        eventNum = 0
                        eventsList = []
                        for atbat in atbats:
                            for play in atbat["playEvents"]:
                                if not play["details"].get("event"):
                                    continue

                                eventsList.append([game["season"],
                                                   game["seriesDescription"],
                                                   game["officialDate"],
                                                   game["teams"]["away"]["team"]["name"],
                                                   game["teams"]["home"]["team"]["name"],
                                                   game["teams"]["away"]["score"],
                                                   game["teams"]["home"]["score"],
                                                   gamepk,
                                                   eventNum,
                                                   atbat["about"]["inning"],
                                                   atbat["about"]["halfInning"],
                                                   None,
                                                   play["count"]["balls"],
                                                   play["count"]["strikes"],
                                                   play["count"]["outs"],
                                                   None,
                                                   play["details"]["awayScore"],
                                                   play["details"]["homeScore"],
                                                   play["details"]["event"],
                                                   play["details"]["description"],
                                                   game.get("venue", {}).get("name"),
                                                   game.get("description")])

                                eventNum += 1

                            eventsList.append([game["season"],
                                               game["seriesDescription"],
                                               game["officialDate"],
                                               game["teams"]["away"]["team"]["name"],
                                               game["teams"]["home"]["team"]["name"],
                                               game["teams"]["away"]["score"],
                                               game["teams"]["home"]["score"],
                                               gamepk,
                                               eventNum,
                                               atbat["about"]["inning"],
                                               atbat["about"]["halfInning"],
                                               atbat["about"]["atBatIndex"],
                                               atbat["count"]["balls"],
                                               atbat["count"]["strikes"],
                                               atbat["count"]["outs"],
                                               len(atbat["pitchIndex"]),
                                               atbat["result"]["awayScore"],
                                               atbat["result"]["homeScore"],
                                               atbat["result"]["event"],
                                               atbat["result"]["description"],
                                               game.get("venue", {}).get("name"),
                                               game.get("description")])

                            eventNum += 1

                        scores, superlatives = evaluate.start(eventsList)

                        gameDF = pd.DataFrame(eventsList, columns=GAME_COLUMNS)
                        gameDF['defenseScore'] = scores[0]
                        gameDF['offenseScore'] = scores[1]
                        gameDF['thrillScore'] = scores[2]
                        gameDF['superlatives'] = superlatives

                        gamedate = datetime.date(year, month, day)

                        # Output to data folder, grouped by year
                        # ../data/{year}/{filename}
                        
                        target_dir = f'../data/{year}'
                        filename = f'{target_dir}/{year}-{month:02d}-{day:02d}-{gamepk}.ftr'
                        
                        os.makedirs(os.path.dirname(filename), exist_ok=True)
                        feather.write_feather(gameDF, filename, compression='uncompressed')


        except Exception as e:
            logger.error(e)

    logger.info("Done parse")

    # Generate manifest
    # We need to scan the output directory for all generated Feather files
    # Output directory is ../data/{year}
    
    manifest = {}
    # Glob patterns are relative to CWD of script?
    # If running in backend/, we look in ../data/
    
    # We want to support all years, so ../data/*/*.ftr
    files = glob.glob('../data/*/*.ftr')
    
    for f in files:
        # f is like "../data/2025/2025-10-31-813025.ftr"
        # When served from root, the path should be "data/2025/2025-10-31-813025.ftr"
        # So we strip the leading "../"
        
        web_path = f.replace('../', '')
        
        # Extract date from filename
        basename = os.path.basename(f)
        # 2025-10-31-813025.ftr
        parts = basename.split('-')
        date_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
        
        if date_str not in manifest:
            manifest[date_str] = []
        manifest[date_str].append(web_path)
        
    # Write manifest to ../data/games.json
    os.makedirs('../data', exist_ok=True)
    with open('../data/games.json', 'w') as f:
        json.dump(manifest, f)
        
    logger.info(f"Generated manifest with {len(files)} games")



logger.info('Loaded parse')


if __name__ == "__main__":
    pass
