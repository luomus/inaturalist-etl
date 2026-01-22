#!/bin/bash
set -e

echo "Downloading data from Allas..."
python3 /app/download_from_allas.py

echo "Data download complete. Executing command: $@"
exec "$@"
