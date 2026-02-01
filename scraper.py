import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_ipo_data():
    # Chittorgarh website se data uthana
    r = requests.get("https://www.chittorgarh.com/report/main-board-ipo-list-in-india/20/")
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Table se pehla IPO nikalna
    first_row = soup.find('table').find_all('tr')[1]
    cols = first_row.find_all('td')
    
    ipo_name = cols[0].text.strip()
    
    data = {
        "name": ipo_name,
        "category": "Mainboard",
        "status": "Live"
    }
    
    # Supabase mein bhejnah
    supabase.table("ipos").insert(data).execute()
    print(f"Success: {ipo_name} add ho gaya!")

if __name__ == "__main__":
    get_ipo_data()
