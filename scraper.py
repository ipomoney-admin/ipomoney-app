import requests
from bs4 import BeautifulSoup
from supabase import create_client
import os

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL, KEY)

def scrape_ipo_watch():
    # Locked URL: No extra paths
    url = "https://ipowatch.in/" 
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table: return

        rows = table.find_all('tr')[1:] 
        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all('td')]
            if len(cols) >= 5:
                # Mapping as per your feedback:
                ipo_data = {
                    "name": cols[0],          
                    "gmp": cols[1],           
                    "dates": cols[2],         
                    "type": cols[3],          
                    "price_band": cols[4],    
                    "status": "Upcoming"      
                }
                supabase.table("ipos").upsert(ipo_data, on_conflict="name").execute()
                print(f"Done: {cols[0]}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_ipo_watch()
