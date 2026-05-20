import time
import logging
import requests

def request_with_retry(url: str, headers: dict = None, params: dict = None, max_retries: int = 5) -> dict:
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            # rate limit → retry after delay
            if response.status_code == 429:
                wait = 2 ** attempt
                logging.warning(f"Rate limited. Waiting {wait}s")
                time.sleep(wait)
                continue

            # server errors → retry after delay
            if 500 <= response.status_code < 600:
                wait = 2 ** attempt
                logging.warning(f"Server error {response.status_code}. Retrying in {wait}s")
                time.sleep(wait)
                continue

            # client errors → raise exception
            if 400 <= response.status_code < 500:
                raise Exception(f"Client error {response.status_code}: {response.text}")

            return response.json()

        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Request failed permanently: {e}")
                raise
            wait = 2 ** attempt
            logging.warning(f"Request failed: {e}. Retrying in {wait}s")
            time.sleep(wait)

    return None

#---------------------------------------------------------------------------------------------------
def fetch_data(url: str, data_key: str, headers: dict = None, params: dict = None, paginate: bool = False) -> list:
    try:
        if params:
            log_params = params.copy()
        else:
            log_params = {}

        for sensitive_key in ['key', 'X-Auth-Token', 'api_key', 'token']:
            log_params.pop(sensitive_key, None)

        if paginate:
            return fetch_paginated(url, data_key, headers, params, log_params)
        else:
            return fetch_single(url, data_key, headers, params, log_params)
    
    except Exception as e:
        logging.error(f"Fetch failed: {e}")
        raise

#---------------------------------------------------------------------------------------------------
def fetch_paginated(url: str, data_key: str, headers: dict = None, params: dict = None, log_params: dict = None) -> list:

    log_fetch_start(url, "paginated", log_params)

    all_results = []
    limit = 100
    offset = 0

    while True:
        if params:
            paged_params = params.copy()
        else:
            paged_params = {}

        paged_params.update({"limit": limit, "offset": offset})

        data = request_with_retry(url, headers=headers, params=paged_params)

        if data is None:
            raise Exception(f"Critical API error (None response) for URL: {url}")

        if data_key not in data:
            logging.error(f"Missing key '{data_key}' in response from {url}")
            break

        page = data.get(data_key) or []

        if not page:
            break

        all_results.extend(page)

        logging.info(f"Fetched page offset={offset} size={len(page)}")

        time.sleep(1)

        if len(page) < limit:
            break

        offset += limit

    logging.info(f"API Fetch done | URL: {url} | Total: {len(all_results)}")
    return all_results

#---------------------------------------------------------------------------------------------------
def fetch_single(url: str, data_key: str, headers: dict = None, params: dict = None, log_params: dict = None) -> list:
    
    log_fetch_start(url, "single", log_params)

    data = request_with_retry(url, headers=headers, params=params)

    if data is None:
        raise Exception(f"Critical API error (None response) for URL: {url}")

    if data_key not in data:
        logging.error(f"Missing key '{data_key}' in response from {url}")
        return []

    result = data.get(data_key) or []

    if not result:
        logging.warning(f"No {data_key} found in API response | URL: {url}")
        return []

    time.sleep(1)

    return result

#---------------------------------------------------------------------------------------------------
def log_fetch_start(url: str, mode: str, log_params: dict = None):

    if log_params:
        logging.info(f"API Fetch | URL: {url} | Mode: {mode} | Params: {log_params}")
    else:
        logging.info(f"API Fetch | URL: {url} | Mode: {mode}")

