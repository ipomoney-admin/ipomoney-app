import requests
from bs4 import BeautifulSoup
import re
from supabase import create_client

# --- SETTINGS ---
# Hum seedha GMP page se data uthayenge jo sabse reliable hai
URL = "https://www.ipowatch.in/"
S_URL = "https://blwjuzmvrvtfklthvfoz.supabase.co"
# Teri Secret Key jo tune share ki thi
S_KEY = "sb_secret_D3eHTtrO8atdHTHIReXxXQ_gc9AnEil"

supabase = create_client(S_URL, S_KEY)

def extract_number(text):
    if not text: return 0
    nums = re.findall(r'\d+', text.replace(',', ''))
    return float(nums[0]) if nums else 0

def get_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    print(f"🔄 Fetching data from IPOWatch...")
    
    try:
        r = requests.get(URL, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # IPO Watch ka main data table
        table = soup.find('table')
        if not table:
            print("❌ Table nahi mili! Site structure check karo.")
            return []
            
        rows = table.find_all('tr')[1:] # Header skip karo
        ipo_list = []
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                name = cols[0].text.strip()
                # Sirf real IPO names filter karne ke liye
                if name and "IPO" in name:
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
    print(f"🔎 Total {len(found_ipos)} IPOs dhunde gaye.")
    
    for ipo in found_ipos:
        try:
            # Table 'ipos' mein data upsert ho raha hai
            supabase.table("ipos").upsert(ipo, on_conflict="name").execute()
            print(f"✅ Synced: {ipo['name']}")
        except Exception as e:
            print(f"❌ Error for {ipo['name']}: {e}")
