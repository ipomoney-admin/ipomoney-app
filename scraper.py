import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# Environment variables se credentials uthana
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_ipo_data():
    # Website ko lage ki ye ek browser hai, isliye headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Chittorgarh IPO report page
        response = requests.get("https://www.chittorgarh.com/report/main-board-ipo-list-in-india/20/", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Table find karna jisme 'table' class ho
        table = soup.find('table', {'class': 'table'})
        
        if table:
            # Saari rows nikalna
            rows = table.find_all('tr')
            
            # Row 0 header hai, Row 1 pehla IPO hai
            if len(rows) > 1:
                cols = rows[1].find_all('td')
                
                # Pehla column company ka naam hota hai
                ipo_name = cols[0].text.strip()
                
                # Supabase ke liye data packet
                data = {
                    "name": ipo_name,
                    "category": "Mainboard",
                    "status": "Live"
                }
                
                # Purana data clear karke naya insert karna (Optional, but testing ke liye best)
                # supabase.table("ipos").delete().neq("id", 0).execute() 
                
                # Naya data bhejnah
                supabase.table("ipos").insert(data).execute()
                print(f"🚀 Success: {ipo_name} Supabase mein add ho gaya!")
        else:
            print("❌ Error: Website par table nahi mili.")
            
    except Exception as e:
        print(f"❌ Kuch gadbad hui: {e}")

if __name__ == "__main__":
    get_ipo_data()
