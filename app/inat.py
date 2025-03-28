import datetime
import sys
import os
import json

import getInat
import inatToDw
import inatHelpers
import postDw
import logger

import pandas

def subtract_minutes(datetime_str, minutes_to_subtract):
    """Subtract minutes from a datetime string.

    Args:
        datetime_str (string): ISO format datetime string
        minutes_to_subtract (int): Number of minutes to subtract

    Raises:
        ValueError: If datetime string is invalid

    Returns:
        string: New datetime string in ISO format
    """
    try:
        # Replace encoded characters with their actual representations
        formatted_str = datetime_str.replace('%3A', ':').replace('%2B', '+').replace('%2F', '/')

        # Convert the string to a datetime object
        datetime_obj = datetime.datetime.fromisoformat(formatted_str)

        # Subtract the specified number of minutes
        new_datetime_obj = datetime_obj - datetime.timedelta(minutes=minutes_to_subtract)

        # Convert back to the required string format
        new_datetime_str = new_datetime_obj.isoformat().replace(':', '%3A').replace('+', '%2B').replace('/', '%2F')

        return new_datetime_str
    except ValueError as e:
        raise ValueError(f"Invalid datetime string: {datetime_str}") from e


# Temp helper
def printObject(object):
  print(object.__dict__)


def set_variable(var_name, var_value):
    """Set a variable in the data store.

    Args:
        var_name (string): Name of the variable
        var_value: Value to store

    Raises:
        Exception: If file operations fail
    """
    file_path = './store/data.json'

    try:
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
    except Exception as e:
        raise Exception(f"Failed to update data store: {str(e)}")


def read_variables():
    """Read variables from the data store.

    Raises:
        Exception: If file operations fail

    Returns:
        dict: Stored variables
    """
    file_path = './store/data.json'

    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
        else:
            return {}
    except Exception as e:
        raise Exception(f"Failed to read data store: {str(e)}")


### SETUP

# Mandatory command line arguments
if len(sys.argv) < 4:
    raise ValueError("Missing required arguments. Usage: python inat.py <target> <mode> <full_logging> [sleep]")

target = sys.argv[1] # staging | production
mode = sys.argv[2] # auto | manual

if sys.argv[3].lower() == 'false':
    full_logging_on = False
else:
    full_logging_on = True

# Optional command line arguments
# Sleep between requests, default 10 seconds
if len(sys.argv) > 4:
    try:
        sleep = int(sys.argv[4])
        if sleep < 1:
            sleep = 10
    except ValueError:
        sleep = 10
else:
    sleep = 10

# Setup logging
logger.setup_logging(full_logging_on)

# This will be the new updatedLast time in Variables. Generating update time here, since observations are coming from the API sorted by id, not by datemodified -> cannot use time of last record
now = datetime.datetime.now()
thisUpdateTime = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
thisUpdateTime = thisUpdateTime.replace(":", "%3A")
thisUpdateTime = thisUpdateTime.replace("+", "%2B")

logger.log_minimal("Starting at " + str(thisUpdateTime))
logger.log_minimal("Target " + str(target))
logger.log_minimal("Mode " + str(mode))
logger.log_minimal("Full logging " + str(full_logging_on))
logger.log_minimal("Sleep between iNat requests " + str(sleep))

# Load private data
try:
    privateObservationData = pandas.read_csv("./privatedata/latest.tsv", sep='\t')

    # Exclude the last row if it is empty
    if privateObservationData.iloc[-1].isnull().all():
        privateObservationData = privateObservationData.iloc[:-1]

    rowCount = len(privateObservationData.index)
    logger.log_minimal("Loaded " + str(rowCount) + " private observation rows")
except Exception as e:
    raise Exception(f"Failed to load private observation data: {str(e)}")

try:
    private_emails = inatHelpers.load_private_emails()
except Exception as e:
    raise Exception(f"Failed to load private emails: {str(e)}")

logger.log_full("------------------------------------------------")

# Get latest update data
try:
    variables = read_variables()
except Exception as e:
    raise Exception(f"Failed to read variables: {str(e)}")

# Automatic scheduled update
if mode == "auto":
    urlSuffix = ""
    if target == "staging":
        variableName_latest_obsId = "inat_auto_staging_latest_obsId"
        variableName_latest_update = "inat_auto_staging_latest_update"
        variableName_status = "inat_auto_staging_status"
    elif target == "production":
        variableName_latest_obsId = "inat_auto_production_latest_obsId"
        variableName_latest_update = "inat_auto_production_latest_update"
        variableName_status = "inat_auto_production_status"
    else:
        raise ValueError(f"Invalid target: {target}")

# Manually triggered update
elif mode == "manual":
    urlSuffix = variables.get("inat_MANUAL_urlSuffix", "")
    if target == "staging":
        variableName_latest_obsId = "inat_MANUAL_staging_latest_obsId"
        variableName_latest_update = "inat_MANUAL_staging_latest_update"
        variableName_status = "inat_MANUAL_staging_status"
    elif target == "production":
        variableName_latest_obsId = "inat_MANUAL_production_latest_obsId"
        variableName_latest_update = "inat_MANUAL_production_latest_update"
        variableName_status = "inat_MANUAL_production_status"
    else:
        raise ValueError(f"Invalid target: {target}")
else:
    raise ValueError(f"Invalid mode: {mode}")

latest_obs_id = variables.get(variableName_latest_obsId, 0)
latest_update = variables.get(variableName_latest_update, "")

if not latest_update:
    raise ValueError(f"Missing latest update time for {mode} mode")

# Reduce minutes from datetime. This is done because observations can appear on the API with delay of few minutes, which would cause them not to be processed. 
try:
    latest_update = subtract_minutes(latest_update, 3)
except ValueError as e:
    raise ValueError(f"Invalid latest update time: {str(e)}")

# GET DATA
page = 1
props = {"sleepSeconds": sleep, "perPage": 100, "pageLimit": 10000, "urlSuffix": urlSuffix}

# For each pageful of data
try:
    for multiObservationDict in getInat.getUpdatedGenerator(latest_obs_id, latest_update, **props):
        # If no more observations on page, finish the process by saving update time and resetting observation id to zero.
        if multiObservationDict is False:
            set_variable(variableName_latest_update, thisUpdateTime)
            set_variable(variableName_latest_obsId, 0)
            set_variable(variableName_status, "finished")
            logger.log_minimal("Finished, latest update set to " + thisUpdateTime)
            break

        # CONVERT
        dwObservations, latestObsId = inatToDw.convertObservations(multiObservationDict['results'], privateObservationData, private_emails)

        # POST
        postSuccess = postDw.postMulti(dwObservations, target)

        # If this pageful contained data, and was saved successfully to DW, set latestObsId as variable
        if postSuccess:
            set_variable(variableName_latest_obsId, latestObsId)
            set_variable(variableName_status, "ongoing")

        if page < props["pageLimit"]:
            page = page + 1
        else:
            # Exception because this should not happen in production (happens only if pageLimit is too low compared to frequency of this script being run)
            raise Exception("Page limit " + str(props["pageLimit"]) + " reached, this means that either page limit is set for debugging, or value is too low for production.")

except Exception as e:
    logger.log_minimal(f"Error during processing: {str(e)}")
    # Don't re-raise the exception, just exit with error code
    sys.exit(1)

logger.log_full("------------------------------------------------")

