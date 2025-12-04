import json
import pandas as pd
import gspread
import httpx  # Menggunakan httpx untuk request asinkron
from channels.generic.websocket import AsyncWebsocketConsumer
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
from asgiref.sync import sync_to_async


# === 🔹 Ambil Data Google Sheets ===
def fetch_ipm_data():
    try:
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'credentials.json', scope
        )
        client = gspread.authorize(credentials)

        SHEET_ID = "1keS9YFYO1qzAawWgLh2U2pY6xX5ppKUnhbdHQYfU5HM"
        sheet = client.open_by_key(SHEET_ID).worksheet("Indeks Pembangunan Manusia Menu_Y-to-Y")

        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        return df
    
    except Exception as e:
        print(f"❌ ERROR Sheets: {e}")
        return pd.DataFrame()

# Dijalankan sebagai fungsi async agar tidak memblokir
@sync_to_async
def fetch_ipm_data_async():
    return fetch_ipm_data()

# === 🔹 Rules agar LLM hanya menjawab berdasarkan data Spreadsheet ===
RULES = """
Peraturan:
1. Kamu TIDAK BOLEH menggunakan pengetahuan luar.
2. Jawaban harus berasal dari data spreadsheet di bawah.
3. Jika tidak ada di data → jawab persis:
"Saya tidak menemukan informasi tersebut di data."
4. Jangan menebak atau membuat data baru.
5. Berikan jawaban dalam Bahasa Indonesia.
"""


# ============================================================
#               🔥 WebSocket AI Consumer 🔥
# ============================================================
class ChatConsumer(AsyncWebsocketConsumer):
    async def setup_data(self):
        """Mengambil dan menyimpan data IPM untuk koneksi ini."""
        self.df_ipm = await fetch_ipm_data_async()
        print("📌 Google Sheets Loaded for new connection:", not self.df_ipm.empty)

    async def connect(self):
        await self.accept()
        await self.setup_data()

    async def disconnect(self, close_code):
        """Called when the WebSocket closes."""
        print(f"WebSocket disconnected with code: {close_code}")
        
    async def receive(self, text_data):
        user_message = json.loads(text_data)["message"]

        if self.df_ipm.empty:
            await self.send(text_data=json.dumps({"message": "⚠️ Maaf, saya tidak dapat mengambil data saat ini."}))
            return

        prompt = f"{RULES}\n\nData Spreadsheet:\n{self.df_ipm.to_string()}\n\nPertanyaan: {user_message}"
        # === 🔹 KONFIGURASI API OpenRouter ===
        OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
        # === 🔹 CALL API OpenRouter ===
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "tngtech/deepseek-r1t-chimera:free",
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                ai_reply = result.get("choices", [{}])[0].get("message", {}).get("content", "⚠️ Terjadi kesalahan API!")
            except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError) as e:
                print(f"API Error: {e}")
                ai_reply = "⚠️ Terjadi kesalahan saat menghubungi layanan AI."

        # Kirim kembali ke WebSocket Client
        await self.send(text_data=json.dumps({"message": ai_reply}))
