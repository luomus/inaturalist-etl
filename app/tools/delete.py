import requests

import sys
import os

# Include token form sibling folder
parent_dir = os.path.dirname(os.path.dirname(__file__))
secret_data_path = os.path.join(parent_dir, 'secret_data')
sys.path.append(secret_data_path)

import secret_data
 
# Define the API endpoint
url = f"https://api.laji.fi/v0/warehouse/push?access_token={secret_data.inat_production_token}"

# Path to plain iNaturalist identifiers to be deleted from Laji.fi
# The file was generated with https://gist.github.com/mikkohei13/fc7ccb467b8088a5ad3ec8310cff3b1a
file_path = "test.txt"

# Read all lines from the file and create a single payload
with open(file_path, "r") as file:
    identifiers = [f"DELETE http://tun.fi/HR.3211/{line.strip()}" for line in file]

payload = "\n".join(identifiers)

headers = {
    "Content-Type": "text/plain"
}

response = requests.post(url, data=payload, headers=headers)

# Check for successful response
if response.status_code == 200:
    print("Successfully sent DELETE commands for all identifiers")
else:
    print(f"Failed to send DELETE commands: {response.status_code} - {response.text}")

