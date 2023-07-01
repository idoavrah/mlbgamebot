FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements*.txt .

# Install the required dependencies
RUN pip install -r requirements.txt

# Copy the Python script to the working directory
COPY mlbgamebot ./mlbgamebot
COPY images ./images

# Set the entrypoint to run the Python script
#CMD ["/bin/bash"]
CMD ["python", "mlbgamebot/gamebot.py"]
