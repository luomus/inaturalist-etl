
import datetime
import sys

import getInat
import inatToDw
import inatHelpers
import postDw

import pandas
import json
import os

def reduce_minutes(datetime_str, minutes_to_reduce):
    # Replace encoded characters with their actual representations
    formatted_str = datetime_str.replace('%3A', ':').replace('%2B', '+').replace('%2F', '/')

    # Convert the string to a datetime object
    datetime_obj = datetime.datetime.fromisoformat(formatted_str)

    # Subtract 3 minutes
    new_datetime_obj = datetime_obj - datetime.timedelta(minutes=minutes_to_reduce)

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

# Example usage
# set_variable('test_var', 'test_value')


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

# Example usage
#variables = read_variables()
#print(variables)

'''
def setAirflowVariable(variable, value):
  """Sets an Airflow variable. If setting fails, waits and tries again. If fails, exits with exception.

  Args:
    variable (string): Name of the variable to be set.
    value (string): Value to be set.

  Raises:
    Exception: Setting fails after multiple tries.

  Returns:
    Nothing.
  """

  maxRetries = 3
  sleepSeconds = 3

  for _ in range(maxRetries):
    try:
      Variable.set(variable, value)
    except:
      print("Setting " + variable + " failed, sleeping " + sleepSeconds + " seconds")
      time.sleep(sleepSeconds)
      continue
    else: # On success
      break
  else:
    raise Exception("Setting " + variable + " failed after " + maxRetries + " retries")
'''

### SETUP

#print(pathlib.Path(__file__).parent.resolve()) # /opt/airflow/dags/inaturalist
#exit("DONE")

#cwd = os.getcwd()
#print(cwd) # /tmp/airflowtmpa_qykltg
#exit("CWD DONE")


target = sys.argv[1] # staging | production
mode = sys.argv[2] # auto | manual


# Load private data
# TODO: Move to helpers, load original table like with emails?
print("Loading private data")
privateObservationData = pandas.read_csv("./privatedata/latest.tsv", sep='\t') 

# Exclude the last row if it is empty
# Check if the last row is indeed empty
if privateObservationData.iloc[-1].isnull().all():
  privateObservationData = privateObservationData.iloc[:-1]

rowCount = len(privateObservationData.index)
print("Loaded " + str(rowCount) + " rows")

private_emails = inatHelpers.load_private_emails()


print("------------------------------------------------") 
print("Starting inat.py, target " + target) 

# This will be the new updatedLast time in Variables. Generating update time here, since observations are coming from the API sorted by id, not by datemodified -> cannot use time of last record
now = datetime.datetime.now()
thisUpdateTime = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
thisUpdateTime = thisUpdateTime.replace(":", "%3A")
thisUpdateTime = thisUpdateTime.replace("+", "%2B")

# Get latest update data
variables = read_variables()

# Automatic scheduled update
if "auto" == mode:
  urlSuffix = ""
  if "staging" == target:
    variableName_latest_obsId = "inat_auto_staging_latest_obsId"
    variableName_latest_update = "inat_auto_staging_latest_update"
  elif "production" == target:
    variableName_latest_obsId = "inat_auto_production_latest_obsId"
    variableName_latest_update = "inat_auto_production_latest_update"

# Manually triggered update
elif "manual" == mode:
  urlSuffix = variables["inat_MANUAL_urlSuffix"]
  if "staging" == target:
    variableName_latest_obsId = "inat_MANUAL_staging_latest_obsId"
    variableName_latest_update = "inat_MANUAL_staging_latest_update"
  elif "production" == target:
    variableName_latest_obsId = "inat_MANUAL_production_latest_obsId"
    variableName_latest_update = "inat_MANUAL_production_latest_update"

else:
   exit("Invalid mode")

AirflowLatestObsId = variables[variableName_latest_obsId]
AirflowLatestUpdate = variables[variableName_latest_update]

# Reduce minutes from datetime. This is done because observations can appear on the API with delay of few minutes, which would cause them not to be processed. 
AirflowLatestUpdate = reduce_minutes(AirflowLatestUpdate, 3)

# GET DATA
page = 1
props = { "sleepSeconds": 10, "perPage": 100, "pageLimit": 10000, "urlSuffix": urlSuffix }

# For each pageful of data
for multiObservationDict in getInat.getUpdatedGenerator(AirflowLatestObsId, AirflowLatestUpdate, **props):

  # If no more observations on page, finish the process by saving update time and resetting observation id to zero.
  if False == multiObservationDict:
    print("Finishing, setting latest update to " + thisUpdateTime)
    set_variable(variableName_latest_update, thisUpdateTime)
    set_variable(variableName_latest_obsId, 0)
    break

  # CONVERT
  dwObservations, latestObsId = inatToDw.convertObservations(multiObservationDict['results'], privateObservationData, private_emails)

  # POST
  postSuccess = postDw.postMulti(dwObservations, target)

  # If this pageful contained data, and was saved successfully to DW, set latestObsId as variable
  if postSuccess:
    set_variable(variableName_latest_obsId, latestObsId)

  if page < props["pageLimit"]:
    page = page + 1
  else:
    # Exception because this should not happen in production (happens only if pageLimit is too low compared to frequency of this script being run)
    raise Exception("Page limit " + str(props["pageLimit"]) + " reached, this means that either page limit is set for debugging, or value is too low for production.")


print("End") 
print("------------------------------------------------") 

