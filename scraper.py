import pandas as pd
import requests
from io import StringIO
from supabase import create_client
import os

# Credentials
URL = "https://khnuyrhafzppbugebjdn.supabase.co"
KEY = "sb_secret_SIb_8imA5DxLxNVK1srMDQ__xLolWEV"
# Google Sheet CSV Link (Niche bataya hai kaise milega)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTGp-0ECuXqbLmlDHfvKbfu0IqfFxqwnnEpA376aco74HqOuctesu17dUWPgYPVPkx6xUFS51RqhzmM/pub?output=csv"

supabase = create_client(URL, KEY)

def sync_from_sheet():
    try:
        # Sheet se data read karna
        response = requests.get(SHEET_CSV_URL)
        df = pd.read_csv(StringIO(response.text))
        
        # Har row ko Supabase mein daalna
        for _, row in df.iterrows():
            data = {
                "name": str(row['name']),
                "dates": str(row['dates']),
                "type": str(row['type']),
                "gmp": str(row['gmp']),
                "subs_total": str(row['subs_total']),
                "status": str(row['status'])
            }
            supabase.table("ipos").upsert(data, on_conflict="name").execute()
            print(f"✅ Live on Ipomoney: {row['name']}")
            
    except Exception as e:
        print(f"❌ Sync Error: {e}")

if __name__ == "__main__":
    sync_from_sheet()
