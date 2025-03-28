import requests
import sys
import os
import logger

def get_token(target):
    """Get API token for the specified target environment.

    Args:
        target (string): Either "staging" or "production"

    Raises:
        ValueError: If target is invalid or required environment variable is not set

    Returns:
        string: API token
    """
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
        raise ValueError(f"Invalid target environment: {target}")

def postSingle(dwObs, target):
    """Post a single observation to FinBIF DW API.

    Args:
        dwObs (dict): Observation data to post
        target (string): Either "staging" or "production"

    Raises:
        ValueError: If target is invalid
        Exception: If API request fails

    Returns:
        bool: True if successful
    """
    if target == "staging":
        logger.log_full("Pushing to staging API")
        targetUrl = "https://apitest.laji.fi/v0/warehouse/push?access_token=" + get_token(target)
    elif target == "production":
        logger.log_full("Pushing to production API")
        targetUrl = "https://api.laji.fi/v0/warehouse/push?access_token=" + get_token(target)
    else:
        raise ValueError(f"Invalid target environment: {target}")

    logger.log_full("Pushing to " + targetUrl)
    targetResponse = requests.post(url=targetUrl, json=dwObs)

    if targetResponse.status_code == 200:
        logger.log_full("DW API responded " + str(targetResponse.status_code))
        return True
    else:
        errorCode = str(targetResponse.status_code)
        raise Exception(f"DW API responded with error {errorCode}: {targetResponse.text}")


def postMulti(dwObs, target):
    """Post multiple observations to FinBIF DW API.

    Args:
        dwObs (list): List of observations to post
        target (string): Either "staging" or "production"

    Raises:
        ValueError: If target is invalid
        Exception: If API request fails

    Returns:
        bool: True if successful
    """
    if target == "staging":
        logger.log_full("Pushing to staging API")
        targetUrl = "https://apitest.laji.fi/v0/warehouse/push?access_token=" + get_token(target)
    elif target == "production":
        logger.log_full("Pushing to production API")
        targetUrl = "https://api.laji.fi/v0/warehouse/push?access_token=" + get_token(target)
    else:
        raise ValueError(f"Invalid target environment: {target}")

    logger.log_full("Pushing to " + targetUrl)
    targetResponse = requests.post(url=targetUrl, json=dwObs)

    if targetResponse.status_code == 200:
        logger.log_full("API responded " + str(targetResponse.status_code))
        return True
    else:
        errorCode = str(targetResponse.status_code)
        raise Exception(f"API responded with error {errorCode}: {targetResponse.text}")


