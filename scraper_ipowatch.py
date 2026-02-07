"""
============================================
IPOWATCH.IN SCRAPER
============================================
Scrapes IPO data from ipowatch.in
- Current & Upcoming IPOs
- Mainboard & SME
- Price bands, dates, issue size
============================================
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def clean_text(text):
    if not text:
        return ""
    return " ".join(text.split()).strip()

def parse_date(date_str):
    if not date_str or date_str.strip() in ['', '-', 'TBA']:
        return None
    
    try:
        for fmt in ["%b %d, %Y", "%d %b %Y", "%d-%b-%Y", "%d/%m/%Y"]:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
            except:
                continue
    except:
        pass
    return None

def extract_number(text):
    if not text:
        return None
    text = text.replace('₹', '').replace(',', '').strip()
    match = re.search(r'[\d.]+', text)
    return float(match.group()) if match else None

def scrape_ipowatch():
    """Scrape IPOWatch.in"""
    print("\n[IPOWATCH] Starting scraper...")
    
    ipos = []
    
    try:
        url = "https://ipowatch.in/"
        print(f"[IPOWATCH] Fetching: {url}")
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"[IPOWATCH] Error: HTTP {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find IPO table
        table = soup.find('table')
        
        if not table:
            print("[IPOWATCH] No table found")
            return []
        
        rows = table.find_all('tr')[1:]  # Skip header
        print(f"[IPOWATCH] Found {len(rows)} rows")
        
        for row in rows:
            try:
                cols = row.find_all('td')
                
                if len(cols) < 5:
                    continue
                
                ipo_name = clean_text(cols[0].get_text())
                
                if not ipo_name or len(ipo_name) < 3:
                    continue
                
                # Determine type
                ipo_type = "SME" if "sme" in ipo_name.lower() else "Mainboard"
                
                # Extract data
                dates_text = clean_text(cols[1].get_text()) if len(cols) > 1 else ""
                type_text = clean_text(cols[2].get_text()) if len(cols) > 2 else ""
                size_text = clean_text(cols[3].get_text()) if len(cols) > 3 else ""
                price_text = clean_text(cols[4].get_text()) if len(cols) > 4 else ""
                
                # Parse price band
                price_min = None
                price_max = None
                if price_text:
                    prices = re.findall(r'[\d.]+', price_text.replace(',', ''))
                    if len(prices) >= 2:
                        price_min = float(prices[0])
                        price_max = float(prices[1])
                
                # Extract issue size
                issue_size = extract_number(size_text)
                
                ipo_data = {
                    "name": ipo_name,
                    "type": ipo_type,
                    "status": "Upcoming",
                    "price_band_min": price_min,
                    "price_band_max": price_max,
                    "issue_size_cr": issue_size,
                    "source": "ipowatch"
                }
                
                ipos.append(ipo_data)
                print(f"  ✓ {ipo_name}")
            
            except Exception as e:
                continue
        
        print(f"[IPOWATCH] Total: {len(ipos)} IPOs")
        return ipos
    
    except Exception as e:
        print(f"[IPOWATCH] Error: {e}")
        return []

if __name__ == "__main__":
    ipos = scrape_ipowatch()
    for ipo in ipos:
        print(f"{ipo['name']} - {ipo['type']}")
