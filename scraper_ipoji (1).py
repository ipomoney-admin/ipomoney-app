"""
============================================
IPOJI.COM SCRAPER
============================================
Scrapes comprehensive IPO data from ipoji.com
- Current IPOs (Mainboard + SME)
- Upcoming IPOs
- GMP data
- Subscription status
- All IPO details
============================================
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
from supabase import create_client

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Database connection
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("⚠️  Supabase credentials not found - running in test mode")

def clean_text(text):
    """Remove extra whitespace"""
    if not text:
        return ""
    return " ".join(text.split()).strip()

def parse_date(date_str):
    """Convert date to YYYY-MM-DD"""
    if not date_str or date_str.strip() in ['', '-', 'NA', 'TBA', 'To be Announced']:
        return None
    
    try:
        # Common formats on ipoji.com
        for fmt in ["%b %d, %Y", "%d %b %Y", "%d-%b-%Y", "%d/%m/%Y", "%Y-%m-%d"]:
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
    
    # Remove symbols
    text = text.replace('₹', '').replace(',', '').replace('Rs', '').replace('%', '').strip()
    
    # Handle negative
    is_negative = '-' in text or '−' in text
    
    match = re.search(r'[\d.]+', text)
    if match:
        try:
            num = float(match.group())
            return -num if is_negative else num
        except:
            return None
    return None

def scrape_ipoji_current_ipos():
    """
    Scrape current IPOs from ipoji.com
    """
    print("\n[IPOJI] Starting scraper for current IPOs...")
    
    ipos = []
    
    try:
        # Current Mainboard IPOs
        url_mainboard = "https://www.ipoji.com/ipo/current-ipo"
        
        print(f"[IPOJI] Fetching: {url_mainboard}")
        response = requests.get(url_mainboard, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"[IPOJI] Error: HTTP {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find IPO cards/sections
        # IPO Ji uses div containers for each IPO
        ipo_containers = soup.find_all(['div', 'section'], class_=re.compile('ipo|card|item', re.I))
        
        print(f"[IPOJI] Found {len(ipo_containers)} potential IPO containers")
        
        # Alternative: Look for links to individual IPO pages
        ipo_links = soup.find_all('a', href=re.compile(r'/ipo/.*-ipo'))
        
        print(f"[IPOJI] Found {len(ipo_links)} IPO links")
        
        # Extract unique IPO names from links
        seen_ipos = set()
        
        for link in ipo_links:
            try:
                ipo_name = clean_text(link.get_text())
                ipo_url = link.get('href')
                
                if not ipo_name or len(ipo_name) < 3:
                    continue
                
                # Skip navigation/common text
                skip_words = ['apply', 'check', 'view', 'details', 'subscription', 'allotment', 'see', 'more', 'read', 'click']
                if any(word in ipo_name.lower() for word in skip_words):
                    continue
                
                # Avoid duplicates
                if ipo_name in seen_ipos:
                    continue
                
                seen_ipos.add(ipo_name)
                
                # Determine type
                ipo_type = "SME" if "sme" in ipo_url.lower() or "sme" in ipo_name.lower() else "Mainboard"
                
                # Try to extract more details from the card/container
                parent = link.find_parent(['div', 'section'], class_=re.compile('ipo|card', re.I))
                
                ipo_data = {
                    "name": ipo_name,
                    "type": ipo_type,
                    "status": "Live",  # Current IPO page = Live
                    "source": "ipoji"
                }
                
                if parent:
                    # Try to extract GMP
                    gmp_element = parent.find(text=re.compile(r'GMP|Premium|₹\s*\d+'))
                    if gmp_element:
                        gmp_text = clean_text(str(gmp_element))
                        gmp_value = extract_number(gmp_text)
                        if gmp_value:
                            ipo_data['gmp'] = int(gmp_value)
                    
                    # Try to extract price band
                    price_element = parent.find(text=re.compile(r'₹\s*\d+\s*-\s*₹?\s*\d+'))
                    if price_element:
                        price_text = clean_text(str(price_element))
                        prices = re.findall(r'[\d.]+', price_text.replace(',', ''))
                        if len(prices) >= 2:
                            ipo_data['price_band_min'] = float(prices[0])
                            ipo_data['price_band_max'] = float(prices[1])
                
                ipos.append(ipo_data)
                print(f"  ✓ Found: {ipo_name} ({ipo_type})")
            
            except Exception as e:
                continue
        
        # Also try SME IPOs
        url_sme = "https://www.ipoji.com/sme-ipo/current-ipo"
        
        try:
            print(f"\n[IPOJI] Fetching SME IPOs: {url_sme}")
            response_sme = requests.get(url_sme, headers=HEADERS, timeout=15)
            
            if response_sme.status_code == 200:
                soup_sme = BeautifulSoup(response_sme.text, 'html.parser')
                sme_links = soup_sme.find_all('a', href=re.compile(r'/ipo/.*-ipo'))
                
                for link in sme_links:
                    try:
                        ipo_name = clean_text(link.get_text())
                        
                        if not ipo_name or len(ipo_name) < 3 or ipo_name in seen_ipos:
                            continue
                        
                        skip_words = ['apply', 'check', 'view', 'details', 'subscription', 'allotment']
                        if any(word in ipo_name.lower() for word in skip_words):
                            continue
                        
                        seen_ipos.add(ipo_name)
                        
                        ipos.append({
                            "name": ipo_name,
                            "type": "SME",
                            "status": "Live",
                            "source": "ipoji"
                        })
                        
                        print(f"  ✓ Found SME: {ipo_name}")
                    except:
                        continue
        except Exception as e:
            print(f"[IPOJI] SME page error: {e}")
        
        print(f"\n[IPOJI] Total IPOs extracted: {len(ipos)}")
        return ipos
    
    except Exception as e:
        print(f"[IPOJI] Error: {e}")
        return []

def upsert_to_database(ipos):
    """
    Save IPOs to Supabase database
    """
    if not supabase:
        print("[DATABASE] Skipping (no Supabase connection)")
        return
    
    print("\n[DATABASE] Saving to Supabase...")
    
    success = 0
    for ipo in ipos:
        try:
            # Check if exists
            existing = supabase.table("ipos").select("id").eq("name", ipo["name"]).execute()
            
            # Add timestamp
            if ipo.get('gmp', 0) > 0:
                ipo['gmp_updated_at'] = datetime.now().isoformat()
            
            if existing.data:
                # Update
                ipo_id = existing.data[0]["id"]
                supabase.table("ipos").update(ipo).eq("id", ipo_id).execute()
                print(f"  ✓ Updated: {ipo['name']}")
            else:
                # Insert
                supabase.table("ipos").insert(ipo).execute()
                print(f"  ✓ Added: {ipo['name']}")
            
            success += 1
            
            # Log to scraper_logs
            supabase.table("scraper_logs").insert({
                "scraper_name": "ipoji",
                "status": "success",
                "message": f"Processed {ipo['name']}",
                "records_processed": 1
            }).execute()
        
        except Exception as e:
            print(f"  ✗ Failed: {ipo['name']} - {e}")
    
    print(f"[DATABASE] Saved {success}/{len(ipos)} IPOs")

def main():
    """Main function"""
    print("="*60)
    print("IPOJI.COM SCRAPER")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Scrape IPOs
    ipos = scrape_ipoji_current_ipos()
    
    if ipos:
        # Save to database
        upsert_to_database(ipos)
    else:
        print("\n⚠️  No IPOs found!")
    
    print("\n" + "="*60)
    print("✅ IPOJI scraper completed")
    print("="*60)

if __name__ == "__main__":
    main()
