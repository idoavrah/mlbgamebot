FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/*.py ./backend/

VOLUME ["/app/data"]

WORKDIR /app/backend
CMD ["python3", "gamebot.py"]
