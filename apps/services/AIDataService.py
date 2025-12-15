import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from django.core.cache import cache
import time
# Define the API scope for Google Sheets
scope = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate using the credentials.json file
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    gc = gspread.authorize(creds)
    print("Authentication with Google Sheets successful!")
except Exception as e:
    print(f"Authentication failed: {e}")
    print("Please ensure 'credentials.json' is correctly uploaded and has the necessary permissions.")

def fetch_all_sheets_data():
    """Fetches and combines all worksheets data from a Google Sheet into a single DataFrame."""
    print("\n📡 Fetching ALL sheets data from Google Sheets...")

    try:
        # Scope akses
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # Autentikasi via service account
        credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(credentials)

        # ID Google Sheet dari link
        SHEET_ID = "1keS9YFYO1qzAawWgLh2U2pY6xX5ppKUnhbdHQYfU5HM"
        spreadsheet = client.open_by_key(SHEET_ID)

        worksheets = spreadsheet.worksheets()
        print(f"📄 Found {len(worksheets)} sheets!")

        df_list = []

        # Loop semua worksheet dengan delay untuk hindari rate limit
        for idx, ws in enumerate(worksheets):
            print(f"➡ Loading sheet ({idx+1}/{len(worksheets)}): {ws.title}")
            try:
                # Langsung pakai get_all_values (1 API call saja, bukan 2)
                all_values = ws.get_all_values()
                
                if len(all_values) > 1:
                    headers = all_values[0]
                    rows = all_values[1:]
                    
                    # Deduplicate headers by adding suffix to duplicates
                    seen = {}
                    new_headers = []
                    for h in headers:
                        if h in seen:
                            seen[h] += 1
                            new_headers.append(f"{h}_{seen[h]}")
                        else:
                            seen[h] = 0
                            new_headers.append(h)
                    
                    # Create DataFrame with deduplicated headers
                    df_temp = pd.DataFrame(rows, columns=new_headers)
                    print(f"   ✓ Loaded ({len(rows)} rows, {len(new_headers)} cols)")
                else:
                    print(f"   ✗ Sheet is empty, skipping...")
                    time.sleep(3)
                    continue
                    
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RATE_LIMIT" in error_str:
                    print(f"   ⏸ Rate limit hit, waiting 60 seconds...")
                    time.sleep(60)  # Wait full 60 seconds to reset quota
                    print(f"   → Retrying {ws.title}...")
                    try:
                        all_values = ws.get_all_values()
                        if len(all_values) > 1:
                            headers = all_values[0]
                            rows = all_values[1:]
                            
                            seen = {}
                            new_headers = []
                            for h in headers:
                                if h in seen:
                                    seen[h] += 1
                                    new_headers.append(f"{h}_{seen[h]}")
                                else:
                                    seen[h] = 0
                                    new_headers.append(h)
                            
                            df_temp = pd.DataFrame(rows, columns=new_headers)
                            print(f"   ✓ Loaded after retry ({len(rows)} rows)")
                        else:
                            print(f"   ✗ Sheet still empty after retry, skipping...")
                            time.sleep(3)
                            continue
                    except Exception as e2:
                        print(f"   ✗ Still failed after retry: {str(e2)[:80]}")
                        time.sleep(3)
                        continue
                else:
                    print(f"   ✗ Error: {error_str[:80]}")
                    time.sleep(3)
                    continue
            
            # Tambahkan nama sheet sebagai label
            df_temp["Worksheet"] = ws.title
            df_list.append(df_temp)
            print(f"   📊 Added to merge list - Total sheets queued: {len(df_list)}")
            
            # Add delay antar sheet (3-5 detik untuk respect rate limit)
            time.sleep(4)

        # Validasi sebelum concat
        if not df_list:
            print("❌ No valid data sheets found to combine.")
            return pd.DataFrame()
        
        print(f"\n🔄 Combining {len(df_list)} sheets into single DataFrame...")
        
        # Gabungkan semua sheet jadi satu DataFrame dengan error handling
        try:
            df_combined = pd.concat(df_list, ignore_index=True, sort=False)
            
            # Hapus kolom duplikat yang mungkin ada
            df_combined = df_combined.loc[:, ~df_combined.columns.duplicated()]
            
            # Konversi tipe data
            df_combined = df_combined.fillna('')
            
            print(f"✅ Successfully combined all sheets!")
            print(f"🎯 Total {len(df_combined)} rows, {len(df_combined.columns)} columns")
            print(f"📋 Columns: {list(df_combined.columns)}")
            
            return df_combined
        except Exception as e:
            print(f"❌ Error during data combination: {e}")
            return pd.DataFrame()

    except Exception as e:
        print(f"❌ Unexpected error during data fetching: {e}")
        print("Pastikan file 'credentials.json' sudah benar & memiliki akses ke Spreadsheet.")
        return pd.DataFrame()

# Cache helper: get cached DataFrame or refresh
CACHE_KEY = 'aastabaya:google_sheets_df'
CACHE_TTL = 60 * 60  # 1 jam

def get_cached_sheets(refresh=False):
    """Return cached combined DataFrame. If refresh True or cache miss, refetch and store in cache."""
    if not refresh:
        try:
            df = cache.get(CACHE_KEY)
            if df is not None:
                return df
        except Exception:
            # If cache backend misconfigured, ignore and fetch fresh
            pass

    # kalau cache kosong atau refresh=True -> fetch dan simpan
    df = fetch_all_sheets_data()
    if not df.empty:
        try:
            cache.set(CACHE_KEY, df, CACHE_TTL)
        except Exception:
            # If caching backend not configured or pickling fails, ignore and return df
            pass
    return df

# Eksekusi (gunakan cache helper sehingga consumers/views dapat reuse)
df_all = get_cached_sheets()

# Preview hasil
if not df_all.empty:
    print("\n📌 First 5 rows of combined data:")
    print(df_all.head())
    print("\nℹ DataFrame Info:")
    df_all.info()
else:
    print("❌ df_all is empty, kemungkinan error saat fetching.")
