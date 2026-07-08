"""
llm/search_client.py

Uses Gemini 2.5 Flash with Google Search Grounding to extract preliminary data about a firm.
"""
import os
import json
from google import genai
from google.genai import types

def extract_company_data(company_name: str) -> dict:
    """
    Searches the internet for the company and extracts key metrics into a dict 
    matching the questionnaire keys.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "Missing GEMINI_API_KEY"}
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Search the internet for the financial services company: "{company_name}".
    Find their latest:
    1. Total Assets Under Management (AUM) in Billions USD (convert to float, e.g. 50.0). If they are an insurance company, use their total premium or AUM equivalent.
    2. Total Employee Count (convert to float, e.g. 15000.0).
    3. The official, correctly spelled name of the company (to fix any typos the user might have made).
    
    Return EXACTLY a raw JSON object (no markdown formatting, no code blocks) with these keys:
    {{
        "S1_AUM": <float value or null if not found>,
        "S1_EMPLOYEES": <float value or null if not found>,
        "company_name": <string of the official company name>
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.0
            )
        )
        
        # Clean the response to ensure it's pure JSON
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text.strip())
        
        # Filter out nulls so we don't overwrite defaults with null
        return {k: v for k, v in data.items() if v is not None}
        
    except Exception as e:
        print(f"Error during Gemini Search extraction: {e}")
        return {}
