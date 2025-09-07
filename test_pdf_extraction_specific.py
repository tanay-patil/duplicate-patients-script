#!/usr/bin/env python3
"""
Test PDF extraction from a specific URL

This script tests PDF text extraction and OpenAI processing on a specific PDF.
"""

import requests
import io
import pdfplumber
import sys
import logging
from config import Config
from openai import AzureOpenAI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_pdf(url: str) -> bytes:
    """Download PDF from URL"""
    try:
        logger.info(f"Downloading PDF from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        logger.info(f"Downloaded PDF: {len(response.content)} bytes")
        return response.content
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        raise

def extract_text_with_pdfplumber(pdf_content: bytes) -> str:
    """Extract text using pdfplumber"""
    try:
        logger.info("Extracting text using pdfplumber...")
        text_content = ""
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            logger.info(f"PDF has {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages, 1):
                logger.info(f"Processing page {page_num}...")
                page_text = page.extract_text()
                
                if page_text:
                    text_content += f"\n--- PAGE {page_num} ---\n"
                    text_content += page_text
                    logger.info(f"Page {page_num}: {len(page_text)} characters extracted")
                else:
                    logger.warning(f"Page {page_num}: No text extracted")
        
        logger.info(f"Total text extracted: {len(text_content)} characters")
        return text_content
        
    except Exception as e:
        logger.error(f"Error extracting text with pdfplumber: {e}")
        raise

def extract_with_openai(text_content: str, config: Config) -> dict:
    """Extract MRN and DOB using OpenAI"""
    try:
        logger.info("Setting up OpenAI client...")
        
        client = AzureOpenAI(
            api_key=config.AZURE_OPENAI_KEY,
            api_version="2024-02-01",  # Default version
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT
        )
        
        # Enhanced prompt for better extraction
        prompt = f"""
You are a medical data extraction expert. Extract the Medical Record Number (MRN) and Date of Birth (DOB) from this medical document text.

Medical Document Text:
{text_content}

Please extract:
1. MRN (Medical Record Number) - Look for patterns like "MRN:", "Medical Record Number:", "Patient ID:", "Chart #:", or similar identifiers
2. DOB (Date of Birth) - Look for patterns like "DOB:", "Date of Birth:", "Born:", or date formats like MM/DD/YYYY, MM-DD-YYYY, etc.

Return ONLY a JSON object in this exact format:
{{
    "mrn": "extracted_mrn_value",
    "dob": "extracted_dob_value"
}}

If you cannot find either value, use null for that field.
"""

        logger.info("Sending request to OpenAI...")
        response = client.chat.completions.create(
            model=config.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a medical data extraction expert. Extract information accurately and return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response: {result_text}")
        
        # Try to parse JSON
        import json
        try:
            result = json.loads(result_text)
            logger.info(f"Successfully parsed JSON: {result}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Raw response: {result_text}")
            return {"mrn": None, "dob": None, "error": f"JSON parse error: {e}"}
            
    except Exception as e:
        logger.error(f"Error with OpenAI extraction: {e}")
        return {"mrn": None, "dob": None, "error": str(e)}

def main():
    """Main test function"""
    pdf_url = "https://dawav.blob.core.windows.net/externalwav/1318362d-9f00-47b9-bb9d-bf687065730f/5ca7351e-320a-479b-b0f5-9d6521bac4d0/patientorders/d3446e5d-1731-46a6-b6bf-ba3d8f9ac0c8_document.pdf"
    
    print("=" * 80)
    print("PDF EXTRACTION TEST")
    print("=" * 80)
    print(f"Testing PDF: {pdf_url}")
    print()
    
    try:
        # Load config
        config = Config()
        
        # Step 1: Download PDF
        pdf_content = download_pdf(pdf_url)
        
        # Step 2: Extract text
        text_content = extract_text_with_pdfplumber(pdf_content)
        
        print("\n" + "=" * 80)
        print("EXTRACTED TEXT")
        print("=" * 80)
        if text_content.strip():
            print(text_content)
        else:
            print("❌ NO TEXT EXTRACTED!")
        
        # Step 3: Test OpenAI extraction if we have text
        if text_content.strip():
            print("\n" + "=" * 80)
            print("OPENAI EXTRACTION TEST")
            print("=" * 80)
            
            openai_result = extract_with_openai(text_content, config)
            print(f"OpenAI Result: {openai_result}")
            
            if openai_result.get('mrn'):
                print(f"✅ MRN Found: {openai_result['mrn']}")
            else:
                print("❌ MRN Not Found")
                
            if openai_result.get('dob'):
                print(f"✅ DOB Found: {openai_result['dob']}")
            else:
                print("❌ DOB Not Found")
        else:
            print("❌ Skipping OpenAI test - no text to process")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETED")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Test failed with exception")

if __name__ == "__main__":
    main()
