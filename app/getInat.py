import requests
import json
from collections import OrderedDict
import time
import logger

def getPageFromAPI(url):
  """Get a single pageful of observations from iNat.

  Args:
    url (string): API URL to get data from.

#  Raises:
#    Exception: API responds with code other than 200, or does not repond at all.

  Returns:
    orderedDictionary: Observatons and associated API metadata (paging etc.)
    False: if iNat API responds with error code, or does not repond at all. 
  """
  max_retries = 3
  retry_delay = 10  # seconds

  for attempt in range(max_retries):
    logger.log_full("Getting " + url)
    if attempt > 0:
      logger.log_full(f"Retry attempt {attempt + 1}/{max_retries}")
    
    try:
      inatResponse = requests.get(url)
    except:
      if attempt < max_retries - 1:
        logger.log_full(f"Connection error, waiting {retry_delay} seconds before retry")
        time.sleep(retry_delay)
        retry_delay *= 2  # Exponential backoff
        continue
      logger.log_minimal("Error getting data from iNaturalist API")
      raise Exception("Error getting data from iNaturalist API")

    # TODO: Find out why slightly too large idAbove returns 200 with zero results, but with much too large returns 400 
    if 200 == inatResponse.status_code:
      logger.log_full("iNaturalist API responded " + str(inatResponse.status_code))
    else:
      errorCode = str(inatResponse.status_code)
      logger.log_minimal("iNaturalist responded with error " + errorCode)
#    raise Exception(f"iNaturalist API responded with error {errorCode}")
      return False

    # Tries to convert JSON to dict. If iNat API gave invalid JSON, returns False instead.
    try:
      inatResponseDict = json.loads(inatResponse.text, object_pairs_hook=OrderedDict)
    except:
      logger.log_minimal("iNaturalist responded with invalid JSON")
      inatResponseDict = False

    return inatResponseDict

  return False


def getUpdatedGenerator(latestObsId, latestUpdateTime, pageLimit, perPage, sleepSeconds, urlSuffix = ""):
  """Generator that gets and yields new and updated iNat observations, by handling pagination and calling getPageFromAPI().

  Args:
    latestObsId (int): Highest observation id that should not be fetched.
    latestUpdateTime (string): Time after which updated observations should be fecthed.
    pageLimit (int):
    perPage (int):
    sleepSeconds (int):
    urlSuffix (string): Optional additional parameters for API request. Must start with "&".

#  Raises:
#    Exception: If getPageFromAPI() fails to fetch data.

  Returns:
    orderedDictionary: Yields observations and associated API metadata (paging etc.)
    boolean: Returns False when no more results.
  """

  page = 1

  while True:
    logger.log_full("Getting set number " + str(page) + " of " + str(pageLimit) + " latestObsId " + str(latestObsId) + " latestUpdateTime " + latestUpdateTime)

    # place_id filter: Finland, Åland & Finland EEZ
    url = "https://api.inaturalist.org/v1/observations?place_id=7020%2C10282%2C165234&page=1&per_page=" + str(perPage) + "&order=asc&order_by=id&updated_since=" + latestUpdateTime + "&id_above=" + str(latestObsId) + "&include_new_projects=true" + urlSuffix

    if " " in url:
      raise Exception("iNat API url malformed, contains space(s)")

    inatResponseDict = getPageFromAPI(url)

    # TODO: If response is False, or JSON is invalid, wait and try again
    if False == inatResponseDict:
      logger.log_full("iNat API returned False, waiting 10 seconds and trying again")
      time.sleep(10)
      continue

    resultObservationCount = inatResponseDict["total_results"]

    logger.log_minimal("Received " + str(resultObservationCount) + " observations")

    # If no observations on page, just return False
    if 0 == resultObservationCount:
      logger.log_full("No more observations.")
      yield False
      break
    
    else:
      latestObsId = inatResponseDict["results"][-1]["id"]
      page = page + 1
  
      time.sleep(sleepSeconds)

      # return whole dict
      yield inatResponseDict



def getSingle(observationId):
  """Gets and returns a single iNat observation, by calling getPageFromAPI().

  Args:
    observationId (int): iNat observation id.

  Raises:
    Exception: If getPageFromAPI() fails to fetch data, or if zero result is found.

  Returns:
    orderedDictionary: Single observation and associated API metadata (paging etc.)
  """

  url = "https://api.inaturalist.org/v1/observations?id=" + str(observationId) + "&order=desc&order_by=created_at&include_new_projects=true";

  inatResponseDict = getPageFromAPI(url)

  # TODO: Maybe handle error cases here as well (inatResponseDict is False), at least if this function is used in any automatic process.
  # When getting a single observation, zero results is an error
  if 0 == inatResponseDict["total_results"]:
    raise Exception(f"Zero results from iNaturalist API")

  return inatResponseDict
  

