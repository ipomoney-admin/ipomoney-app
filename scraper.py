import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# GitHub Secrets se uthane ka try karega
URL = "https://khnuyrhafzppbugebjdn.supabase.co"
KEY = "sb_secret_SIb_8imA5DxLxNVK1srMDQ__xLolWEV"

supabase = create_client(URL, KEY)

# Agar variables nahi mil rahe toh yahan se error pakda jayega
if not URL or not KEY:
    print(f"DEBUG: URL length: {len(URL)}, KEY length: {len(KEY)}")
    raise ValueError("Bhai, SUPABASE_URL ya KEY GitHub Secrets mein nahi mil rahi!")

supabase = create_client(URL, KEY)

def scrape():
    url = "https://ipowala.in/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find('table')
        if not table: return
        
        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all('td')]
            if len(cols) >= 3 and "IPO" in cols[0].upper():
                ipo_data = {
                    "name": cols[0],
                    "dates": cols[1],
                    "type": "SME" if "SME" in cols[0].upper() else "Mainboard",
                    "gmp": cols[2],
                    "status": "Live",
                    "subs_total": "1.0x"
                }
                supabase.table("ipos").upsert(ipo_data, on_conflict="name").execute()
                print(f"✅ Synced: {cols[0]}")
    except Exception as e:
        print(f"❌ Scraper Error: {e}")

if __name__ == "__main__":
    scrape()
