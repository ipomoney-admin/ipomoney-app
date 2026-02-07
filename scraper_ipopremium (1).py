"""
============================================
IPO PREMIUM SCRAPER
============================================
Scrapes IPO data from IPOPremium.in
- IPO name, type
- GMP data
- Dates, price band, lot size
- Subscription data
- Lead manager, registrar
============================================
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def clean_text(text):
    """Remove extra whitespace"""
    if not text:
        return ""
    return " ".join(text.split()).strip()

def parse_date(date_str):
    """Convert date to YYYY-MM-DD"""
    if not date_str or date_str.strip() in ['', '-', 'NA', 'TBA']:
        return None
    
    try:
        for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%b %d, %Y"]:
            try:
                date_obj = datetime.strptime(date_str.strip(), fmt)
                return date_obj.strftime("%Y-%m-%d")
            except:
                continue
    except:
        pass
    
    return None

def extract_number(text):
    """Extract number from text"""
    if not text:
        return None
    
    # Remove common symbols
    text = text.replace('₹', '').replace(',', '').replace('Rs', '').replace('%', '').strip()
    
    # Handle negative numbers
    is_negative = '-' in text or '−' in text
    
    match = re.search(r'[\d.]+', text)
    if match:
        try:
            num = float(match.group())
            return -num if is_negative else num
        except:
            return None
    return None

def scrape_ipopremium():
    """
    Main scraper for IPO Premium
    """
    print("\n[IPOPREMIUM] Starting scraper...")
    
    ipos = []
    
    try:
        url = "https://www.ipopremium.in/"
        
        print(f"[IPOPREMIUM] Fetching: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"[IPOPREMIUM] Error: HTTP {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # IPO Premium shows data in a table
        table = soup.find('table')
        
        if not table:
            print("[IPOPREMIUM] No table found")
            return []
        
        # Get headers to identify columns
        headers = []
        header_row = table.find('tr')
        if header_row:
            headers = [clean_text(th.get_text()).lower() for th in header_row.find_all(['th', 'td'])]
            print(f"[IPOPREMIUM] Table headers: {headers}")
        
        # Find column indices
        name_idx = next((i for i, h in enumerate(headers) if 'company' in h or 'name' in h), 0)
        gmp_idx = next((i for i, h in enumerate(headers) if 'gmp' in h), -1)
        open_idx = next((i for i, h in enumerate(headers) if 'open' in h), -1)
        close_idx = next((i for i, h in enumerate(headers) if 'close' in h), -1)
        price_idx = next((i for i, h in enumerate(headers) if 'price' in h), -1)
        lot_idx = next((i for i, h in enumerate(headers) if 'lot' in h), -1)
        size_idx = next((i for i, h in enumerate(headers) if 'issue' in h or 'size' in h), -1)
        
        rows = table.find_all('tr')[1:]  # Skip header
        
        print(f"[IPOPREMIUM] Found {len(rows)} data rows")
        
        for row in rows:
            try:
                cols = row.find_all('td')
                
                if len(cols) < 3:
                    continue
                
                # Extract IPO name (first column usually has link)
                name_cell = cols[0]
                link = name_cell.find('a')
                ipo_name = clean_text(link.get_text() if link else name_cell.get_text())
                
                if not ipo_name or len(ipo_name) < 3:
                    continue
                
                # Skip header-like rows
                if 'company' in ipo_name.lower() or 'name' in ipo_name.lower():
                    continue
                
                # Determine type from row class or context
                ipo_type = "Mainboard"
                row_class = row.get('class', [])
                if any('sme' in str(c).lower() for c in row_class):
                    ipo_type = "SME"
                
                # Extract GMP
                gmp = 0
                gmp_percentage = 0
                
                if gmp_idx >= 0 and gmp_idx < len(cols):
                    gmp_text = clean_text(cols[gmp_idx].get_text())
                    
                    # Check for both ₹ and % in same cell
                    if '₹' in gmp_text or 'rs' in gmp_text.lower():
                        gmp = extract_number(gmp_text)
                    
                    if '%' in gmp_text:
                        gmp_percentage = extract_number(gmp_text.replace('₹', ''))
                
                # Extract dates
                open_date = None
                close_date = None
                
                if open_idx >= 0 and open_idx < len(cols):
                    open_date = parse_date(clean_text(cols[open_idx].get_text()))
                
                if close_idx >= 0 and close_idx < len(cols):
                    close_date = parse_date(clean_text(cols[close_idx].get_text()))
                
                # Extract price band
                price_min = None
                price_max = None
                
                if price_idx >= 0 and price_idx < len(cols):
                    price_text = clean_text(cols[price_idx].get_text())
                    numbers = re.findall(r'[\d.]+', price_text.replace(',', ''))
                    
                    if len(numbers) >= 2:
                        price_min = float(numbers[0])
                        price_max = float(numbers[1])
                    elif len(numbers) == 1:
                        price_max = float(numbers[0])
                
                # Extract lot size
                lot_size = None
                if lot_idx >= 0 and lot_idx < len(cols):
                    lot_size = int(extract_number(cols[lot_idx].get_text())) if extract_number(cols[lot_idx].get_text()) else None
                
                # Extract issue size
                issue_size = None
                if size_idx >= 0 and size_idx < len(cols):
                    issue_text = clean_text(cols[size_idx].get_text())
                    issue_size = extract_number(issue_text)
                
                # Determine status based on dates
                status = "Upcoming"
                today = datetime.now().date()
                
                if open_date and close_date:
                    open_dt = datetime.strptime(open_date, "%Y-%m-%d").date()
                    close_dt = datetime.strptime(close_date, "%Y-%m-%d").date()
                    
                    if open_dt <= today <= close_dt:
                        status = "Live"
                    elif today > close_dt:
                        status = "Closed"
                
                ipo_data = {
                    "name": ipo_name,
                    "type": ipo_type,
                    "status": status,
                    "open_date": open_date,
                    "close_date": close_date,
                    "price_band_min": price_min,
                    "price_band_max": price_max,
                    "issue_size_cr": issue_size,
                    "lot_size": lot_size,
                    "gmp": int(gmp) if gmp else 0,
                    "gmp_percentage": round(gmp_percentage, 2) if gmp_percentage else 0,
                    "source": "ipopremium"
                }
                
                if ipo_name:
                    ipos.append(ipo_data)
                    print(f"  ✓ {ipo_name} | GMP: ₹{gmp} ({gmp_percentage}%)")
            
            except Exception as e:
                print(f"  ✗ Error parsing row: {e}")
                continue
        
        print(f"[IPOPREMIUM] Total IPOs extracted: {len(ipos)}")
        return ipos
    
    except Exception as e:
        print(f"[IPOPREMIUM] Error: {e}")
        return []

# ============================================
# Alternative: API endpoint (if available)
# ============================================
def scrape_ipopremium_api():
    """
    Try to access IPO Premium API (if they have one)
    """
    try:
        # Some sites expose JSON endpoints
        api_url = "https://www.ipopremium.in/api/ipos"  # Example - may not exist
        
        response = requests.get(api_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("[IPOPREMIUM] API endpoint found!")
            return data
    except:
        pass
    
    return None

# ============================================
# Test function
# ============================================
if __name__ == "__main__":
    print("="*60)
    print("TESTING IPO PREMIUM SCRAPER")
    print("="*60)
    
    ipos = scrape_ipopremium()
    
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
            print(f"   Lot Size: {ipo['lot_size']}")
            print(f"   GMP: ₹{ipo['gmp']} ({ipo['gmp_percentage']}%)")
    else:
        print("No IPOs found!")
    
    print("\n" + "="*60)
