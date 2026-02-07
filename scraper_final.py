import requests
from bs4 import BeautifulSoup
import re
from supabase import create_client

# --- SETTINGS ---
S_URL = "https://blwjuzmvrvtfklthvfoz.supabase.co"
S_KEY = "sb_secret_D3eHTtrO8atdHTHIReXxXQ_gc9AnEil"
supabase = create_client(S_URL, S_KEY)

# List of sources to try
SOURCES = [
    "https://ipowatch.in/",
    "https://ipopremium.in/",
    "https://ipowala.in/",
    "https://ipocentral.in/"
]

def extract_number(text):
    if not text: return 0
    nums = re.findall(r'\d+', text.replace(',', ''))
    return float(nums[0]) if nums else 0

def get_data_from_source(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
    try:
        print(f"🔄 Checking: {url}")
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200: return []
        
        soup = BeautifulSoup(r.text, 'html.parser')
        temp_list = []
        rows = soup.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                name = cols[0].get_text(strip=True)
                if "IPO" in name.upper() and "DATE" not in name.upper():
                    # GMP extraction logic
                    gmp_val = extract_number(cols[2].get_text(strip=True)) if len(cols) > 2 else 0
                    temp_list.append({
                        "name": name,
                        "gmp": gmp_val,
                        "status": "Live",
                        "type": "Mainboard" if "SME" not in name.upper() else "SME"
                    })
        return temp_list
    except:
        return []

if __name__ == "__main__":
    final_ipos = []
    
    # Ek-ek karke saari sites check karo jab tak data na mil jaye
    for source in SOURCES:
        data = get_data_from_source(source)
        if data:
            print(f"✅ Success! Found {len(data)} IPOs from {source}")
            final_ipos = data
            break # Data mil gaya toh aage ki sites check karne ki zaroorat nahi
    
    if not final_ipos:
        print("❌ Saari sites ne block kar diya ya data nahi mila.")
    else:
        # Sync to Supabase
        for ipo in final_ipos:
            try:
                supabase.table("ipos").upsert(ipo, on_conflict="name").execute()
                print(f"🚀 Synced: {ipo['name']}")
            except Exception as e:
                print(f"⚠️ DB Error: {e}")
