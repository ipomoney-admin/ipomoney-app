"""
============================================
INVESTORGAIN SCRAPER
============================================
Scrapes GMP (Grey Market Premium) data
- IPO name
- GMP value (₹)
- GMP percentage (%)
- Latest update time
============================================
"""

import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.investorgain.com/',
}

def clean_text(text):
    """Remove extra whitespace"""
    if not text:
        return ""
    return " ".join(text.split()).strip()

def extract_number(text):
    """Extract number from text, handling negatives"""
    if not text:
        return None
    
    # Remove currency symbols, commas, % signs
    text = text.replace('₹', '').replace(',', '').replace('%', '').strip()
    
    # Check for negative
    is_negative = '-' in text or '−' in text
    
    # Extract number
    match = re.search(r'[\d.]+', text)
    if match:
        try:
            num = float(match.group())
            return -num if is_negative else num
        except:
            return None
    return None

def scrape_investorgain_gmp():
    """
    Scrape GMP data from Investorgain
    Returns list of GMP dictionaries
    """
    print("\n[INVESTORGAIN] Starting GMP scraper...")
    
    gmp_data = []
    
    try:
        url = "https://www.investorgain.com/report/live-ipo-gmp/331/"
        
        print(f"[INVESTORGAIN] Fetching: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"[INVESTORGAIN] Error: HTTP {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Investorgain uses multiple tables
        # Look for table with GMP data
        tables = soup.find_all('table')
        
        print(f"[INVESTORGAIN] Found {len(tables)} tables")
        
        for table_idx, table in enumerate(tables):
            try:
                # Check if this table has GMP-related headers
                headers = table.find_all('th')
                header_text = ' '.join([th.get_text().lower() for th in headers])
                
                if 'gmp' not in header_text and 'premium' not in header_text:
                    continue
                
                print(f"[INVESTORGAIN] Processing table {table_idx + 1}...")
                
                rows = table.find_all('tr')
                
                for row in rows[1:]:  # Skip header
                    try:
                        cols = row.find_all('td')
                        
                        if len(cols) < 3:
                            continue
                        
                        # First column usually has IPO name
                        ipo_name = clean_text(cols[0].get_text())
                        
                        # Skip if name is too short or contains unwanted text
                        if not ipo_name or len(ipo_name) < 3:
                            continue
                        
                        if 'mainboard' in ipo_name.lower() or 'sme' in ipo_name.lower():
                            # This might be a section header, skip
                            continue
                        
                        # Look for GMP value (₹)
                        gmp_value = None
                        gmp_percentage = None
                        
                        for col in cols[1:]:
                            text = col.get_text()
                            
                            # Look for ₹ symbol (GMP in rupees)
                            if '₹' in text or 'rs' in text.lower():
                                gmp_value = extract_number(text)
                            
                            # Look for % symbol (GMP percentage)
                            if '%' in text:
                                gmp_percentage = extract_number(text)
                        
                        # If we found GMP data, add it
                        if gmp_value is not None or gmp_percentage is not None:
                            gmp_entry = {
                                "name": ipo_name,
                                "gmp": int(gmp_value) if gmp_value is not None else 0,
                                "gmp_percentage": round(gmp_percentage, 2) if gmp_percentage is not None else 0,
                                "source": "investorgain"
                            }
                            
                            gmp_data.append(gmp_entry)
                            print(f"  ✓ {ipo_name}: GMP ₹{gmp_value} ({gmp_percentage}%)")
                    
                    except Exception as e:
                        print(f"  ✗ Error parsing row: {e}")
                        continue
            
            except Exception as e:
                print(f"[INVESTORGAIN] Error processing table: {e}")
                continue
        
        # Remove duplicates (keep first occurrence)
        seen_names = set()
        unique_gmp_data = []
        for entry in gmp_data:
            if entry['name'] not in seen_names:
                seen_names.add(entry['name'])
                unique_gmp_data.append(entry)
        
        print(f"[INVESTORGAIN] Total GMP entries: {len(unique_gmp_data)}")
        return unique_gmp_data
    
    except Exception as e:
        print(f"[INVESTORGAIN] Error: {e}")
        return []

# ============================================
# Alternative: Scrape from different page
# ============================================
def scrape_investorgain_mainboard():
    """
    Alternate scraper for mainboard IPO page
    """
    try:
        url = "https://www.investorgain.com/report/live-ipo/mainboard-ipo/331/ipo.html"
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            # Similar parsing logic as above
            print("[INVESTORGAIN] Mainboard page accessible")
            # Add parsing here if needed
    except:
        pass

# ============================================
# Test function
# ============================================
if __name__ == "__main__":
    print("="*60)
    print("TESTING INVESTORGAIN GMP SCRAPER")
    print("="*60)
    
    gmp_data = scrape_investorgain_gmp()
    
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    
    if gmp_data:
        for i, entry in enumerate(gmp_data, 1):
            print(f"\n{i}. {entry['name']}")
            print(f"   GMP: ₹{entry['gmp']}")
            print(f"   GMP %: {entry['gmp_percentage']}%")
    else:
        print("No GMP data found!")
    
    print("\n" + "="*60)
