import requests
import sys
import os

# Get the script directory to construct absolute paths
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

# Load token from environment variable
token = os.getenv('LAJI_PRODUCTION_TOKEN')
if not token:
    print("Error: LAJI_PRODUCTION_TOKEN environment variable is not set")
    sys.exit(1)

# Define the API endpoint
url = f"https://api.laji.fi/v0/warehouse/push?access_token={token}"

# Read IDs from CSV file (skip header row)
ids_file_path = os.path.join(base_dir, 'privatedata', 'ids_to_be_deleted.csv')

with open(ids_file_path, "r") as ids_file:
    lines = ids_file.readlines()
    # Skip header row and strip newlines
    identifiers = [f"DELETE http://tun.fi/HR.3211/{line.strip()}" for line in lines[1:] if line.strip()]

if not identifiers:
    print("Warning: No identifiers found to delete")
    sys.exit(0)

payload = "\n".join(identifiers)

headers = {
    "Content-Type": "text/plain"
}

try:
    response = requests.post(url, data=payload, headers=headers)
    response.raise_for_status()  # Raises an exception for bad status codes
except requests.exceptions.RequestException as e:
    print(f"Error: Failed to send DELETE commands: {e}")
    sys.exit(1)

# Check for successful response
if response.status_code == 200:
    print(f"Successfully sent DELETE commands for {len(identifiers)} identifiers")
else:
    print(f"Failed to send DELETE commands: {response.status_code} - {response.text}")
    sys.exit(1)

