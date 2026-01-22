FROM python:3.11-slim-bookworm

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

RUN apt update
RUN apt -y upgrade
RUN apt install -y rclone

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Copy application code
COPY app /app

# Copy and set up entrypoint script
COPY entrypoint.py /entrypoint.py
RUN chmod +x /entrypoint.py

WORKDIR /app

ENTRYPOINT ["/entrypoint.py"]