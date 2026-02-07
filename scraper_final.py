import requests
from bs4 import BeautifulSoup
import re
from supabase import create_client

# --- SETTINGS ---
URL = "https://ipowatch.in/"
S_URL = "https://blwjuzmvrvtfklthvfoz.supabase.co"
S_KEY = "sb_secret_D3eHTtrO8atdHTHIReXxXQ_gc9AnEil"

supabase = create_client(S_URL, S_KEY)

def extract_number(text):
    if not text: return 0
    nums = re.findall(r'\d+', text.replace(',', ''))
    return float(nums[0]) if nums else 0

def get_data():
    # User-Agent taaki ipowatch.in ko lage ki real user hai
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    print(f"🔄 Fetching data from {URL}...")
    
    try:
        r = requests.get(URL, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # ipowatch.in ke saare tables scan karo
        tables = soup.find_all('table')
        ipo_list = []
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    name = cols[0].text.strip()
                    # Sirf un rows ko lo jisme "IPO" likha ho
                    if "IPO" in name.upper() and "DATE" not in name.upper():
                        # GMP aksar 2nd ya 3rd column mein hota hai
                        gmp_val = extract_number(cols[1].text) if len(cols) > 1 else 0
                        
                        ipo_list.append({
                            "name": name,
                            "gmp": gmp_val,
                            "status": "Live",
                            "type": "Mainboard" if "SME" not in name.upper() else "SME"
                        })
        
        # Duplicate names remove karo
        unique_data = {v['name']: v for v in ipo_list}.values()
        return list(unique_data)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    found_ipos = get_data()
    print(f"🔎 Total {len(found_ipos)} IPOs dhunde gaye.")
    
    for ipo in found_ipos:
        try:
            supabase.table("ipos").upsert(ipo, on_conflict="name").execute()
            print(f"✅ Synced: {ipo['name']}")
        except Exception as e:
            print(f"❌ DB Sync Error: {e}")
