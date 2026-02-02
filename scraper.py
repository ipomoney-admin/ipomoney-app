import requests
from bs4 import BeautifulSoup
from supabase import create_client
import os

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL, KEY)

def scrape_ipo_watch():
    url = "https://ipowatch.in/" 
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table: return

        # Headers dhoondna taaki sahi column se sahi data aaye
        headers_row = [th.get_text(strip=True).upper() for th in table.find_all('th')]
        rows = table.find_all('tr')[1:] 

        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all('td')]
            if len(cols) < len(headers_row): continue

            # Mapping by Header Name
            name_idx = next((i for i, h in enumerate(headers_row) if "NAME" in h), 0)
            gmp_idx = next((i for i, h in enumerate(headers_row) if "GMP" in h), 1)
            date_idx = next((i for i, h in enumerate(headers_row) if "DATE" in h), 2)
            type_idx = next((i for i, h in enumerate(headers_row) if "TYPE" in h), 3)
            price_idx = next((i for i, h in enumerate(headers_row) if "PRICE" in h), 4)

            ipo_data = {
                "name": cols[name_idx],
                "gmp": cols[gmp_idx],
                "dates": cols[date_idx],
                "type": cols[type_idx],
                "price_band": cols[price_idx],
                "status": "Upcoming" # Default status as per your DB
            }
            
            if ipo_data["name"]:
                supabase.table("ipos").upsert(ipo_data, on_conflict="name").execute()
                print(f"Verified Sync: {ipo_data['name']}")
                
    except Exception as e:
        print(f"Scraper Error: {e}")

if __name__ == "__main__":
    scrape_ipo_watch()
