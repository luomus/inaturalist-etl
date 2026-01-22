FROM python:3.11-slim-bookworm

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

RUN apt update
RUN apt -y upgrade
RUN apt install -y rclone

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Copy the download script
COPY app/download_from_allas.py /app/download_from_allas.py
RUN chmod +x /app/download_from_allas.py

# Copy the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app

ENTRYPOINT ["/entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]