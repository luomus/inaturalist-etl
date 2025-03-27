
import datetime
import sys

import getInat
import inatToDw
import inatHelpers
import postDw

import pandas
import json
import os

def subtract_minutes(datetime_str, minutes_to_subtract):
    # Replace encoded characters with their actual representations
    formatted_str = datetime_str.replace('%3A', ':').replace('%2B', '+').replace('%2F', '/')

    # Convert the string to a datetime object
    datetime_obj = datetime.datetime.fromisoformat(formatted_str)

    # Subtract the specified number of minutes
    new_datetime_obj = datetime_obj - datetime.timedelta(minutes=minutes_to_subtract)

    # Convert back to the required string format
    new_datetime_str = new_datetime_obj.isoformat().replace(':', '%3A').replace('+', '%2B').replace('/', '%2F')

    return new_datetime_str


# Temp helper
def printObject(object):
  print(object.__dict__)


def set_variable(var_name, var_value):
    # Path to the JSON file
    file_path = './store/data.json'

    # Read existing data from the file
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
    else:
        data = {}

    # Update the data with new variable
    data[var_name] = var_value

    # Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def read_variables():
    # Path to the JSON file
    file_path = './store/data.json'

    # Check if the file exists
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            # Read and return the data from the file
            return json.load(file)
    else:
        # Return an empty dictionary if the file does not exist
        return {}


### SETUP

# Mandatory command line arguments
target = sys.argv[1] # staging | production
mode = sys.argv[2] # auto | manual

if sys.argv[3].lower() == 'false':
  logging_on = False
else:
  logging_on = True

# Optional command line arguments
# Sleep between requests, default 10 seconds
if len(sys.argv) > 4:
  sleep = int(sys.argv[4]) 
  if sleep < 1:
    sleep = 10
else:
  sleep = 10

# This will be the new updatedLast time in Variables. Generating update time here, since observations are coming from the API sorted by id, not by datemodified -> cannot use time of last record
now = datetime.datetime.now()
thisUpdateTime = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
thisUpdateTime = thisUpdateTime.replace(":", "%3A")
thisUpdateTime = thisUpdateTime.replace("+", "%2B")

print("Starting at " + str(thisUpdateTime))
print("Target " + str(target))
print("Mode " + str(mode))
print("Logging " + str(logging_on))
print("Sleep " + str(sleep))

# Load private data
# TODO: Move to helpers, load original table like with emails?
privateObservationData = pandas.read_csv("./privatedata/latest.tsv", sep='\t') 

# Exclude the last row if it is empty
# Check if the last row is indeed empty
if privateObservationData.iloc[-1].isnull().all():
  privateObservationData = privateObservationData.iloc[:-1]

rowCount = len(privateObservationData.index)
print("Loaded " + str(rowCount) + " private observation rows")

private_emails = inatHelpers.load_private_emails()

if logging_on:
  print("------------------------------------------------") 


# Get latest update data
variables = read_variables()

# Automatic scheduled update
if "auto" == mode:
  urlSuffix = ""
  if "staging" == target:
    variableName_latest_obsId = "inat_auto_staging_latest_obsId"
    variableName_latest_update = "inat_auto_staging_latest_update"
    variableName_status = "inat_auto_staging_status"
  elif "production" == target:
    variableName_latest_obsId = "inat_auto_production_latest_obsId"
    variableName_latest_update = "inat_auto_production_latest_update"
    variableName_status = "inat_auto_production_status"

# Manually triggered update
elif "manual" == mode:
  urlSuffix = variables["inat_MANUAL_urlSuffix"]
  if "staging" == target:
    variableName_latest_obsId = "inat_MANUAL_staging_latest_obsId"
    variableName_latest_update = "inat_MANUAL_staging_latest_update"
    variableName_status = "inat_MANUAL_staging_status"
  elif "production" == target:
    variableName_latest_obsId = "inat_MANUAL_production_latest_obsId"
    variableName_latest_update = "inat_MANUAL_production_latest_update"
    variableName_status = "inat_MANUAL_production_status"
else:
   exit("Invalid mode")

latest_obs_id = variables[variableName_latest_obsId]
latest_update = variables[variableName_latest_update]

# Reduce minutes from datetime. This is done because observations can appear on the API with delay of few minutes, which would cause them not to be processed. 
latest_update = subtract_minutes(latest_update, 3)

# GET DATA
page = 1
props = { "sleepSeconds": sleep, "perPage": 100, "pageLimit": 10000, "urlSuffix": urlSuffix, "logging_on": logging_on }

# For each pageful of data
for multiObservationDict in getInat.getUpdatedGenerator(latest_obs_id, latest_update, **props):

  # If no more observations on page, finish the process by saving update time and resetting observation id to zero.
  if False == multiObservationDict:
    set_variable(variableName_latest_update, thisUpdateTime)
    set_variable(variableName_latest_obsId, 0)
    set_variable(variableName_status, "finished")
    print("Finished, latest update set to " + thisUpdateTime)
    break

  # CONVERT
  dwObservations, latestObsId = inatToDw.convertObservations(multiObservationDict['results'], privateObservationData, private_emails, logging_on)

  # POST
  postSuccess = postDw.postMulti(dwObservations, target, logging_on)

  # If this pageful contained data, and was saved successfully to DW, set latestObsId as variable
  if postSuccess:
    set_variable(variableName_latest_obsId, latestObsId)
    set_variable(variableName_status, "ongoing")

  if page < props["pageLimit"]:
    page = page + 1
  else:
    # Exception because this should not happen in production (happens only if pageLimit is too low compared to frequency of this script being run)
    raise Exception("Page limit " + str(props["pageLimit"]) + " reached, this means that either page limit is set for debugging, or value is too low for production.")

if logging_on:
  print("------------------------------------------------") 

