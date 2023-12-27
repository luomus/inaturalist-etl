

import requests

import sys
import os

from secret_data import secret_data


def postSingle(dwObs, target):
#  dwObsJson = json.dumps(dwObs)
#  print(dwObsJson)
#  exit()

  if "staging" == target:
    print("Pushing to staging API")
    targetUrl = "https://apitest.laji.fi/v0/warehouse/push?access_token=" + secret_data.inat_staging_token

  elif "production" == target:
    print("Pushing to production API")
    targetUrl = "https://api.laji.fi/v0/warehouse/push?access_token=" + secret_data.inat_production_token


  # Sending post request and saving the response as response object 
  print("Pushing to " + targetUrl)
  targetResponse = requests.post(url = targetUrl, json = dwObs) 

  if 200 == targetResponse.status_code:
    print("DW API responded " + str(targetResponse.status_code))
#    print(targetResponse.text) # DEBUG
    return True

  else:
    errorCode = str(targetResponse.status_code)
#    print(targetResponse.text) # DEBUG
    raise Exception(f"DW API responded with error {errorCode}")


def postMulti(dwObs, target):
#  dwObsJson = json.dumps(dwObs)

  if "staging" == target:
    print("Pushing to staging API.")
    targetUrl = "https://apitest.laji.fi/v0/warehouse/push?access_token=" + secret_data.inat_staging_token

  elif "production" == target:
    print("Pushing to production API")
    targetUrl = "https://api.laji.fi/v0/warehouse/push?access_token=" + secret_data.inat_production_token

  # sending post request and saving the response as response object 
  print("Pushing to " + targetUrl)
  targetResponse = requests.post(url = targetUrl, json = dwObs) 

  if 200 == targetResponse.status_code:
    print("API responded " + str(targetResponse.status_code))
    return True

  else:
    errorCode = str(targetResponse.status_code)
    raise Exception(f"API responded with error {errorCode}")


