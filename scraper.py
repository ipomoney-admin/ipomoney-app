import os
from supabase import create_client

# Ye lines aapke secrets (URL aur Key) ko read karengi
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def test_data():
    # Hum ek dummy data bhej rahe hain testing ke liye
    data = {
        "name": "Tata Motors IPO Test",
        "category": "Mainboard",
        "status": "Upcoming"
    }
    # Ye command data ko Supabase ki 'ipos' table mein bhej degi
    try:
        supabase.table("ipos").insert(data).execute()
        print("Mubarak Ho! Data Supabase mein pahunch gaya.")
    except Exception as e:
        print(f"Kuch gadbad hui: {e}")

if __name__ == "__main__":
    test_data()
