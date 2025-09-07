#!/usr/bin/env python3
"""
Test keyword matching for PDF extraction

This script tests the keyword matching logic used to find medical documents.
"""

def test_keyword_matching():
    """Test keyword matching against sample document names"""
    
    # Keywords from the system (in order of preference)
    primary_keywords = [
        '485',           # CMS-485 Home Health Certification and Plan of Care
        'plan',          # Plan of Care
        'cert',          # Certification
        'poc',           # Plan of Care (abbreviated)
        'care plan',     # Care Plan
        'physician',     # Physician orders
        'recert',        # Recertification
        'home health',   # Home Health documents
        'medical',       # Medical documents
        'intake',        # Intake forms
        'assessment'     # Assessment forms
    ]
    
    fallback_keywords = ['home', 'health', 'patient', 'evaluation', 'order', 'note', 'communication']
    
    # Sample document names (real examples from the system)
    test_documents = [
        "CMS-485 HOME HEALTH CERTIFICATION AND PLAN OF CARE",
        "Home Health Certification and Plan of Care",
        "HOME HEALTH CERTIFICATION AND PLAN OF CARE",
        "Recertification",
        "COMMUNICATION NOTE",
        "Physician Orders",
        "Medical Assessment",
        "Patient Intake Form",
        "Home Health Plan",
        "Care Plan Review",
        "POC Update",
        "485 Form",
        "Health Evaluation",
        "Patient Communication",
        "Order Update",
        "Some Random Document",
        "Invoice 2025",
        "Lab Results"
    ]
    
    print("=" * 80)
    print("KEYWORD MATCHING TEST")
    print("=" * 80)
    print()
    
    for doc_name in test_documents:
        doc_name_lower = doc_name.lower()
        matched_primary = None
        matched_fallback = None
        
        # Test primary keywords
        for keyword in primary_keywords:
            if keyword in doc_name_lower:
                matched_primary = keyword
                break
        
        # Test fallback keywords if no primary match
        if not matched_primary:
            for keyword in fallback_keywords:
                if keyword in doc_name_lower:
                    matched_fallback = keyword
                    break
        
        # Display results
        status = "✅ PRIMARY" if matched_primary else "⚠️  FALLBACK" if matched_fallback else "❌ NO MATCH"
        keyword_found = matched_primary or matched_fallback or "None"
        
        print(f"{status:<12} | {doc_name:<40} | Keyword: {keyword_found}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✅ PRIMARY    - Document contains high-priority medical keywords")
    print("⚠️  FALLBACK   - Document contains general medical keywords")
    print("❌ NO MATCH   - Document doesn't contain medical keywords")
    print("\nThe system will:")
    print("1. First try to find documents with PRIMARY keywords")
    print("2. If none found, try FALLBACK keywords")
    print("3. If still none found, skip PDF extraction")

if __name__ == "__main__":
    test_keyword_matching()
