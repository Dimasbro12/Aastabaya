from urllib import response
from venv import logger
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def _fetch_bps_data(model: str):
    """
    Fetches data from the BPS Web API for a given model.
    """
    try:
        url = f"https://webapi.bps.go.id/v1/api/list/model/{model}/lang/ind/domain/3578/key/{settings.API_KEY}/"
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve BPS data for model '{model}': {e}")
    return None

def get_news_data():
    return _fetch_bps_data("news")

def get_publication_data():
    return _fetch_bps_data("publication")

def get_inpographic_data():
    return _fetch_bps_data("infographic")
