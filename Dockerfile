FROM python:3.11-slim-bookworm

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED True

RUN apt update && \
    apt -y upgrade && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy all application code
COPY app/ /app/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.py

WORKDIR /app

# Use Python entrypoint instead of shell script
ENTRYPOINT ["python3", "/app/entrypoint.py"]

# Default CMD: production update parameters (can be overridden in OpenShift)
CMD ["production", "auto", "true", "5"]