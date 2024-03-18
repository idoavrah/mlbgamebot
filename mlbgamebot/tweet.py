import os
import io
import logging
import setup  # pylint: disable=unused-import
import asyncio
import plotly.graph_objects as go
from setup import TWITTER_HANDLES, TEAM_ABBREVIATIONS
from PIL import ImageFont, Image, ImageDraw
from telegram import Bot

logger = logging.getLogger()

bot_token = os.getenv('TELEGRAM_BOT_API_TOKEN')
channel_id = os.getenv('TELEGRAM_CHANNEL')

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


def createGameImage(gamedate, away, home, defenseScore, offenseScore, thrillScore):
    '''Creates image to be used with tweets'''

    myImage = Image.new(mode="RGB", size=(600, 400))

    try:
        homeImg = Image.open(f'images/{home}.png')
        awayImg = Image.open(f'images/{away}.png')
        myImage.paste(awayImg.resize((140, 140)), (80, 70))
        myImage.paste(homeImg.resize((140, 140)), (380, 70))
    except FileNotFoundError:
        pass
    
    gauge = Image.open(createGauge(defenseScore, offenseScore, thrillScore))
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

async def createDailySummaryImage(gamedate, games):

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=games["defenseScore"],
        y=games["offenseScore"],
        mode='markers, text',
        text=games['homeTeam'] + ' @ ' + games['awayTeam'],
        textposition="bottom center",
        marker=dict(
            size=games["thrillScore"]*6,
            color=games["thrillScore"],
            line=dict(width=1, color='DarkSlateGrey'),
            colorscale='Rainbow',
            showscale=True
        )
    ))

    fig.update_layout(width=1000, height=1000,
                      paper_bgcolor='rgb(200, 200, 200)',
                      title_font_size=30,
                      font_size=16,
                      title_text=f'Gameday: {gamedate.year}-{gamedate.month:02d}-{gamedate.day:02d}',
                      xaxis_title="Defense Score",
                      yaxis_title="Offense Score")

    fig.update_xaxes(zeroline=False, title_font=dict(size=30), showgrid=False)
    fig.update_yaxes(zeroline=False, title_font=dict(size=30), showgrid=False)

    return fig


async def tweetGame(filename, gamedate, away, home):
    '''Tweets results'''
    try:
        logger.info(f'Tweeting about game {filename}')
        caption = f'#MLB {gamedate:%d-%b-%Y}: {TWITTER_HANDLES[away]} @ {TWITTER_HANDLES[home]}'

        bot = Bot(token=bot_token)
        with open(filename, 'rb') as image_file:
            await bot.send_photo(chat_id=channel_id, photo=image_file, caption=caption)
    except Exception as e:
        logger.error(f'Error tweeting game: {e}')

async def tweetDailySummary(gamedate, filename):
    '''Tweets daily summary'''

    logger.info(f'Tweeting about day {gamedate}')
    caption = f'#MLB scores for {gamedate:%d-%b-%Y}'

    bot = Bot(token=bot_token)
    with open(filename, 'rb') as image_file:
        await bot.send_photo(chat_id=channel_id, photo=image_file, caption=caption)
