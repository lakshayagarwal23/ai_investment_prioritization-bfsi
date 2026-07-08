"""
llm/search_client.py

Uses Gemini 2.5 Flash with Google Search Grounding to extract preliminary data about a firm.
Upgraded to support Tiered Retrieval, Provenance Objects, and JSON Schema validation.
"""
import os
import json
from google import genai
from google.genai import types

def extract_company_data(company_name: str) -> dict:
    """
    Searches the internet for the company and extracts key metrics into a dict 
    matching the questionnaire keys. Returns provenance objects.
    """
    import streamlit as st
    api_key = os.environ.get("GEMINI_API_KEY") or st.session_state.get("gemini_api_key")
    if not api_key:
        return {"error": "Missing GEMINI_API_KEY"}
        
    client = genai.Client(api_key=api_key)
    
    provenance_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "value": types.Schema(type=types.Type.STRING),
            "source_url": types.Schema(type=types.Type.STRING),
            "quote": types.Schema(type=types.Type.STRING),
            "confidence": types.Schema(type=types.Type.STRING, enum=["High", "Med", "Low"])
        },
        required=["value", "source_url", "quote", "confidence"]
    )

    response_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "company_name": types.Schema(type=types.Type.STRING),
            "S1_AUM": provenance_schema,
            "S1_ARCH": provenance_schema,
            "S1_ERP": provenance_schema,
            "S2_ANNUAL_UNDERWRITING_APPS": provenance_schema,
            "S3_ANNUAL_CLAIMS": provenance_schema
        },
        required=["company_name"]
    )

    prompt = f"""
    Search the internet for the financial services company: "{company_name}".
    Focus on Tier A sources (regulatory filings, IRDAI disclosures, SEC 10-K) and Tier B sources (Investor Presentations).
    
    Extract the following metrics if available:
    1. Total Assets Under Management (AUM) or Gross Written Premium in Billions USD. (S1_AUM)
    2. Data Architecture (S1_ARCH). Output one of: "Siloed On-Premises (Batch)", "Hybrid — partial cloud", "Cloud-Native (AWS/Azure/GCP)".
    3. Core ERP/Policy Admin System status (S1_ERP). Output one of: "Legacy monolith (>10 years old)", "On-prem with API layer", "Modern cloud-native".
    4. Annual life insurance / policy applications (S2_ANNUAL_UNDERWRITING_APPS)
    5. Annual insurance claims processed (S3_ANNUAL_CLAIMS)
    
    Also return the official, correctly spelled name of the company as 'company_name'.
    
    For each metric (except company_name), provide a provenance object with:
    - value: The extracted value as a string (e.g. "50.0" or the exact category).
    - source_url: The URL where you found this information.
    - quote: A short excerpt justifying the value.
    - confidence: "High" (from official Tier A/B docs), "Med" (from press releases/Tier C), or "Low" (inferred/estimated).
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        
        data = json.loads(response.text)
        
        # Filter out nulls
        return {k: v for k, v in data.items() if v is not None}
        
    except Exception as e:
        print(f"Error during Gemini Search extraction: {e}")
        return {}
