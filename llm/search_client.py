"""
llm/search_client.py

Uses Gemini 2.5 Flash with Google Search Grounding to extract preliminary data about a firm.
Upgraded to support Tiered Retrieval, Provenance Objects, and JSON Schema validation.
Uses a two-step Search-then-Extract pattern to comply with Gemini API constraints.
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

    # Step 1: Search and gather context with Google Search Grounding
    search_prompt = f"""
    Search the internet for the financial services company: "{company_name}".
    Focus on Tier A sources (regulatory filings, IRDAI disclosures, SEC 10-K) and Tier B sources (Investor Presentations).
    
    Find the following information:
    1. Total Assets Under Management (AUM) or Gross Written Premium in Billions USD. (S1_AUM)
    2. Core data platform / architecture status. Determine if it is Siloed On-Premises (Batch), Hybrid — partial cloud, or Cloud-Native (AWS/Azure/GCP).
    3. Core ERP / Policy Admin System status. Determine if it is Legacy monolith (>10 years old), On-prem with API layer, or Modern cloud-native.
    4. Annual life insurance / policy applications (if they do insurance).
    5. Annual insurance claims processed (if they do insurance).
    
    Provide the exact values, the source URLs, and a quote justifying each metric.
    """
    
    try:
        search_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=search_prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.0
            )
        )
        
        search_results = search_response.text
        if not search_results:
            return {}

        # Step 2: Structured JSON extraction of search results
        extract_prompt = f"""
        Based on the following search results about "{company_name}", extract the metrics into the requested JSON schema.
        
        Search Results:
        {search_results}
        
        Schema mapping instructions:
        - company_name: Correctly spelled official company name.
        - S1_AUM: AUM or GWP in Billions USD (value should be a string representing a float, e.g. "50.0").
        - S1_ARCH: Data architecture. Value must be one of: "Siloed On-Premises (Batch)", "Hybrid — partial cloud", "Cloud-Native (AWS/Azure/GCP)".
        - S1_ERP: Core ERP/Policy Admin status. Value must be one of: "Legacy monolith (>10 years old)", "On-prem with API layer", "Modern cloud-native".
        - S2_ANNUAL_UNDERWRITING_APPS: Annual policy applications.
        - S3_ANNUAL_CLAIMS: Annual claims processed.
        
        If any metric is not found in the search results, return null for that property.
        """
        
        extract_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=extract_prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        
        data = json.loads(extract_response.text)
        
        # Filter out nulls
        return {k: v for k, v in data.items() if v is not None}
        
    except Exception as e:
        print(f"Error during Gemini Search extraction: {e}")
        return {}
