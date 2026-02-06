"""
============================================
MONEYCONTROL SCRAPER
============================================
Scrapes IPO data from MoneyControl
- IPO name, type
- Dates, price band
- Issue details
- Subscription data (if available)
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
}

def clean_text(text):
    """Remove extra whitespace"""
    if not text:
        return ""
    return " ".join(text.split()).strip()

def parse_date(date_str):
    """Convert date to YYYY-MM-DD"""
    if not date_str or date_str.strip() in ['', '-', 'NA']:
        return None
    
    try:
        # Format: "Dec 11, 2024" or "11 Dec 2024"
        for fmt in ["%b %d, %Y", "%d %b %Y", "%d-%b-%Y", "%d/%m/%Y"]:
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
    
    text = text.replace('₹', '').replace(',', '').replace('Rs', '').strip()
    match = re.search(r'[\d.]+', text)
    if match:
        try:
            return float(match.group())
        except:
            return None
    return None

def scrape_moneycontrol():
    """
    Main scraper for MoneyControl IPO page
    """
    print("\n[MONEYCONTROL] Starting scraper...")
    
    ipos = []
    
    try:
        url = "https://www.moneycontrol.com/ipo/ipo-snapshot/current-ipo-India.html"
        
        print(f"[MONEYCONTROL] Fetching: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"[MONEYCONTROL] Error: HTTP {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # MoneyControl has IPO cards/sections
        # Look for divs with IPO info
        
        # Try finding table first
        tables = soup.find_all('table')
        
        if tables:
            print(f"[MONEYCONTROL] Found {len(tables)} tables")
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows[1:]:  # Skip header
                    try:
                        cols = row.find_all('td')
                        
                        if len(cols) < 3:
                            continue
                        
                        # Extract IPO name
                        name_cell = cols[0]
                        link = name_cell.find('a')
                        
                        if link:
                            ipo_name = clean_text(link.get_text())
                        else:
                            ipo_name = clean_text(name_cell.get_text())
                        
                        if not ipo_name or len(ipo_name) < 3:
                            continue
                        
                        # Determine type
                        ipo_type = "Mainboard"
                        if "sme" in ipo_name.lower():
                            ipo_type = "SME"
                        
                        # Extract other data from remaining columns
                        col_texts = [clean_text(col.get_text()) for col in cols[1:]]
                        
                        # Try to parse dates
                        open_date = None
                        close_date = None
                        
                        for text in col_texts:
                            if '-' in text and any(month in text for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                                # Might be date range: "11-Dec to 13-Dec"
                                date_parts = text.split('to')
                                if len(date_parts) == 2:
                                    open_date = parse_date(date_parts[0].strip())
                                    close_date = parse_date(date_parts[1].strip())
                                    break
                        
                        # Extract price band
                        price_min = None
                        price_max = None
                        
                        for text in col_texts:
                            if '₹' in text or 'Rs' in text:
                                # Format: "₹100-110" or "₹100 to ₹110"
                                numbers = re.findall(r'[\d.]+', text.replace(',', ''))
                                if len(numbers) >= 2:
                                    price_min = float(numbers[0])
                                    price_max = float(numbers[1])
                                elif len(numbers) == 1:
                                    price_max = float(numbers[0])
                                break
                        
                        # Extract issue size
                        issue_size = None
                        for text in col_texts:
                            if 'cr' in text.lower():
                                issue_size = extract_number(text)
                                break
                        
                        ipo_data = {
                            "name": ipo_name,
                            "type": ipo_type,
                            "status": "Live",  # MoneyControl usually shows current IPOs
                            "open_date": open_date,
                            "close_date": close_date,
                            "price_band_min": price_min,
                            "price_band_max": price_max,
                            "issue_size_cr": issue_size,
                            "source": "moneycontrol"
                        }
                        
                        if ipo_name:
                            ipos.append(ipo_data)
                            print(f"  ✓ Extracted: {ipo_name}")
                    
                    except Exception as e:
                        print(f"  ✗ Error parsing row: {e}")
                        continue
        
        # Alternative: Look for IPO cards/divs
        if not ipos:
            print("[MONEYCONTROL] No table found, trying alternative parsing...")
            
            # Look for IPO sections
            ipo_sections = soup.find_all(['div', 'section'], class_=re.compile('ipo|issue', re.I))
            
            print(f"[MONEYCONTROL] Found {len(ipo_sections)} potential IPO sections")
            
            # Add generic parsing here if needed
        
        print(f"[MONEYCONTROL] Total IPOs extracted: {len(ipos)}")
        return ipos
    
    except Exception as e:
        print(f"[MONEYCONTROL] Error: {e}")
        return []

# ============================================
# Upcoming IPOs page
# ============================================
def scrape_moneycontrol_upcoming():
    """
    Scrape upcoming IPOs from MoneyControl
    """
    try:
        url = "https://www.moneycontrol.com/ipo/ipo-snapshot/upcoming-ipo-India.html"
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            print("[MONEYCONTROL] Upcoming IPOs page accessible")
            # Similar parsing as main function
    except:
        pass

# ============================================
# Test function
# ============================================
if __name__ == "__main__":
    print("="*60)
    print("TESTING MONEYCONTROL SCRAPER")
    print("="*60)
    
    ipos = scrape_moneycontrol()
    
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
    else:
        print("No IPOs found!")
    
    print("\n" + "="*60)
