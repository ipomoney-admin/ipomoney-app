import requests
from bs4 import BeautifulSoup
import re
from supabase import create_client

# --- FIXED CREDENTIALS ---
SUPABASE_URL = "https://blwjuzmvrvtfklthvfoz.supabase.co"
SUPABASE_KEY = "sb_secret_D3eHTtrO8atdHTHIReXxXQ_gc9AnEil" # Teri di hui secret key
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_number(text):
    if not text: return 0
    nums = re.findall(r'\d+', text.replace(',', ''))
    return float(nums[0]) if nums else 0

def scrape_ipoji_live():
    url = "https://www.ipoji.com/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    print("🔄 Fetching data from Ipoji...")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    ipo_list = []
    table = soup.find('table') 
    if not table:
        print("❌ Table nahi mili!")
        return []

    rows = table.find_all('tr')[1:] 
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 6:
            name = cols[0].text.strip()
            # Ipoji column structure ke hisaab se GMP (Col 5) aur Sub (Col 6)
            gmp_val = extract_number(cols[4].text)
            sub_val = extract_number(cols[5].text)
            
            ipo_data = {
                "name": name,
                "gmp": gmp_val,
                "subs_total": sub_val,
                "status": "Live" if sub_val > 0 else "Upcoming"
            }
            ipo_list.append(ipo_data)
            
    return ipo_list

def update_db(data):
    if not data:
        print("⚠️ No data to update.")
        return
    
    for ipo in data:
        try:
            # Upsert logic: Name match karega toh update, nahi toh insert
            supabase.table("ipos").upsert(ipo, on_conflict="name").execute()
            print(f"✅ Synced: {ipo['name']}")
        except Exception as e:
            print(f"❌ Error syncing {ipo['name']}: {e}")

if __name__ == "__main__":
    live_data = scrape_ipoji_live()
    update_db(live_data)
    print("\n🚀 Sab kuch set hai! Database check karo.")
