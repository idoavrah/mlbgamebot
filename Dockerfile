FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY mlbgamebot ./mlbgamebot
COPY images ./images

RUN mkdir /app/data && groupadd -r user && useradd -r -g user user && chown -R user:user /app

USER user

CMD ["python", "mlbgamebot/gamebot.py"]
