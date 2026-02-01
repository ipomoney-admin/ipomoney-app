import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_ipo_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Moneycontrol ka IPO page
    target_url = "https://www.moneycontrol.com/ipo/forthcoming-ipos.html"
    
    try:
        r = requests.get(target_url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Moneycontrol ki table find karna
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')
            if len(rows) > 1:
                # First data row
                cols = rows[1].find_all('td')
                ipo_name = cols[0].text.strip()
                
                data = {"name": ipo_name, "category": "Mainboard", "status": "Upcoming"}
                supabase.table("ipos").insert(data).execute()
                print(f"🚀 Success: {ipo_name} add ho gaya!")
        else:
            print("❌ Moneycontrol par bhi table nahi mili!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_ipo_data()
