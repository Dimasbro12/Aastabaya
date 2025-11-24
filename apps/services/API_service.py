import json
import requests
import logging
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

from django.conf import settings
import time
from apps.models import HumanDevelopmentIndex, Publication, Infographic, News
from apps.serializers import HumanDevelopmentIndexSerializer, PublicationSerializer, InfographicSerializer, NewsSerializer

logger = logging.getLogger(__name__)


class IPMService:
    @staticmethod
    def fetch_ipm_data():
        """Fetches and processes IPM data from Google Sheets into a long-format DataFrame."""
        print("📡 Fetching IPM data from Google Sheets...")
        try:
            # Scope akses Google Sheets dan Google Drive
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            # Autentikasi
            credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
            client = gspread.authorize(credentials)

            # ID Google Sheet dari link
            SHEET_ID = "1keS9YFYO1qzAawWgLh2U2pY6xX5ppKUnhbdHQYfU5HM"
            sheet = client.open_by_key(SHEET_ID).worksheet("Indeks Pembangunan Manusia Menu")

            # Ambil semua data dan buat DataFrame
            data = sheet.get_all_values()
            headers = data[0]
            data_rows = data[1:]
            df = pd.DataFrame(data_rows, columns=headers)
            print(f"✅ Raw data fetched with shape: {df.shape}")

            # --- Data Cleaning and Transformation ---
            df = df.rename(columns={'Kabupaten/Kota\nRegency/Municipality': 'Kabupaten/Kota'})
            empty_columns = [col for col in df.columns if col == '']
            if empty_columns:
                df = df.drop(columns=empty_columns)

            # Melt DataFrame to long format
            year_columns = [col for col in df.columns if col.isdigit()]
            df_melted = pd.melt(df, id_vars=['Kabupaten/Kota'], value_vars=year_columns,
                                var_name='Tahun', value_name='Value')

            # Convert data types
            df_melted['Tahun'] = pd.to_numeric(df_melted['Tahun'])
            df_melted['Value'] = pd.to_numeric(df_melted['Value'], errors='coerce')

            # Hapus baris dengan nilai IPM yang tidak valid/kosong
            df_melted.dropna(subset=['Value'], inplace=True)

            print(f"✅ Data processed. Total valid records: {len(df_melted)}")
            return df_melted

        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"Spreadsheet with ID '{SHEET_ID}' not found.")
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Worksheet 'Indeks Pembangunan Manusia Menu' not found.")
        except Exception as e:
            logger.error(f"An error occurred while fetching/processing IPM data: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

    @staticmethod
    def save_ipm_to_db(ipm_df):
        """Saves the processed IPM DataFrame to the database using a serializer."""
        if ipm_df.empty:
            print("⚠️ No IPM data to save.")
            return 0, 0

        created_count = 0
        updated_count = 0

        for index, row in ipm_df.iterrows():
            location_name = str(row['Kabupaten/Kota']).strip()

            # Skip any residual non-data rows
            if not location_name or "Sumber/Source" in location_name:
                continue

            # Determine location type
            location_type = HumanDevelopmentIndex.LocationType.MUNICIPALITY if location_name.startswith("KOTA") else HumanDevelopmentIndex.LocationType.REGENCY

            data_to_serialize = {
                'location_name': location_name,
                'location_type': location_type.value,
                'year': row['Tahun'],
                'ipm_value': row['Value']
            }

            # Coba dapatkan instance yang ada terlebih dahulu
            try:
                instance = HumanDevelopmentIndex.objects.get(location_name=location_name, year=row['Tahun'])
            except HumanDevelopmentIndex.DoesNotExist:
                instance = None

            # Berikan instance ke serializer jika ada (untuk mode update)
            serializer = HumanDevelopmentIndexSerializer(instance=instance, data=data_to_serialize)

            if serializer.is_valid():
                # Gunakan serializer.save() yang akan menangani create atau update secara otomatis
                obj = serializer.save()
                created = instance is None # Jika instance sebelumnya tidak ada, berarti ini adalah create
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            else:
                print(f"❌ Error saat menyimpan IPM untuk {location_name} tahun {row['Tahun']}: {serializer.errors}")

        print(f"💾 Total IPM records created: {created_count}, updated: {updated_count}")
        return created_count, updated_count

    @classmethod
    def sync_ipm(cls):
        """Fungsi utama untuk sinkronisasi data API -> database."""
        ipm_df = cls.fetch_ipm_data()
        created_count, updated_count = cls.save_ipm_to_db(ipm_df)
        return created_count, updated_count
        
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
        created_count = 0
        updated_count = 0
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
                obj, created = News.objects.update_or_create(
                    news_id=item.get("news_id"),
                    defaults=serializer.validated_data
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            else:
                print(f"❌ Error saat menyimpan news_id {item.get('news_id')}: {serializer.errors}")
        print(f"💾 Total berita dibuat: {created_count}, diperbarui: {updated_count}")
        return created_count, updated_count

    @classmethod
    def sync_news(cls):
        """Fungsi utama untuk sinkronisasi data API -> database."""
        news_list = cls.fetch_news_data()
        created_count, updated_count = cls.save_news_to_db(news_list)
        return created_count, updated_count
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
        created_count = 0
        updated_count = 0
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
                obj, created = Publication.objects.update_or_create(
                    pub_id=item.get("pub_id"),
                    defaults=serializer.validated_data
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            else:
                print(f"❌ Error saat menyimpan pub_id {item.get('pub_id')}: {serializer.errors}")
        print(f"💾 Total publikasi dibuat: {created_count}, diperbarui: {updated_count}")
        return created_count, updated_count

    @classmethod
    def sync_publication(cls):
        """Fungsi utama untuk sinkronisasi data API -> database."""
        publication_list = cls.fetch_publication_data()
        created_count, updated_count = cls.save_publication_to_db(publication_list)
        return created_count, updated_count

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
        created_count = 0
        updated_count = 0
        for item in infographic_list:
            # Map API fields to model fields
            data_to_serialize = {
                'title': item.get('title'),
                'image': item.get('img'),
                'dl': item.get('dl')
            }
            serializer = InfographicSerializer(data=data_to_serialize)
            if serializer.is_valid():
                obj, created = Infographic.objects.update_or_create(
                    title=item.get("title"), # Assuming title is unique for infographics
                    defaults=serializer.validated_data
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            else:
                print(f"❌ Error saat menyimpan infografis {item.get('title')}: {serializer.errors}")
        print(f"💾 Total infografis dibuat: {created_count}, diperbarui: {updated_count}")
        return created_count, updated_count

    @classmethod
    def sync_infographic(cls):
        """Fungsi utama untuk sinkronisasi data API -> database."""
        infographic_list = cls.fetch_infographic_data()
        created_count, updated_count = cls.save_infographic_to_db(infographic_list)
        return created_count, updated_count
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
