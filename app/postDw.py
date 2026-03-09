import requests
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


def get_request_config(target):
    """Build FinBIF API request URL and headers for the target environment."""
    if target == "staging":
        target_url = "https://apitest.laji.fi/warehouse/push"
    elif target == "production":
        target_url = "https://api.laji.fi/warehouse/push"
    else:
        raise ValueError(f"Invalid target environment: {target}")

    token = get_token(target)
    headers = {
        "Authorization": f"Bearer {token}",
        "API-Version": "1",
    }
    return target_url, headers


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
    targetUrl, headers = get_request_config(target)
    logger.log_full(f"Pushing to {target} API")

    logger.log_full("Pushing to " + targetUrl)
    targetResponse = requests.post(url=targetUrl, json=dwObs, headers=headers)

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
    targetUrl, headers = get_request_config(target)
    logger.log_full(f"Pushing to {target} API")

    logger.log_full("Pushing to " + targetUrl)
    targetResponse = requests.post(url=targetUrl, json=dwObs, headers=headers)

    if targetResponse.status_code == 200:
        logger.log_full("API responded " + str(targetResponse.status_code))
        return True
    else:
        errorCode = str(targetResponse.status_code)
        raise Exception(f"API responded with error {errorCode}: {targetResponse.text}")


