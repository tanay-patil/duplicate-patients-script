#!/usr/bin/env python3
"""
Test script to check Azure OpenAI configuration and implementation
"""

import sys
import traceback
from config import Config

def test_openai_import():
    """Test if OpenAI library can be imported"""
    try:
        from openai import AzureOpenAI
        print("✅ OpenAI library imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import OpenAI library: {e}")
        return False

def test_azure_openai_client():
    """Test Azure OpenAI client initialization"""
    try:
        from openai import AzureOpenAI
        
        config = Config()
        print(f"Azure OpenAI Endpoint: {config.AZURE_OPENAI_ENDPOINT}")
        print(f"Azure OpenAI Deployment: {config.AZURE_OPENAI_DEPLOYMENT}")
        print(f"Azure OpenAI Key: {'***' + config.AZURE_OPENAI_KEY[-4:] if config.AZURE_OPENAI_KEY else 'NOT SET'}")
        
        client = AzureOpenAI(
            api_key=config.AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT
        )
        print("✅ Azure OpenAI client created successfully")
        return client
    except Exception as e:
        print(f"❌ Failed to create Azure OpenAI client: {e}")
        traceback.print_exc()
        return None

def test_openai_api_call(client):
    """Test a simple API call to Azure OpenAI"""
    try:
        config = Config()
        response = client.chat.completions.create(
            model=config.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Extract MRN and DOB from this text: 'Patient John Doe, MRN: 12345, DOB: 01/01/1980'"}
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        result = response.choices[0].message.content
        print("✅ Azure OpenAI API call successful")
        print(f"Response: {result}")
        return True
    except Exception as e:
        print(f"❌ Azure OpenAI API call failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("AZURE OPENAI IMPLEMENTATION TEST")
    print("="*60)
    
    # Test 1: Import OpenAI library
    print("\n1. Testing OpenAI library import...")
    if not test_openai_import():
        print("Cannot proceed without OpenAI library")
        return
    
    # Test 2: Create Azure OpenAI client
    print("\n2. Testing Azure OpenAI client creation...")
    client = test_azure_openai_client()
    if not client:
        print("Cannot proceed without working client")
        return
    
    # Test 3: Test API call
    print("\n3. Testing Azure OpenAI API call...")
    test_openai_api_call(client)
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    main()
