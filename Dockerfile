FROM python:3.11-slim-bookworm

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

RUN apt update
RUN apt -y upgrade

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

CMD ["tail", "-f", "/dev/null"]