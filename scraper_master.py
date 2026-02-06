"""
============================================
MASTER SCRAPER ORCHESTRATOR
============================================
Combines data from all 4 sources:
1. Chittorgarh - Main IPO data
2. Investorgain - GMP updates
3. MoneyControl - Backup data
4. IPO Premium - Comprehensive data + GMP

Merges intelligently and updates Supabase
============================================
"""

import os
import sys
from datetime import datetime
from supabase import create_client

# Import our scrapers
from scraper_chittorgarh import scrape_chittorgarh
from scraper_investorgain import scrape_investorgain_gmp
from scraper_moneycontrol import scrape_moneycontrol
from scraper_ipopremium import scrape_ipopremium

# ============================================
# Configuration
# ============================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Supabase credentials not found")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================
# Logging to Database
# ============================================
def log_scraper(scraper_name, status, message, records=0):
    """Log scraper activity"""
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
# Data Merging Logic
# ============================================
def merge_ipo_data(sources_data):
    """
    Intelligently merge IPO data from multiple sources
    Priority: IPO Premium > Chittorgarh > MoneyControl
    GMP: Investorgain > IPO Premium
    """
    merged = {}
    
    # Process each source
    for source_name, ipos in sources_data.items():
        for ipo in ipos:
            name = ipo.get('name', '').strip()
            
            if not name:
                continue
            
            # Normalize name (for matching)
            name_key = name.lower().replace('ltd', '').replace('limited', '').strip()
            
            if name_key not in merged:
                # First time seeing this IPO
                merged[name_key] = ipo.copy()
                merged[name_key]['_sources'] = [source_name]
            else:
                # Already exists, merge data
                existing = merged[name_key]
                existing['_sources'].append(source_name)
                
                # Merge logic: prefer non-null values from higher priority sources
                
                # Priority for main data: ipopremium > chittorgarh > moneycontrol
                priority = {'ipopremium': 3, 'chittorgarh': 2, 'moneycontrol': 1, 'investorgain': 1}
                
                source_priority = priority.get(source_name, 0)
                existing_priority = priority.get(existing.get('source', ''), 0)
                
                # Update fields if new source has higher priority OR if existing field is null
                for key, value in ipo.items():
                    if key == 'name':
                        continue  # Don't overwrite name
                    
                    if value is not None and value != 0 and value != '':
                        if existing.get(key) is None or existing.get(key) == 0 or existing.get(key) == '':
                            # Existing is empty, use new value
                            existing[key] = value
                        elif source_priority > existing_priority:
                            # New source has higher priority
                            existing[key] = value
                
                # Special handling for GMP: Investorgain is most reliable
                if source_name == 'investorgain':
                    if 'gmp' in ipo and ipo['gmp'] is not None:
                        existing['gmp'] = ipo['gmp']
                    if 'gmp_percentage' in ipo and ipo['gmp_percentage'] is not None:
                        existing['gmp_percentage'] = ipo['gmp_percentage']
    
    # Convert back to list
    return list(merged.values())

# ============================================
# Update Database
# ============================================
def upsert_ipo_to_db(ipo_data):
    """
    Insert or update IPO in database
    """
    try:
        # Check if exists
        existing = supabase.table("ipos").select("id").eq("name", ipo_data["name"]).execute()
        
        # Remove internal fields
        if '_sources' in ipo_data:
            del ipo_data['_sources']
        if 'source' in ipo_data:
            del ipo_data['source']
        
        # Add GMP update timestamp if GMP exists
        if ipo_data.get('gmp', 0) > 0:
            ipo_data['gmp_updated_at'] = datetime.now().isoformat()
        
        if existing.data:
            # Update existing
            ipo_id = existing.data[0]["id"]
            supabase.table("ipos").update(ipo_data).eq("id", ipo_id).execute()
            print(f"  ✓ Updated: {ipo_data['name']}")
            return True
        else:
            # Insert new
            supabase.table("ipos").insert(ipo_data).execute()
            print(f"  ✓ Added: {ipo_data['name']}")
            return True
    
    except Exception as e:
        print(f"  ✗ Failed: {ipo_data.get('name', 'Unknown')} - {e}")
        return False

# ============================================
# Update IPO Status
# ============================================
def update_ipo_statuses():
    """
    Auto-update IPO statuses based on dates
    """
    print("\n[STATUS] Updating IPO statuses...")
    
    try:
        today = datetime.now().date()
        
        all_ipos = supabase.table("ipos").select("*").execute()
        
        updated = 0
        for ipo in all_ipos.data:
            new_status = None
            
            if ipo.get('listing_date'):
                new_status = "Listed"
            elif ipo.get('open_date') and ipo.get('close_date'):
                open_date = datetime.strptime(ipo['open_date'], "%Y-%m-%d").date()
                close_date = datetime.strptime(ipo['close_date'], "%Y-%m-%d").date()
                
                if open_date <= today <= close_date:
                    new_status = "Live"
                elif today > close_date:
                    new_status = "Closed"
                else:
                    new_status = "Upcoming"
            
            if new_status and new_status != ipo.get('status'):
                supabase.table("ipos").update({"status": new_status}).eq("id", ipo['id']).execute()
                print(f"  ✓ {ipo['name']}: {ipo.get('status')} → {new_status}")
                updated += 1
        
        print(f"[STATUS] Updated {updated} statuses")
        log_scraper("status_updater", "success", f"Updated {updated} statuses", updated)
    
    except Exception as e:
        print(f"[STATUS] Error: {e}")
        log_scraper("status_updater", "error", str(e), 0)

# ============================================
# Main Execution
# ============================================
def main():
    """
    Main orchestrator function
    """
    print("="*60)
    print("IPO MONEY - MASTER SCRAPER")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Step 1: Run all scrapers
    sources_data = {}
    
    # Chittorgarh
    try:
        chittorgarh_data = scrape_chittorgarh()
        sources_data['chittorgarh'] = chittorgarh_data
        log_scraper("chittorgarh", "success", f"Scraped {len(chittorgarh_data)} IPOs", len(chittorgarh_data))
    except Exception as e:
        print(f"[CHITTORGARH] Failed: {e}")
        log_scraper("chittorgarh", "error", str(e), 0)
        sources_data['chittorgarh'] = []
    
    # Investorgain (GMP)
    try:
        investorgain_data = scrape_investorgain_gmp()
        sources_data['investorgain'] = investorgain_data
        log_scraper("investorgain", "success", f"Scraped {len(investorgain_data)} GMP entries", len(investorgain_data))
    except Exception as e:
        print(f"[INVESTORGAIN] Failed: {e}")
        log_scraper("investorgain", "error", str(e), 0)
        sources_data['investorgain'] = []
    
    # MoneyControl
    try:
        moneycontrol_data = scrape_moneycontrol()
        sources_data['moneycontrol'] = moneycontrol_data
        log_scraper("moneycontrol", "success", f"Scraped {len(moneycontrol_data)} IPOs", len(moneycontrol_data))
    except Exception as e:
        print(f"[MONEYCONTROL] Failed: {e}")
        log_scraper("moneycontrol", "error", str(e), 0)
        sources_data['moneycontrol'] = []
    
    # IPO Premium
    try:
        ipopremium_data = scrape_ipopremium()
        sources_data['ipopremium'] = ipopremium_data
        log_scraper("ipopremium", "success", f"Scraped {len(ipopremium_data)} IPOs", len(ipopremium_data))
    except Exception as e:
        print(f"[IPOPREMIUM] Failed: {e}")
        log_scraper("ipopremium", "error", str(e), 0)
        sources_data['ipopremium'] = []
    
    # Step 2: Merge data
    print("\n[MERGE] Combining data from all sources...")
    merged_ipos = merge_ipo_data(sources_data)
    
    print(f"[MERGE] Total unique IPOs: {len(merged_ipos)}")
    
    # Step 3: Update database
    if merged_ipos:
        print("\n[DATABASE] Upserting to Supabase...")
        success = 0
        for ipo in merged_ipos:
            if upsert_ipo_to_db(ipo):
                success += 1
        
        print(f"[DATABASE] Successfully processed {success}/{len(merged_ipos)} IPOs")
        log_scraper("master_scraper", "success", f"Processed {success} IPOs", success)
    else:
        print("\n⚠️  No IPO data collected from any source")
        log_scraper("master_scraper", "warning", "No data collected", 0)
    
    # Step 4: Update statuses
    update_ipo_statuses()
    
    print("\n" + "="*60)
    print("✅ Scraping completed successfully")
    print("="*60)

# ============================================
# Run
# ============================================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        log_scraper("master_scraper", "error", f"Critical: {e}", 0)
        sys.exit(1)
