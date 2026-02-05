"""
============================================
IPO MONEY - Data Scraper
============================================
This scraper collects IPO data from multiple sources
and stores it in Supabase database.

Sources:
1. BSE India (Official announcements)
2. Fallback to manual/RSS feeds if needed

Runs every 30 minutes via GitHub Actions
============================================
"""

import requests
from bs4 import BeautifulSoup
from supabase import create_client
import os
from datetime import datetime, timedelta
import time

# ============================================
# Configuration
# ============================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Supabase credentials not found in environment variables")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Headers to avoid blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# ============================================
# Logging Function
# ============================================
def log_to_db(scraper_name, status, message, records=0):
    """Log scraper activity to database"""
    try:
        supabase.table("scraper_logs").insert({
            "scraper_name": scraper_name,
            "status": status,
            "message": message,
            "records_processed": records
        }).execute()
    except Exception as e:
        print(f"Failed to log: {e}")

# ============================================
# Helper: Parse Date
# ============================================
def parse_date(date_str):
    """Convert various date formats to YYYY-MM-DD"""
    if not date_str or date_str.strip() == "":
        return None
    
    try:
        # Try common formats
        for fmt in ["%d-%b-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
            except:
                continue
        return None
    except:
        return None

# ============================================
# Helper: Clean Text
# ============================================
def clean_text(text):
    """Remove extra spaces and newlines"""
    if not text:
        return ""
    return " ".join(text.split()).strip()

# ============================================
# Scraper 1: BSE IPO Data
# ============================================
def scrape_bse_ipos():
    """
    Scrape current IPOs from BSE India
    Note: BSE may block scrapers, this is a backup approach
    """
    print("\n[BSE] Starting BSE IPO scraper...")
    
    try:
        url = "https://www.bseindia.com/markets/PublicIssues/forthcoming_ipo.aspx"
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            log_to_db("bse_scraper", "error", f"HTTP {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # BSE structure varies, this is a basic parser
        # You may need to adjust selectors based on actual HTML
        
        ipos = []
        
        # Look for IPO table (adjust selector as needed)
        table = soup.find('table', {'id': 'ContentPlaceHolder1_GridView1'})
        
        if not table:
            print("[BSE] No table found - BSE structure may have changed")
            log_to_db("bse_scraper", "warning", "Table not found", 0)
            return []
        
        rows = table.find_all('tr')[1:]  # Skip header
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                ipo_data = {
                    "name": clean_text(cols[0].get_text()),
                    "type": "Mainboard",  # BSE is typically mainboard
                    "status": "Upcoming",
                    "open_date": parse_date(cols[1].get_text()),
                    "close_date": parse_date(cols[2].get_text()),
                    "issue_size_cr": None,  # Extract if available
                }
                
                if ipo_data["name"]:
                    ipos.append(ipo_data)
        
        print(f"[BSE] Found {len(ipos)} IPOs")
        log_to_db("bse_scraper", "success", f"Scraped {len(ipos)} IPOs", len(ipos))
        return ipos
        
    except Exception as e:
        print(f"[BSE] Error: {e}")
        log_to_db("bse_scraper", "error", str(e), 0)
        return []

# ============================================
# Scraper 2: Manual/Fallback Data
# ============================================
def get_fallback_ipos():
    """
    Fallback: Manually curated IPO list
    Update this list manually when scrapers fail
    """
    print("\n[FALLBACK] Using manual IPO data...")
    
    # You'll manually update this list when needed
    manual_ipos = [
        {
            "name": "Sample IPO Ltd",
            "type": "Mainboard",
            "status": "Upcoming",
            "open_date": "2026-02-10",
            "close_date": "2026-02-12",
            "price_band_min": 100,
            "price_band_max": 110,
            "issue_size_cr": 500,
            "lot_size": 135,
            "lead_manager": "ICICI Securities",
            "registrar": "KFintech"
        }
        # Add more manually as needed
    ]
    
    log_to_db("fallback", "success", "Using manual data", len(manual_ipos))
    return manual_ipos

# ============================================
# Database: Upsert IPO Data
# ============================================
def upsert_ipo(ipo_data):
    """
    Insert or update IPO in database
    Uses 'name' as unique identifier
    """
    try:
        # Check if IPO exists
        existing = supabase.table("ipos").select("id").eq("name", ipo_data["name"]).execute()
        
        if existing.data:
            # Update existing
            ipo_id = existing.data[0]["id"]
            result = supabase.table("ipos").update(ipo_data).eq("id", ipo_id).execute()
            print(f"  ✓ Updated: {ipo_data['name']}")
        else:
            # Insert new
            result = supabase.table("ipos").insert(ipo_data).execute()
            print(f"  ✓ Added: {ipo_data['name']}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to upsert {ipo_data.get('name', 'Unknown')}: {e}")
        return False

# ============================================
# Update Subscription Data (Placeholder)
# ============================================
def update_subscription_data():
    """
    Update live subscription data for ongoing IPOs
    
    NOTE: This requires access to NSE/BSE APIs which may be blocked.
    For MVP, subscription data will be updated manually via admin panel.
    """
    print("\n[SUBSCRIPTION] Checking for live IPOs...")
    
    try:
        # Get all live IPOs
        live_ipos = supabase.table("ipos").select("*").eq("status", "Live").execute()
        
        if not live_ipos.data:
            print("[SUBSCRIPTION] No live IPOs found")
            return
        
        # For each live IPO, try to fetch subscription data
        # This is a placeholder - implement actual API calls when available
        
        for ipo in live_ipos.data:
            print(f"  → {ipo['name']}: Subscription update pending (manual entry)")
            # TODO: Implement NSE/BSE subscription API calls here
        
    except Exception as e:
        print(f"[SUBSCRIPTION] Error: {e}")
        log_to_db("subscription_updater", "error", str(e), 0)

# ============================================
# Update IPO Status
# ============================================
def update_ipo_status():
    """
    Update IPO status based on dates
    - If open_date <= today <= close_date → Live
    - If close_date < today → Closed
    - If listing_date set → Listed
    """
    print("\n[STATUS] Updating IPO statuses...")
    
    try:
        today = datetime.now().date()
        
        # Get all IPOs
        all_ipos = supabase.table("ipos").select("*").execute()
        
        updated = 0
        for ipo in all_ipos.data:
            new_status = None
            
            # Parse dates
            open_date = datetime.strptime(ipo['open_date'], "%Y-%m-%d").date() if ipo.get('open_date') else None
            close_date = datetime.strptime(ipo['close_date'], "%Y-%m-%d").date() if ipo.get('close_date') else None
            listing_date = datetime.strptime(ipo['listing_date'], "%Y-%m-%d").date() if ipo.get('listing_date') else None
            
            # Determine status
            if listing_date:
                new_status = "Listed"
            elif open_date and close_date:
                if open_date <= today <= close_date:
                    new_status = "Live"
                elif today > close_date:
                    new_status = "Closed"
                else:
                    new_status = "Upcoming"
            
            # Update if status changed
            if new_status and new_status != ipo.get('status'):
                supabase.table("ipos").update({"status": new_status}).eq("id", ipo['id']).execute()
                print(f"  ✓ {ipo['name']}: {ipo.get('status')} → {new_status}")
                updated += 1
        
        print(f"[STATUS] Updated {updated} IPO statuses")
        log_to_db("status_updater", "success", f"Updated {updated} statuses", updated)
        
    except Exception as e:
        print(f"[STATUS] Error: {e}")
        log_to_db("status_updater", "error", str(e), 0)

# ============================================
# Main Execution
# ============================================
def main():
    """Main scraper orchestrator"""
    print("=" * 60)
    print("IPO MONEY - Data Scraper Starting")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Try to scrape BSE
    ipos = scrape_bse_ipos()
    
    # Step 2: If BSE fails, use fallback
    if not ipos:
        print("\n⚠️  Primary scrapers returned no data, using fallback...")
        ipos = get_fallback_ipos()
    
    # Step 3: Upsert all IPOs to database
    if ipos:
        print(f"\n[DATABASE] Upserting {len(ipos)} IPOs...")
        success_count = 0
        for ipo in ipos:
            if upsert_ipo(ipo):
                success_count += 1
        
        print(f"[DATABASE] Successfully processed {success_count}/{len(ipos)} IPOs")
    else:
        print("\n⚠️  No IPO data to process")
    
    # Step 4: Update subscription data for live IPOs
    update_subscription_data()
    
    # Step 5: Update IPO statuses based on dates
    update_ipo_status()
    
    print("\n" + "=" * 60)
    print("✅ Scraper completed successfully")
    print("=" * 60)

# ============================================
# Run Script
# ============================================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        log_to_db("main_scraper", "error", f"Critical: {e}", 0)
        exit(1)
