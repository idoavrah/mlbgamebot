from numpy import sign
from setup import fromdate, todate
import logging
import pandas as pd

logger = logging.getLogger()

# event weights (defense, offense, thrill)
SCORES = {"Balk": [-1, 1, 1],
          "Batter Out": [1, 0, 0],
          "Bunt Groundout": [1, 0, 0],
          "Bunt Lineout": [1, 0, 1],
          "Bunt Pop Out": [1, 0, 0],
          "Catcher Interference": [0, 1, 1],
          "Caught Stealing 2B": [2, 0, 2],
          "Caught Stealing 3B": [2, 0, 2],
          "Caught Stealing Home": [3, 0, 3],
          "Defensive Indiff": [0, 0, 0],
          "Defensive Sub": [0, 0, 0],
          "Defensive Switch": [0, 0, 0],
          "Double": [-1, 2, 2],
          "Double Play": [2, -1, 2],
          "Ejection": [0, 0, 1],
          "Error": [-1, 0, 2],
          "Field Error": [-1, 1, 2],
          "Fielders Choice": [1, 0, 0],
          "Fielders Choice Out": [1, 0, 0],
          "Field Out": [1, 0, 0],
          "Flyout": [1, 0, 0],
          "Forceout": [1, 0, 0],
          "Game Advisory": [0, 0, 0],
          "Grounded Into DP": [2, -1, 2],
          "Groundout": [1, 0, 0],
          "Hit By Pitch": [0, 1, 1],
          "Home Run": [-1, 3, 3],
          "Injury": [0, 0, 1],
          "Intent Walk": [0, 1, 0],
          "Lineout": [2, 0, 1],
          "Offensive Substitution": [0, 0, 0],
          "Other Advance": [0, 0, 0],
          "Passed Ball": [-1, 0, 1],
          "Pickoff 1B": [2, 0, 2],
          "Pickoff 2B": [2, 0, 2],
          "Pickoff 3B": [2, 0, 2],
          "Pickoff Caught Stealing 2B": [2, 0, 2],
          "Pickoff Caught Stealing 3B": [2, 0, 2],
          "Pickoff Caught Stealing Home": [3, 0, 3],
          "Pickoff Error 1B": [0, 1, 2],
          "Pickoff Error 2B": [0, 1, 2],
          "Pickoff Error 3B": [0, 1, 2],
          "Pitching Substitution": [0, 0, 0],
          "Pop Out": [1, 0, 0],
          "Runner Out": [1, 0, 0],
          "Runner Placed On Base": [0, 0, 2],
          "Sac Bunt": [0, 1, 1],
          "Sac Bunt Double Play": [3, 0, 2],
          "Sac Fly": [0, 1, 1],
          "Sac Fly Double Play": [3, 0, 3],
          "Single": [0, 1, 0],
          "Stolen Base 2B": [0, 2, 2],
          "Stolen Base 3B": [0, 2, 2],
          "Stolen Base Home": [0, 3, 3],
          "Strikeout": [1, 0, 0],
          "Strikeout Double Play": [3, 0, 2],
          "Triple": [-1, 3, 3],
          "Triple Play": [4, -1, 5],
          "Umpire Substitution": [0, 0, 0],
          "Walk": [-1, 1, 1],
          "Wild Pitch": [-1, 1, 1]}


def start(eventsList):
    '''Evaluate Game'''

    superlatives = set()

    inningScores = []
    inning = -1
    diff = 0
    leadChanges = -1
    strikeouts = 0

    homeNohit = True
    awayNoHit = True
    noHitBroken = -1

    runsAway = runsHome = 0

    for eventItem in eventsList:

        GAME_COLUMNS = ['season', 'seriesDescription', 'officialDate', 'awayTeam', 'homeTeam', 'awayFinalScore', 'homeFinalScore', 'gamePk',
                        'eventNum', 'inning', 'half', 'atbat', 'balls', 'strikes', 'outs', 'pitches', 'awayScore', 'homeScore', 'event', 'result']
        event = {
            "inning": eventItem[9],
            "half": eventItem[10],
            "atbat": eventItem[11],
            "pitches": eventItem[15],
            "away_runs": eventItem[16],
            "home_runs": eventItem[17],
            "event": eventItem[18],
            "result": eventItem[19]
        }

        if inning+1 != event["inning"]:
            inning += 1
            if inning > 0:
                logging.debug(f'Total Inning Scores: {inningScores[inning-1]}')
            logging.debug(f'inning {event["inning"]}')
            inningScores.append([0, 0, 0])

        eventScores = SCORES.get(event["event"]).copy(
        ) if SCORES.get(event["event"]) else [0, 0, 0]

        if event["event"] == 'Game Advisory':
            if event["result"] == 'Mound Visit.':
                logging.debug('- Mound Visit bonus')
                eventScores[2] = 0.2
            else:
                continue
        elif event["event"].startswith('Strikeout'):
            strikeouts += 1
            eventScores[0] += strikeouts/20

        runsScored = (event["away_runs"] - runsAway) + \
            (event["home_runs"] - runsHome)

        runsAway = event["away_runs"]
        runsHome = event["home_runs"]

        if diff == 0 and runsScored > 0:
            logging.debug('- Take lead bonus')
            leadChanges += 1
            eventScores[2] += 1  # take lead thrill bonus

        elif diff != 0 and sign(runsHome - runsAway) == 0:
            logging.debug('- Tie game bonus')
            if inning+1 >= 8:
                superlatives.add("Late Tie")
            eventScores[2] += 1  # tie game thrill bonus

        elif diff != 0 and sign(runsHome - runsAway) != sign(diff):
            logging.debug('- Lead change bonus')
            if inning+1 >= 8:
                superlatives.add("Late lead change")
            leadChanges += 1
            eventScores[2] += 3  # lead change thrill bonus

        if " sharp" in event["result"]:
            logging.debug('- Sharp play bonus')
            eventScores[2] += 1
        elif " deflect" in event["result"]:
            logging.debug('- Deflected play bonus')
            eventScores[2] += 1
        elif "challenge" in event["result"]:
            logging.debug('- Challenge bonus')
            eventScores[2] += 1
        elif " softly " in event["result"]:
            logging.debug('- Soft play bonus')
            eventScores[0] += 1

        if event["pitches"] and event["pitches"] > 5:
            eventScores[2] += 0.1  # long at bat thrill bonus

        diff = runsHome - runsAway

        if runsScored:
            logging.debug('- Runs Scored bonus & penalty')
            eventScores[0] -= runsScored  # run scored defense penalty
            eventScores[1] += runsScored  # run scored offense bonus

        if homeNohit and event["event"] in ('Single', 'Double', 'Triple', 'Home Run') and event["half"] == 'top':
            homeNohit = False
            noHitBroken = max(noHitBroken, inning)
        elif awayNoHit and event["event"] in ('Single', 'Double', 'Triple', 'Home Run') and event["half"] == 'bottom':
            awayNoHit = False
            noHitBroken = max(noHitBroken, inning)

        # no hit bid thrill bonus
        if homeNohit and event["atbat"] and event["half"] == 'top' and inning > 4:
            eventScores[0] += inning/2
            eventScores[2] += inning/2
        elif awayNoHit and event["atbat"] and event["half"] == 'bottom' and inning > 4:
            eventScores[0] += inning/2
            eventScores[2] += inning/2

        # late innings factor
        if inning+1 >= 7 and abs(diff) < 3:
            eventScores[2] *= 1.05
        elif inning+1 >= 9 and abs(diff) < 3:
            eventScores[2] *= 1.1

        # diff factor
        eventScores[2] *= (1.1 - abs(diff)/20)

        if event["event"] == 'Triple Play':
            superlatives.add("Triple Play")

        if runsScored == 4:
            superlatives.add("Grand Slam")

        logging.debug(
            f'{event["half"]}: {event["event"]:30}: {eventScores} : Result: {runsAway}:{runsHome}')

        for i, score in enumerate(eventScores):
            inningScores[inning][i] += score

    if inning == -1:
        return [0, 0, 0], ''

    logging.debug(f'Total Inning Scores: {inningScores[inning]}')

    if noHitBroken > 5:
        superlatives.add(f"No Hit Broken on {noHitBroken+1}")
    elif awayNoHit or homeNohit:
        superlatives.add("No Hitter")

    if abs(diff) > 6:
        superlatives.add("Blowout")
    if abs(diff) <= 2:
        superlatives.add("Photo Finish")

    if leadChanges > 3:
        superlatives.add("See Saw")

    if runsAway + runsHome > 15:
        superlatives.add("Extravaganza")

    totalScores = [sum(i)/inning for i in zip(*inningScores)]

    # Inning Scores: {inningScores}')
    logging.debug(
        f'Game result: {runsAway:3}:{runsHome:3}   Game Scores: {totalScores}  Superlatives: {superlatives}')

    if not totalScores:
        totalScores = [0, 0, 0]

    return totalScores, ', '.join(superlatives)



logger.info('Loaded evaluate')

