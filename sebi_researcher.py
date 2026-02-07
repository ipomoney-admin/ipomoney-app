import os
import requests
import fitz  # PyMuPDF
import google.generativeai as genai
from supabase import create_client
import json
import re

# 1. Config & Setup (GitHub Secrets se uthayega)
# .strip() lagaya hai taki 'Invalid URL' error na aaye
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# Validations
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL ya KEY missing hai GitHub Secrets mein!")
    exit(1)

# Initialize AI and Database
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_latest_sebi_drhps():
    """SEBI site se latest documents fetch karne ka logic"""
    print("Fetching documents from SEBI...")
    # Abhi ke liye sample data (Testing ke liye)
    # Baad mein yahan BeautifulSoup scraper add karenge
    return [
        {
            "name": "Sample Tech IPO Ltd", 
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jan-2024/sample.pdf"
        }
    ]

def extract_pdf_text(pdf_url):
    """PDF download karke pehle 15 pages ka text nikalta hai"""
    print(f"Reading PDF from: {pdf_url}")
    try:
        r = requests.get(pdf_url, timeout=30)
        with open("temp.pdf", "wb") as f:
            f.write(r.content)
        
        doc = fitz.open("temp.pdf")
        text = ""
        for i in range(min(15, len(doc))):
            text += doc[i].get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"PDF Error: {e}")
        return ""

def get_ai_research(text):
    """Gemini AI ko text bhejkar structured data lena"""
    print("AI Researching in progress...")
    prompt = f"""
    Analyze this IPO prospectus and provide a STRICT JSON response.
    JSON structure:
    {{
      "company_details": "2-3 lines about business",
      "revenue_sources": "how they earn",
      "business_growth": "growth prospects",
      "financials": {{"2023": {{"rev": 0, "pat": 0}}, "2024": {{"rev": 0, "pat": 0}}}},
      "promoters_details": "names",
      "lead_managers": ["banker1", "banker2"],
      "registrar": "name"
    }}
    Text: {text[:10000]}
    """
    try:
        response = model.generate_content(prompt)
        # Markdown clean karna (AI kabhi kabhi ```json ... ``` bhejta hai)
        clean_json = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def main():
    drhp_list = get_latest_sebi_drhps()
    
    for ipo in drhp_list:
        print(f"\n--- Processing {ipo['name']} ---")
        
        # Step 1: Get Text
        raw_text = extract_pdf_text(ipo['url'])
        if not raw_text: continue
        
        # Step 2: AI Analysis
        research_data = get_ai_research(raw_text)
        if not research_data: continue
        
        # Step 3: Supabase Upsert
        try:
            payload = {
                "name": ipo['name'],
                "company_details": research_data.get("company_details"),
                "revenue_sources": research_data.get("revenue_sources"),
                "business_growth": research_data.get("business_growth"),
                "financials": research_data.get("financials"),
                "promoters_details": research_data.get("promoters_details"),
                "lead_managers": ", ".join(research_data.get("lead_managers", [])),
                "registrar": research_data.get("registrar"),
                "drhp_url": ipo['url']
            }
            
            supabase.table("ipos").upsert(payload).execute()
            print(f"DONE: {ipo['name']} updated in Supabase!")
            
        except Exception as e:
            print(f"Supabase Error: {e}")

if __name__ == "__main__":
    main()
