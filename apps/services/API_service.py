import requests
import logging
from django.conf import settings
import pandas as pd
import time

logger = logging.getLogger(__name__)

def _fetch_bps_data(model: str):
    """
    Fetches data from the BPS Web API for a given model.
    It handles pagination and aggregates results into a single DataFrame.
    """
    base_url = f"https://webapi.bps.go.id/v1/api/list/model/{model}/lang/ind/domain/3578/key/{settings.API_KEY}/"
    all_data = []

    try:
        # First request to get total pages
        initial_response = requests.get(f"{base_url}page/1", timeout=10)
        initial_response.raise_for_status()
        initial_data = initial_response.json()
        total_pages = int(initial_data["data"][0]["pages"])
        all_data.extend(initial_data["data"][1])

        # Loop through the rest of the pages
        for page in range(2, total_pages + 1):
            paginated_url = f"{base_url}page/{page}"
            response = requests.get(paginated_url, timeout=10)
            response.raise_for_status()
            page_data = response.json()
            all_data.extend(page_data["data"][1])
            time.sleep(0.2) # Be respectful to the API server

        return pd.json_normalize(all_data) if all_data else pd.DataFrame()

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve BPS data for model '{model}': {e}")
    except Exception as e:
        logger.error(f"Unexpected data structure from BPS API for model '{model}': {e}")
    return None

def get_news_data():
    return _fetch_bps_data("news")

def get_publication_data():
    return _fetch_bps_data("publication")

def get_inpographic_data():
    return _fetch_bps_data("infographic")
