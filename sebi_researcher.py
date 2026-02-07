import os
import requests
import fitz  # PyMuPDF
from google import genai # Nayi library
from supabase import create_client
import json
import re

# URL aur KEY ko check karne ke liye print (Debug mode)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Bhai, SUPABASE_URL ya KEY missing hai GitHub Secrets mein!")

# Client Setup
client = genai.Client(api_key=GEMINI_KEY) # Naya setup
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ... baaki functions wahi rahenge ...
# Bas AI call wala function thoda badlega:

def get_ai_analysis(text):
    prompt = "Extract IPO details in JSON..." # Aapka purana prompt
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", # Latest model
            contents=prompt + text[:10000]
        )
        clean_json = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI Error: {e}")
        return None
