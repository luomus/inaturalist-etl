FROM python:3.11-slim-bookworm

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y rclone && \
    pip install --upgrade pip

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Prepare the application directory (with appropriate permissions for OpenShift)
RUN mkdir -p /usr/src/app

# Copy the app and adjust permissions for OpenShift
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY ./app /usr/src/app
RUN chgrp -R 0 /usr/src/app && \
    chmod -R g=u /usr/src/app /etc/passwd

WORKDIR /usr/src/app

ENTRYPOINT ["entrypoint.sh"]
