import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_ipo_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    # IPO Watch ka main page
    target_url = "https://ipowatch.in/"
    
    try:
        r = requests.get(target_url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # IPO Watch mein data table ke andar hota hai
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')
            # Row 1 ya 2 mein asli data hota hai
            for row in rows[1:4]:
                cols = row.find_all('td')
                if len(cols) > 0:
                    ipo_name = cols[0].text.strip()
                    # Filter out header or empty names
                    if ipo_name and "IPO Name" not in ipo_name:
                        data = {"name": ipo_name, "category": "Mainboard", "status": "Live"}
                        supabase.table("ipos").insert(data).execute()
                        print(f"🚀 Success: {ipo_name} add ho gaya!")
                        return
        else:
            print("❌ IPO Watch par table nahi mili!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_ipo_data()
