import logging
import os
from dotenv import load_dotenv
import datetime

load_dotenv()

logging.basicConfig(
    format='%(asctime)-24s %(filename)-20s %(funcName)-20s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger()

TWITTER_HANDLES = {'Los Angeles Angels': "#Angels",
                   'Houston Astros': "#Astros",
                   'Oakland Athletics': "#Athletics",
                   'Toronto Blue Jays': "#BlueJays",
                   'Atlanta Braves': "#Braves",
                   'Milwaukee Brewers': "#Brewers",
                   'St. Louis Cardinals': "#Cardinals",
                   'Chicago Cubs': "#Cubs",
                   'Arizona Diamondbacks': "#Dbacks",
                   'Los Angeles Dodgers': "#Dodgers",
                   'San Francisco Giants': "#SFGiants",
                   'Cleveland Guardians': "#Guardians",
                   'Cleveland Indians': "#Guardians",
                   'Seattle Mariners': "#Mariners",
                   'Miami Marlins': "#Marlins",
                   'New York Mets': "#Mets",
                   'Washington Nationals': "#Nationals",
                   'Baltimore Orioles': "#Orioles",
                   'San Diego Padres': "#Padres",
                   'Philadelphia Phillies': "#Phillies",
                   'Pittsburgh Pirates': "#Pirates",
                   'Texas Rangers': "#Rangers",
                   'Tampa Bay Rays': "#Rays",
                   'Boston Red Sox': "#RedSox",
                   'Cincinnati Reds': "#Reds",
                   'Colorado Rockies': "#Rockies",
                   'Kansas City Royals': "#Royals",
                   'Detroit Tigers': "#Tigers",
                   'Minnesota Twins': "#Twins",
                   'Chicago White Sox': "#WhiteSox",
                   'New York Yankees': "#Yankees"}


TEAM_ABBREVIATIONS = {'Los Angeles Angels': "LAA",
                      'Houston Astros': "HOU",
                      'Oakland Athletics': "OAK",
                      'Toronto Blue Jays': "TOR",
                      'Atlanta Braves': "ATL",
                      'Milwaukee Brewers': "MIL",
                      'St. Louis Cardinals': "STL",
                      'Chicago Cubs': "CHC",
                      'Arizona Diamondbacks': "ARI",
                      'Los Angeles Dodgers': "LAD",
                      'San Francisco Giants': "SF",
                      'Cleveland Guardians': "CLE",
                      'Cleveland Indians': "CLE",
                      'Seattle Mariners': "SEA",
                      'Miami Marlins': "MIA",
                      'New York Mets': "NYM",
                      'Washington Nationals': "WAS",
                      'Baltimore Orioles': "BAL",
                      'San Diego Padres': "SD",
                      'Philadelphia Phillies': "PHI",
                      'Pittsburgh Pirates': "PIT",
                      'Texas Rangers': "TEX",
                      'Tampa Bay Rays': "TB",
                      'Boston Red Sox': "BOS",
                      'Cincinnati Reds': "CIN",
                      'Colorado Rockies': "COL",
                      'Kansas City Royals': "KC",
                      'Detroit Tigers': "DET",
                      'Minnesota Twins': "MIN",
                      'Chicago White Sox': "CHW",
                      'New York Yankees': "NYY"}


def init():

    logger.info('Start init')

    global fromdate, todate

    year = int(os.getenv("LOAD_YEAR")) if os.getenv("LOAD_YEAR") else None
    month = int(os.getenv("LOAD_MONTH")) if os.getenv("LOAD_MONTH") else None
    day = int(os.getenv("LOAD_DAY")) if os.getenv("LOAD_DAY") else None

    if not year:
        fromdate = datetime.date.today() - datetime.timedelta(days=1)
        todate = datetime.date.today()

    elif not month:
        fromdate = datetime.date(year, 1, 1)
        todate = datetime.date(year, 12, 31)

    elif not day:
        fromdate = datetime.date(year, month, 1)
        todate = datetime.date(year, month+1, 1) - datetime.timedelta(days=1)

    else:
        fromdate = todate = datetime.date(year, month, day)

    logger.info('Done init')


init()

logger.debug(f'{fromdate} => {todate}')

logger.info('Loaded setup')
