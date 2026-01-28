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

# Create writable runtime directories (OpenShift-friendly: arbitrary UID)
RUN mkdir -p /app/store /app/privatedata && \
    chmod 0777 /app/store /app/privatedata && \
    chmod +x /app/entrypoint.py

# Run as non-root by default (OpenShift will still be able to override UID)
RUN useradd --system --uid 1001 --home-dir /app --shell /usr/sbin/nologin appuser
USER 1001

WORKDIR /app

# Use Python entrypoint instead of shell script
ENTRYPOINT ["python3", "/app/entrypoint.py"]

# Default CMD: production update parameters (can be overridden in OpenShift)
CMD ["production", "auto", "true", "5"]