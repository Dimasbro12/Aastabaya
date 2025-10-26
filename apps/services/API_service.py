from urllib import response
from venv import logger
import requests
import logging
from django.conf import settings
import pandas as pd
import time

logger = logging.getLogger(__name__)

def _fetch_bps_data(model: str):
    all_data = []
    """
    Fetches data from the BPS Web API for a given model.
    """
    try:
        url = f"https://webapi.bps.go.id/v1/api/list/model/{model}/lang/ind/domain/3578/key/{settings.API_KEY}/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  
        data = response.json()
        total_pages = data["data"][0]["pages"]
        for page in range(1, total_pages+1):
            response = requests.get(url, timeout=10)
            response.raise_for_status()  
            if response.status_code == 200:
                d = response.json()
                all_data.extend(d["data"][1])
                time.sleep(.2)
                df = pd.json_normalize(all_data)
            return df
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve BPS data for model '{model}': {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return None

def get_news_data():
    return _fetch_bps_data("news")

def get_publication_data():
    return _fetch_bps_data("publication")

def get_inpographic_data():
    return _fetch_bps_data("infographic")
