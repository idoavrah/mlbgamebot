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

    SUMMARY_COLUMNS = ['gamePk', 'officialDate', 'season', 'seriesDescription', 'gameDescription', 'venue',
                       'homeTeam', 'awayTeam', 'homeFinalScore', 'awayFinalScore',
                       'defenseScore', 'offenseScore', 'thrillScore', 'superlatives', 'filePath']

    global fromdate, todate

    filename = ''
    update_manifest = False

    for d in pd.date_range(fromdate, todate):

        year, month, day = d.year, d.month, d.day
        day_summary_rows = []  # one row per game for this day

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

                        target_dir = f'../data/{year}'
                        filename = f'{target_dir}/{year}-{month:02d}-{day:02d}-{gamepk}.ftr'
                        web_path = filename.replace('../', '')

                        if not os.path.isfile(filename):
                            os.makedirs(os.path.dirname(filename), exist_ok=True)
                            feather.write_feather(gameDF, filename, compression='uncompressed')
                            logger.info(f"Wrote {filename}")
                            update_manifest = True
                        else:
                            logger.debug(f"Skipping {filename} (already parsed)")

                        # Collect summary row for this game
                        last = gameDF.iloc[-1]
                        day_summary_rows.append({
                            'gamePk': str(gamepk),
                            'officialDate': game["officialDate"],
                            'season': game["season"],
                            'seriesDescription': game.get("seriesDescription", ""),
                            'gameDescription': game.get("description", ""),
                            'venue': game.get("venue", {}).get("name", ""),
                            'homeTeam': game["teams"]["home"]["team"]["name"],
                            'awayTeam': game["teams"]["away"]["team"]["name"],
                            'homeFinalScore': last['homeScore'],
                            'awayFinalScore': last['awayScore'],
                            'defenseScore': scores[0],
                            'offenseScore': scores[1],
                            'thrillScore': scores[2],
                            'superlatives': superlatives,
                            'filePath': web_path,
                        })

        except Exception as e:
            logger.error(e)

        # Write daily summary FTR if we have any games for this day
        if day_summary_rows:
            date_str = f'{year}-{month:02d}-{day:02d}'
            target_dir = f'../data/{year}'
            summary_path = f'{target_dir}/{date_str}-summary.ftr'
            os.makedirs(target_dir, exist_ok=True)
            summaryDF = pd.DataFrame(day_summary_rows, columns=SUMMARY_COLUMNS)
            feather.write_feather(summaryDF, summary_path, compression='uncompressed')
            logger.info(f"Wrote daily summary {summary_path} ({len(day_summary_rows)} games)")
            update_manifest = True

    logger.info("Done parse")

    # Generate manifests from all summary FTR files on disk
    if not update_manifest:
        return

    # Scan for summary FTRs: ../data/*/{date}-summary.ftr
    summary_files = glob.glob('../data/*/*-summary.ftr')
    dates_found = []

    for sf in summary_files:
        basename = os.path.basename(sf)  # e.g. 2026-03-12-summary.ftr
        date_str = basename.replace('-summary.ftr', '')  # e.g. 2026-03-12
        dates_found.append(date_str)

        # Also write per-day JSON with list of gamePks for that day
        try:
            day_df = feather.read_table(sf).to_pandas()
            gamepks = day_df['gamePk'].tolist()
            year_dir = os.path.dirname(sf)
            day_json_path = os.path.join(year_dir, f'{date_str}.json')
            with open(day_json_path, 'w') as jf:
                json.dump(gamepks, jf)
        except Exception as e:
            logger.error(f"Failed writing per-day JSON for {date_str}: {e}")

    dates_found = sorted(set(dates_found))

    # Write top-level index.json
    os.makedirs('../data', exist_ok=True)
    with open('../data/index.json', 'w') as f:
        json.dump(dates_found, f)

    logger.info(f"Wrote index.json with {len(dates_found)} dates")

logger.info('Loaded parse')


if __name__ == "__main__":
    asyncio.run(start())
