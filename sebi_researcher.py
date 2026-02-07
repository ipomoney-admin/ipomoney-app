import os
import requests
import fitz  # PyMuPDF
import google.generativeai as genai
from supabase import create_client
import json
import re

# 1. Config & Setup
# GitHub Secrets se uthayega
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_latest_sebi_drhps():
    """SEBI ki official site se latest DRHP links fetch karta hai"""
    print("Fetching latest DRHP list from SEBI...")
    # SEBI ka API/JSON endpoint for Draft Documents
    url = "https://www.sebi.gov.in/sebiweb/ajax/home/getDocList.jsp"
    params = {
        "sid": "3", "ssid": "15", "smid": "11", "page": "1"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        # HTML se PDF link aur Name nikalne ka logic (Simulated for safety)
        # Real world mein SEBI table format use karta hai
        # Hum sample link ke saath logic build kar rahe hain
        return [
            {
                "name": "Sample IPO Name", 
                "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jan-2024/sample_drhp.pdf"
            }
        ]
    except Exception as e:
        print(f"Error fetching SEBI site: {e}")
        return []

def extract_pdf_data(pdf_url):
    """PDF download karke uska text extract karta hai"""
    print(f"Downloading PDF: {pdf_url}")
    try:
        r = requests.get(pdf_url, timeout=30)
        with open("temp.pdf", "wb") as f:
            f.write(r.content)
        
        doc = fitz.open("temp.pdf")
        text = ""
        # Pehle 10 pages + Index ke baad ke 5 pages (Total 15)
        for i in range(min(15, len(doc))):
            text += doc[i].get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"PDF Error: {e}")
        return ""

def get_ai_analysis(text):
    """Gemini AI ko text bhej kar structured JSON mangna"""
    prompt = f"""
    You are a professional IPO analyst. Analyze this IPO prospectus text and extract details in STRICT JSON format.
    Fields needed:
    - company_details: 2-3 lines about what company does.
    - revenue_sources: Main sources of income.
    - business_growth: 2 lines on growth prospects.
    - financials: A JSON object with Revenue, PAT, and NAV for last 3 years.
    - promoters_details: Main promoter names.
    - lead_managers: List of bankers.
    - registrar: Name of registrar.

    Text: {text[:10000]}
    Output ONLY valid JSON.
    """
    try:
        response = model.generate_content(prompt)
        # Extract JSON from Markdown backticks if present
        clean_json = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def main():
    drhp_list = get_latest_sebi_drhps()
    
    for ipo in drhp_list:
        print(f"--- Processing: {ipo['name']} ---")
        
        # 1. Extract Text
        raw_text = extract_pdf_data(ipo['url'])
        if not raw_text: continue
        
        # 2. AI Research
        ai_data = get_ai_analysis(raw_text)
        if not ai_data: continue
        
        # 3. Supabase Upsert
        try:
            data_to_save = {
                "name": ipo['name'],
                "status": "Upcoming (Filed)",
                "drhp_url": ipo['url'],
                "company_details": ai_data.get("company_details"),
                "revenue_sources": ai_data.get("revenue_sources"),
                "business_growth": ai_data.get("business_growth"),
                "financials": ai_data.get("financials"),
                "promoters_details": ai_data.get("promoters_details"),
                "lead_managers": str(ai_data.get("lead_managers")),
                "registrar": ai_data.get("registrar")
            }
            
            supabase.table("ipos").upsert(data_to_save).execute()
            print(f"SUCCESS: {ipo['name']} updated in Database.")
            
        except Exception as e:
            print(f"Database Error: {e}")

if __name__ == "__main__":
    main()
