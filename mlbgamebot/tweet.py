import datetime
import tweepy
import os
import io
import logging
import setup  # pylint: disable=unused-import
from setup import TWITTER_HANDLES
from PIL import ImageFont, Image, ImageDraw
import plotly.graph_objects as go

logger = logging.getLogger()


def createGauge(defenseScore, offenseScore, thrillScore):
    '''Creates gauges to be used with tweets'''

    gauge = go.Figure()

    gauge.add_trace(go.Indicator(
        mode="number+gauge",
        value=max(min(defenseScore, 10), 0),
        domain={'x': [0.25, 0.9], 'y': [0.7, 0.9]},
        title={'text': "Defense", 'font': {'color': 'white'}},
        number={'font': {'color': 'white'}},
        gauge={
            'shape': "bullet",
            'axis': {'range': [0, 10], 'visible': False},
            'steps': [
                {'range': [0, 2], 'color': "red"},
                {'range': [2, 4], 'color': "orange"},
                {'range': [4, 6], 'color': "lightgreen"},
                {'range': [6, 8], 'color': "green"},
                {'range': [8, 10], 'color': "darkgreen"}],
            'bar': {'color': "darkblue", "thickness": 0.6}}))

    gauge.add_trace(go.Indicator(
        mode="number+gauge",
        value=max(min(offenseScore, 10), 0),
        domain={'x': [0.25, 0.9], 'y': [0.4, 0.6]},
        title={'text': "Offense", 'font': {'color': 'white'}},
        number={'font': {'color': 'white'}},
        gauge={
            'shape': "bullet",
            'axis': {'range': [0, 10], 'visible': False},
            'steps': [
                {'range': [0, 2], 'color': "red"},
                {'range': [2, 4], 'color': "orange"},
                {'range': [4, 6], 'color': "lightgreen"},
                {'range': [6, 8], 'color': "green"},
                {'range': [8, 10], 'color': "darkgreen"}],
            'bar': {'color': "darkblue", "thickness": 0.6}}))

    gauge.add_trace(go.Indicator(
        mode="number+gauge",
        value=max(min(thrillScore, 10), 0),
        domain={'x': [0.25, 0.9], 'y': [0.1, 0.3]},
        title={'text': "Thrill", 'font': {'color': 'white'}},
        number={'font': {'color': 'white'}},
        gauge={
            'shape': "bullet",
            'axis': {'range': [0, 10], 'visible': False},
            'steps': [
                {'range': [0, 2], 'color': "red"},
                {'range': [2, 4], 'color': "orange"},
                {'range': [4, 6], 'color': "lightgreen"},
                {'range': [6, 8], 'color': "green"},
                {'range': [8, 10], 'color': "darkgreen"}],
            'bar': {'color': "darkblue", "thickness": 0.6}}))

    gauge.update_layout(paper_bgcolor='black', height=200,
                        width=600, margin={'t': 0.2, 'b': 0.2, 'l': 0})

    return io.BytesIO(gauge.to_image(format="png"))


def createImage(gamedate, away, home, defenseScore, offenseScore, thrillScore):
    '''Creates image to be used with tweets'''

    myImage = Image.new(mode="RGB", size=(600, 400))

    homeImg = Image.open(f'images/{home}.png')
    awayImg = Image.open(f'images/{away}.png')
    gauge = Image.open(createGauge(defenseScore, offenseScore, thrillScore))

    myImage.paste(awayImg.resize((140, 140)), (80, 70))
    myImage.paste(homeImg.resize((140, 140)), (380, 70))
    myImage.paste(gauge.resize((600, 150)), (40, 220))

    titleStr = f'{gamedate:%d-%b-%Y}'

    draw = ImageDraw.Draw(myImage)
    font = ImageFont.truetype("images/Ubuntu.ttf", 40)
    atFont = ImageFont.truetype("images/Courgette.ttf", 70)
    length = draw.textsize(titleStr, font=font)[0]
    draw.text(((600-length)/2, 20), titleStr, font=font, fill="white")
    length = draw.textsize("at", font=atFont)[0]
    draw.text(((600-length)/2, 100), "at", font=atFont, fill="white")

    return myImage


def tweet(filename, image, gamedate, away, home):
    '''Tweets results'''

    auth = tweepy.OAuthHandler(
        os.getenv("TWITTER_API_KEY"), os.getenv("TWITTER_API_KEY_SECRET"))
    auth.set_access_token(os.getenv("TWITTER_BOT_ACCESS_TOKEN"), os.getenv(
        "TWITTER_BOT_ACCESS_TOKEN_SECRET"))
    api = tweepy.API(auth)

    tweetStr = f'{gamedate:%d-%b-%Y}: {TWITTER_HANDLES[away]} at {TWITTER_HANDLES[home]}'

    media = api.media_upload(filename)
    
    logger.info(f'Tweeting about game {filename}')
    api.update_status(status=tweetStr, media_ids=[media.media_id])
