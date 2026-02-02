import requests
from bs4 import BeautifulSoup
from supabase import create_client
import os

# Supabase Setup
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL, KEY)

def scrape_ipo_premium():
    url = "https://ipopremium.in/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sabse pehle sari tables dhoondo
        tables = soup.find_all('table')
        
        if not tables:
            print("Bhai, website par koi table nahi mili!")
            return

        # Hum pehli table ko target kar rahe hain
        target_table = tables[0]
        rows = target_table.find_all('tr')[1:] # Header skip
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                ipo_name = cols[0].get_text(strip=True)
                
                # Agar name empty nahi hai toh hi aage badho
                if ipo_name:
                    ipo_data = {
                        "name": ipo_name,
                        "gmp": cols[1].get_text(strip=True),
                        "price_band": cols[2].get_text(strip=True),
                        "subscription": cols[3].get_text(strip=True),
                        "type": "SME" if "SME" in ipo_name.upper() else "Mainboard",
                        "status": "Live"
                    }
                    
                    # Supabase Upsert
                    supabase.table("ipos").upsert(ipo_data, on_conflict="name").execute()
                    print(f"Updated: {ipo_name}")
                
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    scrape_ipo_premium()
