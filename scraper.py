import os
import requests
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_ipo_data():
    # Seedha API hit karenge (No HTML, No Tables)
    api_url = "https://www.chittorgarh.com/services/static/report/main-board-ipo-list-in-india/20/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.get(api_url, headers=headers, timeout=15)
        # Agar JSON mil gaya toh lottery lag gayi
        if r.status_code == 200:
            data_list = r.json()
            if data_list and len(data_list) > 0:
                # Pehla IPO nikalna
                ipo_name = data_list[0].get('issuer_company_name', 'Unknown IPO')
                
                payload = {"name": ipo_name, "category": "Mainboard", "status": "Live"}
                supabase.table("ipos").insert(payload).execute()
                print(f"🚀 Success: {ipo_name} add ho gaya!")
            else:
                print("❌ Data khali mila!")
        else:
            # Plan B: Simple Scraper for a very basic site
            print(f"❌ API fail: {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_ipo_data()
