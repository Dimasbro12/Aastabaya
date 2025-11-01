import json
import requests
import logging
from django.conf import settings
import time
from apps.models import Publication, Infographic, News
from apps.serializers import PublicationSerializer, InfographicSerializer, NewsSerializer

logger = logging.getLogger(__name__)


class BPSNewsService:
    @staticmethod
    def fetch_news_data():
        base_url = f"https://webapi.bps.go.id/v1/api/list/model/news/lang/ind/domain/3578/key/{settings.API_KEY}/"
        first_page = requests.get(f"{base_url}?page=1").json()
        total_pages = first_page["data"][0]["pages"]
        all_news = first_page["data"][1]
        for page in range(2, total_pages + 1):
            print(f"📡 Fetching page {page} ...")    
            response = requests.get(f"{base_url}?page={page}")
            response.raise_for_status()
            data = response.json()
            if "data" in data and len(data["data"]) > 1:
                all_news.extend(data["data"][1])
        print(f"✅ Total berita diambil: {len(all_news)}")
        return all_news
    @staticmethod
    def save_news_to_db(news_list):
        """Simpan hasil fetch ke database menggunakan serializer."""
        saved_count = 0
        for item in news_list:
            # Map API fields to model fields
            data_to_serialize = {
                'news_id': item.get('news_id'),
                'title': item.get('title'),
                'content': item.get('news'),
                'category_id': item.get('newscat_id'),
                'category_name': item.get('newscat_name'),
                'release_date': item.get('rl_date'),
                'picture_url': item.get('picture')
            }
            serializer = NewsSerializer(data=data_to_serialize)
            if serializer.is_valid():
                News.objects.update_or_create(
                    news_id=item.get("news_id"),
                    defaults=serializer.validated_data
                )
                saved_count += 1
            else:
                print(f"❌ Error saat menyimpan news_id {item.get('news_id')}: {serializer.errors}")
        print(f"💾 Total berita tersimpan: {saved_count}")
        return saved_count
    @classmethod
    def sync_news(cls):
        """Fungsi utama untuk sinkronisasi data API -> database."""
        news_list = cls.fetch_news_data()
        saved = cls.save_news_to_db(news_list)
        return saved
class BPSPublicationService:
    @staticmethod
    def fetch_publication_data():
        base_url = f"https://webapi.bps.go.id/v1/api/list/model/publication/lang/ind/domain/3578/key/{settings.API_KEY}/"
        first_page = requests.get(f"{base_url}?page=1").json()
        total_pages = first_page["data"][0]["pages"]
        all_publication = first_page["data"][1]
        for page in range(2, total_pages + 1):
            print(f"📡 Fetching page {page} ...")    
            response = requests.get(f"{base_url}?page={page}")
            response.raise_for_status()
            data = response.json()
            if "data" in data and len(data["data"]) > 1:
                all_publication.extend(data["data"][1])
        print(f"✅ Total publikasi diambil: {len(all_publication)}")
        return all_publication
    @staticmethod
    def save_publication_to_db(publication_list):
        """Simpan hasil fetch ke database menggunakan serializer."""
        saved_count = 0
        for item in publication_list:
            # Map API fields to model fields
            data_to_serialize = {
                'pub_id': item.get('pub_id'),
                'title': item.get('title'),
                'abstract': item.get('abstract'),
                'image': item.get('cover'),
                'dl': item.get('pdf'),
                'date': item.get('rl_date'),
                'size': item.get('size')
            }
            serializer = PublicationSerializer(data=data_to_serialize)
            if serializer.is_valid():
                Publication.objects.update_or_create(
                    pub_id=item.get("pub_id"),
                    defaults=serializer.validated_data
                )
                saved_count += 1
            else:
                print(f"❌ Error saat menyimpan pub_id {item.get('pub_id')}: {serializer.errors}")
        print(f"💾 Total publikasi tersimpan: {saved_count}")
        return saved_count
    @classmethod
    def sync_publication(cls):
        """Fungsi utama untuk sinkronisasi data API -> database."""
        publication_list = cls.fetch_publication_data()
        saved = cls.save_publication_to_db(publication_list)
        return saved

class BPSInfographicService:
    @staticmethod
    def fetch_infographic_data():
        base_url = f"https://webapi.bps.go.id/v1/api/list/model/infographic/lang/ind/domain/3578/key/{settings.API_KEY}/"
        first_page = requests.get(f"{base_url}?page=1").json()
        total_pages = first_page["data"][0]["pages"]
        all_infographic = first_page["data"][1]
        for page in range(2, total_pages + 1):
            print(f"📡 Fetching page {page} ...")    
            response = requests.get(f"{base_url}?page={page}")
            response.raise_for_status()
            data = response.json()
            if "data" in data and len(data["data"]) > 1:
                all_infographic.extend(data["data"][1])
        print(f"✅ Total infografis diambil: {len(all_infographic)}")
        return all_infographic
    @staticmethod
    def save_infographic_to_db(infographic_list):
        """Simpan hasil fetch ke database menggunakan serializer."""
        saved_count = 0
        for item in infographic_list:
            # Map API fields to model fields
            data_to_serialize = {
                'title': item.get('title'),
                'image': item.get('img'),
                'dl': item.get('dl')
            }
            serializer = InfographicSerializer(data=data_to_serialize)
            if serializer.is_valid():
                Infographic.objects.update_or_create(
                    title=item.get("title"), # Assuming title is unique for infographics
                    defaults=serializer.validated_data
                )
                saved_count += 1
            else:
                print(f"❌ Error saat menyimpan infografis {item.get('title')}: {serializer.errors}")
        print(f"💾 Total infografis tersimpan: {saved_count}")
        return saved_count
    @classmethod
    def sync_infographic(cls):
        """Fungsi utama untuk sinkronisasi data API -> database."""
        infographic_list = cls.fetch_infographic_data()
        saved = cls.save_infographic_to_db(infographic_list)
        return saved
# def _fetch_bps_data(model: str):
#     """
#     Fetches data from the BPS Web API for a given model, handling pagination.
#     """
#     base_url = f"https://webapi.bps.go.id/v1/api/list/model/{model}/lang/ind/domain/3578/key/{settings.API_KEY}/"
#     all_data = []

#     try:
#         # First request to get total pages
#         initial_response = requests.get(f"{base_url}page/1", timeout=10)
#         initial_response.raise_for_status()
#         initial_data = initial_response.json()
#         total_pages = int(initial_data["data"][0]["pages"])
#         all_data.extend(initial_data["data"][1])

#         # Loop through the rest of the pages
#         for page in range(2, total_pages + 1):
#             paginated_url = f"{base_url}page/{page}"
#             response = requests.get(paginated_url, timeout=10)
#             response.raise_for_status()
#             page_data = response.json()
            
#             if model == "publication":
#                 serializer = PublicationSerializer(data=page_data, many=True)
#                 for res in page_data:
#                     data = json.dumps(res)
#                     pub_id = res["pub_id"]
#                     title = res["title"]
#                     abstract = res["abstract"]
#                     image = res["cover"]
#                     dl = res["pdf"]
#                     date = res["rl_date"]
#                     size = res["size"]
#                     # publication = Publication.objects.create(
#                     # pub_id = pub_id,
#                     # title = title,
#                     # abstract = abstract,
#                     # image = image,
#                     # dl = dl,
#                     # date = date,
#                     # size = size,
#                     # )
#             if model == "infographic":
#                 for res in page_data:
#                     data = json.dumps(res)
#                     title = res["title"]
#                     image = res["img"]
#                     dl = res["dl"]
#                     infographic =Inpographic.objects.create(
#                     title = title,
#                     image = image,
#                     dl = dl,
#                     )
#             if model == "news":
#                 for res in page_data:
#                     data = json.dumps(res)
#                     title = res["title"]
#                     content = res.get()
#                     category_id = res.get()
#                     infographic =Inpographic.objects.create(
#                     title = title,
#                     image = image,
#                     dl = dl,
#                     )
            
#             all_data.extend(page_data["data"][1])
#             time.sleep(0.2) # Be respectful to the API server

#         return all_data

#     except requests.exceptions.RequestException as e:
#         logger.error(f"Failed to retrieve BPS data for model '{model}': {e}")
#     except Exception as e:
#         logger.error(f"Unexpected data structure from BPS API for model '{model}': {e}")
#     return []

# def get_news_data():
#     return _fetch_bps_data("news")

# def get_publication_data():
#     return _fetch_bps_data("publication")

# def get_inpographic_data():
#     return _fetch_bps_data("infographic")
