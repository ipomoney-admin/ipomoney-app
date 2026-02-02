import requests
from bs4 import BeautifulSoup
from supabase import create_client
import os

# Supabase Credentials (GitHub Secrets se uthayenge)
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL, KEY)

def scrape_ipo_premium():
    # Target URL jahan GMP aur Subscription table milti hai
    url = "https://ipopremium.in/ipo-gmp-live-subscription-data-today/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Table find karna (IPO Premium usually standard tables use karta hai)
        table = soup.find('table')
        rows = table.find_all('tr')[1:] # Header skip karo
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                # Website ke column order ke hisaab se mapping
                ipo_data = {
                    "name": cols[0].get_text(strip=True),
                    "gmp": cols[1].get_text(strip=True),
                    "price_band": cols[2].get_text(strip=True),
                    "subscription": cols[3].get_text(strip=True),
                    "dates": cols[4].get_text(strip=True),
                    "type": "Mainboard" if "SME" not in cols[0].get_text() else "SME",
                    "status": "Live"
                }
                
                # Supabase mein Upsert (Duplicate nahi banega, sirf update hoga)
                supabase.table("ipos").upsert(ipo_data, on_conflict="name").execute()
                print(f"Success: {ipo_data['name']} updated.")
                
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    scrape_ipo_premium()
