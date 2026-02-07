import requests
from bs4 import BeautifulSoup
import re
from supabase import create_client

# --- SETTINGS ---
URL = "https://www.ipowatch.in/"
S_URL = "https://blwjuzmvrvtfklthvfoz.supabase.co"
S_KEY = "sb_secret_D3eHTtrO8atdHTHIReXxXQ_gc9AnEil"

supabase = create_client(S_URL, S_KEY)

def extract_number(text):
    nums = re.findall(r'\d+', text.replace(',', ''))
    return float(nums[0]) if nums else 0

def get_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    print(f"🔄 Fetching from: {URL}")
    
    try:
        r = requests.get(URL, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # IPO Watch ki table find karna
        table = soup.find('table')
        if not table:
            print("❌ Table nahi mili!")
            return []
            
        rows = table.find_all('tr')[1:] # Header skip
        ipo_list = []
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                name = cols[0].text.strip()
                # Sirf active IPOs (jinme "IPO" likha ho)
                if "IPO" in name:
                    gmp_text = cols[2].text.strip()
                    gmp_val = extract_number(gmp_text)
                    
                    ipo_list.append({
                        "name": name,
                        "gmp": gmp_val,
                        "status": "Live",
                        "type": "Mainboard" if "SME" not in name else "SME"
                    })
        return ipo_list
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    found_ipos = get_data()
    print(f"🔎 Found {len(found_ipos)} IPOs")
    
    for ipo in found_ipos:
        try:
            # Table 'ipos' mein data push karna
            supabase.table("ipos").upsert(ipo, on_conflict="name").execute()
            print(f"✅ Synced: {ipo['name']}")
        except Exception as e:
            print(f"❌ DB Error for {ipo['name']}: {e}")
