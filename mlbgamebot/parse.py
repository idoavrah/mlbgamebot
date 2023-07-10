from email.utils import parsedate
from unittest.result import failfast
from numpy import sign
from setup import fromdate, todate, TEAM_ABBREVIATIONS
from jsonpath_ng import jsonpath, parse
from pytz import timezone
import tweet
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
                    'eventNum', 'inning', 'half', 'atbat', 'balls', 'strikes', 'outs', 'pitches', 'awayScore', 'homeScore', 'event', 'result']

    global fromdate, todate

    filename = ''

    for d in pd.date_range(fromdate, todate):

        year, month, day = d.year, d.month, d.day

        try:

            filename = f'data/schedule/{year}/{year}-{month:02d}-{day:02d}.json'
            if not os.path.isfile(filename):
                continue

            with open(filename, 'r') as scheduleFile:
                data = json.load(scheduleFile)
                games = [match.value for match in parse(
                    'dates[*].games').find(data)][0]
                for game in games:
                    gamepk = game["gamePk"]

                    filename = f'data/parsed/{year}/{year}-{month:02d}-{day:02d}-{gamepk}.ftr'
                    if os.path.isfile(filename):
                        continue

                    filename = f'data/games/{year}/{gamepk}.json'
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
                                                   play["details"]["description"]])

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
                                               atbat["result"]["description"]])

                            eventNum += 1

                        scores, superlatives = evaluate.start(eventsList)

                        gameDF = pd.DataFrame(eventsList, columns=GAME_COLUMNS)
                        gameDF['defenseScore'] = scores[0]
                        gameDF['offenseScore'] = scores[1]
                        gameDF['thrillScore'] = scores[2]
                        gameDF['superlatives'] = superlatives

                        gamedate = datetime.date(year, month, day)

                        filename = f'data/parsed/{year}/{year}-{month:02d}-{day:02d}-{gamepk}.ftr'
                        os.makedirs(os.path.dirname(filename), exist_ok=True)
                        feather.write_feather(gameDF, filename)

                        image = tweet.createGameImage(gamedate, game["teams"]["away"]["team"]["name"],
                                                      game["teams"]["home"]["team"]["name"], scores[0], scores[1], scores[2])
                        filename = f'data/parsed/{year}/{year}-{month:02d}-{day:02d}-{gamepk}.png'
                        image.save(filename)

                        await tweet.tweetGame(
                            filename, gamedate, game["teams"]["away"]["team"]["name"], game["teams"]["home"]["team"]["name"])

        except Exception as e:
            logger.error(e)

    logger.info("Done parse")


async def daily(parseDay=None):

    try:

        logger.info("Start daily")

        if not parseDay:
            parseDay = datetime.date.today() - datetime.timedelta(days=1)

        filename = f'data/schedule/{parseDay.year}/{parseDay.year}-{parseDay.month:02d}-{parseDay.day:02d}.png'
        if os.path.isfile(filename):
            logger.info("Already tweeted daily summary, file exists")
            return

        hour = datetime.datetime.now(timezone('EST')).hour
        if hour != 11:
            logger.info(f'Not the time to tweet the daily summary ({hour})')
            return

        files = glob.glob(
            f'data/parsed/{parseDay.year}/{parseDay.year}-{parseDay.month:02d}-{parseDay.day:02d}*.ftr')

        if not files:
            logger.info("No games for daily summary")
            return

        li = []

        for gamefile in files:
            df = ftr.read_dataframe(gamefile)
            li.append(df)

        total = pd.concat(li)

        games = total[["homeTeam", "awayTeam", "gamePk", "defenseScore", "offenseScore", "thrillScore"]
                      ].drop_duplicates().replace({"homeTeam": TEAM_ABBREVIATIONS, "awayTeam": TEAM_ABBREVIATIONS})

        games[["defenseScore", "offenseScore", "thrillScore"]] = games[["defenseScore", "offenseScore", "thrillScore"]].clip(lower=0, upper=10)

        image = await tweet.createDailySummaryImage(parseDay, games)
        image.write_image(filename)

        await tweet.tweetDailySummary(parseDay, filename)

    except Exception as e:
        logger.error(e)

    logger.info("Done daily")

logger.info('Loaded parse')


if __name__ == "__main__":
    daily()
