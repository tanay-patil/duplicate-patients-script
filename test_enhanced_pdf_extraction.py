#!/usr/bin/env python3
"""
Test script for enhanced PDF extraction with OCR fallback

This script tests both direct text extraction and OCR capabilities.
"""

import sys
import logging
from config import Config
from duplicate_patient_manager import DuplicatePatientManager


def setup_logging():
    """Setup basic logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def test_pdf_extraction_methods():
    """Test both PDF text extraction methods"""
    print("=" * 60)
    print("PDF EXTRACTION TEST WITH OCR FALLBACK")
    print("=" * 60)
    
    try:
        # Load configuration
        print("Loading configuration...")
        config = Config()
        
        # Initialize duplicate patient manager
        print("Initializing duplicate patient manager...")
        manager = DuplicatePatientManager(config)
        
        # Get test patient ID
        test_patient_id = input("Enter a patient ID to test PDF extraction: ").strip()
        if not test_patient_id:
            print("No patient ID provided, exiting test")
            return False
        
        print(f"\nTesting PDF extraction for patient: {test_patient_id}")
        print("-" * 40)
        
        # Test PDF verification (which uses the enhanced extraction)
        print("Testing enhanced PDF extraction with OCR fallback...")
        
        # Create a mock patient object
        test_patient = {
            'id': test_patient_id,
            'agencyInfo': {
                'patientFName': 'Test',
                'patientLName': 'Patient',
                'patientMRN': 'TEST123',
                'patientDOB': '01/01/1990'
            }
        }
        
        # Verify patient data from PDF (this will use our enhanced extraction)
        pdf_result = manager.verify_patient_data_from_pdf(test_patient)
        
        print("\n" + "=" * 60)
        print("PDF EXTRACTION RESULTS")
        print("=" * 60)
        
        if pdf_result.get('pdf_mrn') or pdf_result.get('pdf_dob'):
            print("✓ PDF extraction SUCCESS!")
            print(f"   Extracted MRN: '{pdf_result.get('pdf_mrn', 'Not found')}'")
            print(f"   Extracted DOB: '{pdf_result.get('pdf_dob', 'Not found')}'")
            print(f"   Source: {pdf_result.get('extraction_method', 'Unknown')}")
        else:
            print("✗ PDF extraction FAILED - no MRN or DOB extracted")
            print("   This could mean:")
            print("   - No suitable PDF documents found")
            print("   - PDF text extraction and OCR both failed")
            print("   - Document doesn't contain MRN/DOB information")
        
        return True
            
    except Exception as e:
        print(f"✗ Error during PDF extraction test: {e}")
        return False


def test_ocr_availability():
    """Test if OCR libraries are available"""
    print("\n" + "=" * 60)
    print("OCR AVAILABILITY TEST")
    print("=" * 60)
    
    try:
        import pytesseract
        from PIL import Image
        import pdf2image
        
        print("✓ All OCR libraries are available:")
        print("   - pytesseract: Available")
        print("   - PIL (Pillow): Available") 
        print("   - pdf2image: Available")
        
        # Test Tesseract installation
        try:
            version = pytesseract.get_tesseract_version()
            print(f"   - Tesseract version: {version}")
            return True
        except Exception as e:
            print(f"✗ Tesseract not properly installed: {e}")
            print("   Install Tesseract OCR from: https://github.com/tesseract-ocr/tesseract")
            return False
            
    except ImportError as e:
        print("✗ OCR libraries not available:")
        print(f"   Missing: {e}")
        print("\n   To install OCR support, run:")
        print("   pip install pytesseract Pillow pdf2image")
        print("   And install Tesseract OCR binary")
        return False


def main():
    """Main test function"""
    setup_logging()
    
    print("Starting Enhanced PDF Extraction Tests...")
    print()
    
    # Test 1: Check OCR availability
    ocr_available = test_ocr_availability()
    
    if not ocr_available:
        print("\nWarning: OCR not available - only direct text extraction will work")
    
    print("\nDo you want to test PDF extraction on a specific patient?")
    choice = input("Enter 'y' to test extraction, or any other key to skip: ").strip().lower()
    
    if choice == 'y':
        test_pdf_extraction_methods()
    
    print("\n" + "=" * 60)
    print("ENHANCED PDF EXTRACTION TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
