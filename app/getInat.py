import requests
import json
from collections import OrderedDict
import time
import logger
import sys

def getPageFromAPI(url):
  """Get a single pageful of observations from iNat.

  Args:
    url (string): API URL to get data from.

  Raises:
    Exception: If API responds with error code, returns invalid JSON, or connection fails after retries.

  Returns:
    orderedDictionary: Observations and associated API metadata (paging etc.)
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
      raise Exception("Failed to connect to iNaturalist API after multiple retries")

    if inatResponse.status_code != 200:
      errorCode = str(inatResponse.status_code)
      logger.log_minimal(f"iNaturalist API responded with error {errorCode}")
      if errorCode == "403":
        logger.log_minimal("Access denied by iNaturalist API. This may be due to invalid parameters.")
        sys.exit(1)
      raise Exception(f"iNaturalist API responded with error {errorCode}")

    logger.log_full("iNaturalist API responded " + str(inatResponse.status_code))

    try:
      inatResponseDict = json.loads(inatResponse.text, object_pairs_hook=OrderedDict)
      return inatResponseDict
    except:
      logger.log_minimal("iNaturalist responded with invalid JSON")
      raise Exception("iNaturalist API returned invalid JSON")

  raise Exception("Failed to get data from iNaturalist API after all retries")


def getUpdatedGenerator(latestObsId, latestUpdateTime, pageLimit, perPage, sleepSeconds, urlSuffix = ""):
  """Generator that gets and yields new and updated iNat observations.

  Args:
    latestObsId (int): Highest observation id that should not be fetched.
    latestUpdateTime (string): Time after which updated observations should be fecthed.
    pageLimit (int): Maximum number of pages to fetch
    perPage (int): Number of observations per page
    sleepSeconds (int): Seconds to sleep between requests
    urlSuffix (string): Optional additional parameters for API request. Must start with "&".

  Raises:
    Exception: If getPageFromAPI() fails to fetch data.

  Yields:
    orderedDictionary: Observations and associated API metadata (paging etc.)
    boolean: Returns False when no more results.
  """
  page = 1

  while True:
    logger.log_full("Getting set number " + str(page) + " of " + str(pageLimit) + " latestObsId " + str(latestObsId) + " latestUpdateTime " + latestUpdateTime)

    # place_id filter: Finland, Åland & Finland EEZ
    url = "https://api.inaturalist.org/v1/observations?place_id=7020%2C10282%2C165234&page=1&per_page=" + str(perPage) + "&order=asc&order_by=id&updated_since=" + latestUpdateTime + "&id_above=" + str(latestObsId) + "&include_new_projects=true" + urlSuffix

    # Place: whole world
#    url = "https://api.inaturalist.org/v1/observations?page=1&per_page=" + str(perPage) + "&order=asc&order_by=id&updated_since=" + latestUpdateTime + "&id_above=" + str(latestObsId) + "&include_new_projects=true" + urlSuffix

    if " " in url:
      raise Exception("iNat API url malformed, contains space(s)")

    try:
      inatResponseDict = getPageFromAPI(url)
    except Exception as e:
      logger.log_minimal(f"Error fetching data: {str(e)}")
      raise

    resultObservationCount = inatResponseDict["total_results"]
    logger.log_minimal("Received " + str(resultObservationCount) + " observations")

    if resultObservationCount == 0:
      logger.log_full("No more observations.")
      yield False
      break
    
    latestObsId = inatResponseDict["results"][-1]["id"]
    page = page + 1
  
    time.sleep(sleepSeconds)
    yield inatResponseDict


def getSingle(observationId):
  """Gets and returns a single iNat observation.

  Args:
    observationId (int): iNat observation id.

  Raises:
    Exception: If observation not found or API error occurs.

  Returns:
    orderedDictionary: Single observation and associated API metadata.
  """
  url = "https://api.inaturalist.org/v1/observations?id=" + str(observationId) + "&order=desc&order_by=created_at&include_new_projects=true"
  print("URL: " + url)

  try:
    inatResponseDict = getPageFromAPI(url)
  except Exception as e:
    logger.log_minimal(f"Error fetching observation {observationId}: {str(e)}")
    raise

  if inatResponseDict["total_results"] == 0:
    raise Exception(f"Observation {observationId} not found in iNaturalist")

  return inatResponseDict
  

