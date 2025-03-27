import requests
import sys
import os
import logger

def get_token(target):
    if target == "staging":
        token = os.getenv('LAJI_STAGING_TOKEN')
        if not token:
            raise ValueError("LAJI_STAGING_TOKEN environment variable is not set")
        return token
    elif target == "production":
        token = os.getenv('LAJI_PRODUCTION_TOKEN')
        if not token:
            raise ValueError("LAJI_PRODUCTION_TOKEN environment variable is not set")
        return token
    else:
        raise ValueError(f"Invalid target: {target}")

def postSingle(dwObs, target):
#  dwObsJson = json.dumps(dwObs)
#  print(dwObsJson)
#  exit()

  if "staging" == target:
    logger.log_full("Pushing to staging API")
    targetUrl = "https://apitest.laji.fi/v0/warehouse/push?access_token=" + get_token(target)

  elif "production" == target:
    logger.log_full("Pushing to production API")
    targetUrl = "https://api.laji.fi/v0/warehouse/push?access_token=" + get_token(target)


  # Sending post request and saving the response as response object 
  logger.log_full("Pushing to " + targetUrl)
  targetResponse = requests.post(url = targetUrl, json = dwObs) 

  if 200 == targetResponse.status_code:
    logger.log_full("DW API responded " + str(targetResponse.status_code))
#    print(targetResponse.text) # DEBUG
    return True

  else:
    errorCode = str(targetResponse.status_code)
#    print(targetResponse.text) # DEBUG
    raise Exception(f"DW API responded with error {errorCode}")


def postMulti(dwObs, target):
#  dwObsJson = json.dumps(dwObs)

  if "staging" == target:
    logger.log_full("Pushing to staging API.")
    targetUrl = "https://apitest.laji.fi/v0/warehouse/push?access_token=" + get_token(target)

  elif "production" == target:
    logger.log_full("Pushing to production API")
    targetUrl = "https://api.laji.fi/v0/warehouse/push?access_token=" + get_token(target)

  # sending post request and saving the response as response object 
  logger.log_full("Pushing to " + targetUrl)
  targetResponse = requests.post(url = targetUrl, json = dwObs) 

  if 200 == targetResponse.status_code:
    logger.log_full("API responded " + str(targetResponse.status_code))
    return True

  else:
    errorCode = str(targetResponse.status_code)
    logger.log_full(f"API responded with error {errorCode}")
    raise Exception(f"API responded with error {errorCode}")


