import requests
from bs4 import BeautifulSoup
from supabase import create_client
import os

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL, KEY)

def scrape_ipo_premium():
    url = "https://ipopremium.in/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sahi table dhoondna
        table = soup.find('table')
        if not table: return

        rows = table.find_all('tr')[1:] 
        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all('td')]
            if len(cols) >= 5:
                # Sahi Mapping:
                # 0: Name, 1: GMP, 2: Price, 3: Subscription, 4: Dates
                ipo_name = cols[0]
                ipo_data = {
                    "name": ipo_name,
                    "gmp": cols[1],
                    "price_band": cols[2],
                    "subscription": cols[3],
                    "dates": cols[4],
                    "type": "SME" if "SME" in ipo_name.upper() else "Mainboard",
                    "status": "Live" if "Live" in ipo_name.upper() else "Upcoming"
                }
                supabase.table("ipos").upsert(ipo_data, on_conflict="name").execute()
                print(f"Sahi Update: {ipo_name}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_ipo_premium()
