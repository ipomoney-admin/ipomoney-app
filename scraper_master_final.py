"""
============================================
MASTER SCRAPER - FINAL VERSION
============================================
Combines 3 reliable sources:
1. ipoji.com
2. ipowatch.in
3. ipopremium.in

Merges data intelligently and updates database
============================================
"""

import os
import sys
from datetime import datetime
from supabase import create_client

# Import scrapers
from scraper_ipoji import scrape_ipoji_current_ipos
from scraper_ipowatch import scrape_ipowatch
from scraper_ipopremium import scrape_ipopremium

# Database
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Supabase credentials missing")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def log_scraper(name, status, message, records=0):
    try:
        supabase.table("scraper_logs").insert({
            "scraper_name": name,
            "status": status,
            "message": message,
            "records_processed": records
        }).execute()
    except:
        pass

def merge_ipo_data(sources):
    """Merge IPO data from multiple sources"""
    merged = {}
    
    for source_name, ipos in sources.items():
        for ipo in ipos:
            name = ipo.get('name', '').strip()
            if not name:
                continue
            
            # Normalize name for matching
            key = name.lower().replace('ltd', '').replace('limited', '').strip()
            
            if key not in merged:
                merged[key] = ipo.copy()
                merged[key]['_sources'] = [source_name]
            else:
                existing = merged[key]
                existing['_sources'].append(source_name)
                
                # Merge: prefer non-null values
                for k, v in ipo.items():
                    if v and (not existing.get(k) or existing.get(k) == 0):
                        existing[k] = v
    
    return list(merged.values())

def upsert_ipo(ipo_data):
    """Insert or update IPO in database"""
    try:
        # Remove internal fields
        if '_sources' in ipo_data:
            del ipo_data['_sources']
        if 'source' in ipo_data:
            del ipo_data['source']
        
        # Check if exists
        existing = supabase.table("ipos").select("id").eq("name", ipo_data["name"]).execute()
        
        # Add GMP timestamp
        if ipo_data.get('gmp', 0) > 0:
            ipo_data['gmp_updated_at'] = datetime.now().isoformat()
        
        if existing.data:
            # Update
            ipo_id = existing.data[0]["id"]
            supabase.table("ipos").update(ipo_data).eq("id", ipo_id).execute()
            print(f"  ✓ Updated: {ipo_data['name']}")
        else:
            # Insert
            supabase.table("ipos").insert(ipo_data).execute()
            print(f"  ✓ Added: {ipo_data['name']}")
        
        return True
    except Exception as e:
        print(f"  ✗ Failed: {ipo_data.get('name')} - {e}")
        return False

def update_statuses():
    """Update IPO statuses based on dates"""
    print("\n[STATUS] Updating...")
    
    try:
        today = datetime.now().date()
        all_ipos = supabase.table("ipos").select("*").execute()
        
        updated = 0
        for ipo in all_ipos.data:
            new_status = None
            
            if ipo.get('listing_date'):
                new_status = "Listed"
            elif ipo.get('open_date') and ipo.get('close_date'):
                try:
                    open_date = datetime.strptime(ipo['open_date'], "%Y-%m-%d").date()
                    close_date = datetime.strptime(ipo['close_date'], "%Y-%m-%d").date()
                    
                    if open_date <= today <= close_date:
                        new_status = "Live"
                    elif today > close_date:
                        new_status = "Closed"
                    else:
                        new_status = "Upcoming"
                except:
                    pass
            
            if new_status and new_status != ipo.get('status'):
                supabase.table("ipos").update({"status": new_status}).eq("id", ipo['id']).execute()
                print(f"  ✓ {ipo['name']}: {ipo.get('status')} → {new_status}")
                updated += 1
        
        print(f"[STATUS] Updated {updated} statuses")
    except Exception as e:
        print(f"[STATUS] Error: {e}")

def main():
    print("="*60)
    print("IPO MONEY - MASTER SCRAPER (3 SOURCES)")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    sources = {}
    
    # 1. IPOJI
    try:
        ipoji_data = scrape_ipoji_current_ipos()
        sources['ipoji'] = ipoji_data
        log_scraper("ipoji", "success", f"Found {len(ipoji_data)}", len(ipoji_data))
    except Exception as e:
        print(f"[IPOJI] Failed: {e}")
        log_scraper("ipoji", "error", str(e), 0)
        sources['ipoji'] = []
    
    # 2. IPOWATCH
    try:
        ipowatch_data = scrape_ipowatch()
        sources['ipowatch'] = ipowatch_data
        log_scraper("ipowatch", "success", f"Found {len(ipowatch_data)}", len(ipowatch_data))
    except Exception as e:
        print(f"[IPOWATCH] Failed: {e}")
        log_scraper("ipowatch", "error", str(e), 0)
        sources['ipowatch'] = []
    
    # 3. IPOPREMIUM
    try:
        ipopremium_data = scrape_ipopremium()
        sources['ipopremium'] = ipopremium_data
        log_scraper("ipopremium", "success", f"Found {len(ipopremium_data)}", len(ipopremium_data))
    except Exception as e:
        print(f"[IPOPREMIUM] Failed: {e}")
        log_scraper("ipopremium", "error", str(e), 0)
        sources['ipopremium'] = []
    
    # Merge
    print("\n[MERGE] Combining data...")
    merged = merge_ipo_data(sources)
    print(f"[MERGE] Total unique IPOs: {len(merged)}")
    
    # Save
    if merged:
        print("\n[DATABASE] Saving...")
        success = sum(1 for ipo in merged if upsert_ipo(ipo))
        print(f"[DATABASE] Saved {success}/{len(merged)}")
        log_scraper("master", "success", f"Processed {success} IPOs", success)
    else:
        print("\n⚠️  No data collected")
        log_scraper("master", "warning", "No data", 0)
    
    # Update statuses
    update_statuses()
    
    print("\n" + "="*60)
    print("✅ COMPLETE")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        log_scraper("master", "error", str(e), 0)
        sys.exit(1)
