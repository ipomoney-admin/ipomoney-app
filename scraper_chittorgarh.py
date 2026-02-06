"""
============================================
CHITTORGARH SCRAPER
============================================
Scrapes IPO data from Chittorgarh.com
- IPO name, type (Mainboard/SME)
- Dates (open, close, allotment, listing)
- Price band, lot size, issue size
- Subscription data
============================================
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

def clean_text(text):
    """Remove extra whitespace and newlines"""
    if not text:
        return ""
    return " ".join(text.split()).strip()

def parse_date(date_str):
    """Convert date string to YYYY-MM-DD format"""
    if not date_str or date_str.strip() in ['', '-', 'TBA', 'To be announced']:
        return None
    
    try:
        # Try format: "Dec 11, 2024"
        date_obj = datetime.strptime(date_str.strip(), "%b %d, %Y")
        return date_obj.strftime("%Y-%m-%d")
    except:
        pass
    
    try:
        # Try format: "11-Dec-2024"
        date_obj = datetime.strptime(date_str.strip(), "%d-%b-%Y")
        return date_obj.strftime("%Y-%m-%d")
    except:
        pass
    
    try:
        # Try format: "11/12/2024"
        date_obj = datetime.strptime(date_str.strip(), "%d/%m/%Y")
        return date_obj.strftime("%Y-%m-%d")
    except:
        pass
    
    return None

def extract_number(text):
    """Extract number from text like '₹500 Cr' or '135 shares'"""
    if not text:
        return None
    
    # Remove currency symbols and commas
    text = text.replace('₹', '').replace(',', '').strip()
    
    # Extract first number found
    match = re.search(r'[\d.]+', text)
    if match:
        try:
            return float(match.group())
        except:
            return None
    return None

def scrape_chittorgarh():
    """
    Main scraper function for Chittorgarh
    Returns list of IPO dictionaries
    """
    print("\n[CHITTORGARH] Starting scraper...")
    
    ipos = []
    
    # URLs to scrape
    urls = [
        ("https://www.chittorgarh.com/ipo/ipo_current.asp", "Live"),
        ("https://www.chittorgarh.com/ipo/ipo_forthcoming.asp", "Upcoming"),
    ]
    
    for url, default_status in urls:
        try:
            print(f"[CHITTORGARH] Fetching: {url}")
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code != 200:
                print(f"[CHITTORGARH] Error: HTTP {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find IPO table
            # Chittorgarh uses table with class 'table table-bordered'
            table = soup.find('table', {'class': 'table'})
            
            if not table:
                print(f"[CHITTORGARH] No table found on {url}")
                continue
            
            rows = table.find_all('tr')[1:]  # Skip header row
            
            print(f"[CHITTORGARH] Found {len(rows)} rows")
            
            for row in rows:
                try:
                    cols = row.find_all('td')
                    
                    if len(cols) < 5:
                        continue
                    
                    # Extract IPO name (usually first column with link)
                    name_cell = cols[0].find('a')
                    if not name_cell:
                        name_cell = cols[0]
                    
                    ipo_name = clean_text(name_cell.get_text())
                    
                    if not ipo_name or len(ipo_name) < 3:
                        continue
                    
                    # Determine type (Mainboard vs SME)
                    ipo_type = "Mainboard"
                    if "sme" in ipo_name.lower() or "sme" in row.get_text().lower():
                        ipo_type = "SME"
                    
                    # Extract dates (columns vary, so we look for date patterns)
                    dates_text = [clean_text(col.get_text()) for col in cols[1:4]]
                    open_date = parse_date(dates_text[0]) if len(dates_text) > 0 else None
                    close_date = parse_date(dates_text[1]) if len(dates_text) > 1 else None
                    
                    # Extract price band (look for ₹ symbol)
                    price_text = ""
                    for col in cols:
                        text = col.get_text()
                        if '₹' in text or 'Rs' in text:
                            price_text = clean_text(text)
                            break
                    
                    price_min = None
                    price_max = None
                    if price_text:
                        # Format: "₹100 to ₹110" or "₹100-110"
                        prices = re.findall(r'[\d.]+', price_text.replace(',', ''))
                        if len(prices) >= 2:
                            price_min = float(prices[0])
                            price_max = float(prices[1])
                        elif len(prices) == 1:
                            price_max = float(prices[0])
                    
                    # Extract issue size (look for 'Cr' or 'crore')
                    issue_size = None
                    for col in cols:
                        text = col.get_text()
                        if 'cr' in text.lower() or 'crore' in text.lower():
                            issue_size = extract_number(text)
                            break
                    
                    # Extract lot size
                    lot_size = None
                    for col in cols:
                        text = col.get_text()
                        if 'share' in text.lower() or 'lot' in text.lower():
                            lot_size = int(extract_number(text)) if extract_number(text) else None
                            break
                    
                    # Build IPO object
                    ipo_data = {
                        "name": ipo_name,
                        "type": ipo_type,
                        "status": default_status,
                        "open_date": open_date,
                        "close_date": close_date,
                        "price_band_min": price_min,
                        "price_band_max": price_max,
                        "issue_size_cr": issue_size,
                        "lot_size": lot_size,
                        "source": "chittorgarh"
                    }
                    
                    # Only add if we have at least name and one other field
                    if ipo_name and (open_date or price_max or issue_size):
                        ipos.append(ipo_data)
                        print(f"  ✓ Extracted: {ipo_name}")
                
                except Exception as e:
                    print(f"  ✗ Error parsing row: {e}")
                    continue
        
        except Exception as e:
            print(f"[CHITTORGARH] Error fetching {url}: {e}")
            continue
    
    print(f"[CHITTORGARH] Total IPOs extracted: {len(ipos)}")
    return ipos

# ============================================
# Test function (run directly)
# ============================================
if __name__ == "__main__":
    print("="*60)
    print("TESTING CHITTORGARH SCRAPER")
    print("="*60)
    
    ipos = scrape_chittorgarh()
    
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    
    if ipos:
        for i, ipo in enumerate(ipos, 1):
            print(f"\n{i}. {ipo['name']}")
            print(f"   Type: {ipo['type']}")
            print(f"   Status: {ipo['status']}")
            print(f"   Dates: {ipo['open_date']} to {ipo['close_date']}")
            print(f"   Price: ₹{ipo['price_band_min']} - ₹{ipo['price_band_max']}")
            print(f"   Issue Size: ₹{ipo['issue_size_cr']} Cr")
            print(f"   Lot Size: {ipo['lot_size']} shares")
    else:
        print("No IPOs found!")
    
    print("\n" + "="*60)
