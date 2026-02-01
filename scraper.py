import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_ipo_data():
    # Ye headers website ko lagega ki asli browser se request aa rahi hai
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        r = requests.get("https://www.chittorgarh.com/report/main-board-ipo-list-in-india/20/", headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Is baar hum table ki ID dhoondenge jo zyada accurate hai
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')
            # Pehli kuch rows skip karke dekhte hain jahan asli data hota hai
            for row in rows[1:5]: 
                cols = row.find_all('td')
                if len(cols) > 0:
                    ipo_name = cols[0].text.strip()
                    if ipo_name and "More..." not in ipo_name:
                        data = {"name": ipo_name, "category": "Mainboard", "status": "Live"}
                        supabase.table("ipos").insert(data).execute()
                        print(f"🚀 Success: {ipo_name} add ho gaya!")
                        return # Ek naam milte hi ruk jao
        else:
            print("❌ Table nahi mili! Website ne block kiya hai.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_ipo_data()
