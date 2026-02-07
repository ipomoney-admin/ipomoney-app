import requests
from bs4 import BeautifulSoup
import os
from supabase import create_client

# Supabase Setup (Aapke environment variables se lega)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def scrape_ipoji_live():
    url = "https://www.ipoji.com/" # Main page jahan saare live IPOs hote hain
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    ipo_list = []
    
    # Ipoji ke table rows ko target karna (Logic based on their structure)
    table = soup.find('table') # Unka main data table
    rows = table.find_all('tr')[1:] # First row header hoti hai
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 5:
            name = cols[0].text.strip()
            # Yahan hum GMP aur Subscription extract karenge
            gmp_text = cols[4].text.strip() # Example column index
            sub_text = cols[5].text.strip() # Example column index
            
            ipo_data = {
                "name": name,
                "gmp": extract_number(gmp_text),
                "subs_total": extract_number(sub_text),
                "status": "Live", # Defaulting to live for this scraper
                "updated_at": "now()"
            }
            ipo_list.append(ipo_data)
            
    return ipo_list

def extract_number(text):
    # Text se sirf numbers nikalne ka logic (e.g., "₹50 (20%)" -> 50)
    import re
    nums = re.findall(r'\d+', text.replace(',', ''))
    return float(nums[0]) if nums else 0

# Database Update Logic
def update_db(data):
    for ipo in data:
        supabase.table("ipos").upsert(ipo, on_conflict="name").execute()
    print(f"✅ Updated {len(data)} IPOs from Ipoji")

if __name__ == "__main__":
    data = scrape_ipoji_live()
    update_db(data)
