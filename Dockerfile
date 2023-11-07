FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN echo nameserver 8.8.8.8 >> /etc/resolv.conf
RUN pip install -r requirements.txt

COPY mlbgamebot ./mlbgamebot
COPY images ./images

USER 1001

CMD ["python", "mlbgamebot/gamebot.py"]
