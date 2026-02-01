import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# Credentials setup
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_ipo_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Aapka working URL
    target_url = "https://www.ipowatch.in/ipo-grey-market-premium-gmp-2024/"
    
    try:
        r = requests.get(target_url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find('table')
        
        if table:
            # Step 1: Purana data delete karo (Fresh start ke liye)
            supabase.table("ipos").delete().neq("name", "dummystring").execute()
            
            rows = table.find_all('tr')
            # Step 2: Loop chalao saari rows par (Pehli 15 rows tak)
            for row in rows[1:15]:
                cols = row.find_all('td')
                if len(cols) > 0:
                    ipo_name = cols[0].text.strip()
                    
                    # Garbage data filter karna
                    if ipo_name and "IPO Name" not in ipo_name and len(ipo_name) > 3:
                        payload = {
                            "name": ipo_name,
                            "category": "Mainboard",
                            "status": "Live"
                        }
                        # Step 3: Har IPO ko insert karo
                        supabase.table("ipos").insert(payload).execute()
                        print(f"✅ Added: {ipo_name}")
            
            print("🚀 Saare IPOs update ho gaye!")
        else:
            print("❌ Table nahi mili!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_ipo_data()
