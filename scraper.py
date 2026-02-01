import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_ipo_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get("https://www.chittorgarh.com/report/main-board-ipo-list-in-india/20/", headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Table dhundne ka naya tarika
    table = soup.find('table', {'class': 'table'})
    
    if table:
        rows = table.find_all('tr')
        if len(rows) > 1:
            cols = rows[1].find_all('td')
            ipo_name = cols[0].text.strip()
            
            data = {"name": ipo_name, "category": "Mainboard", "status": "Live"}
            supabase.table("ipos").insert(data).execute()
            print(f"Success: {ipo_name} add ho gaya!")
    else:
        print("Table nahi mili bhai!")

if __name__ == "__main__":
    get_ipo_data()
