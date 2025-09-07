#!/usr/bin/env python3
"""
Test MRN and DOB extraction from PDF documents
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from duplicate_patient_manager import DuplicatePatientManager
from config import Config
import json
from typing import Dict, Any
import requests

def test_patient_pdf_extraction():
    """Test MRN and DOB extraction for specific patients"""
    
    config = Config()
    manager = DuplicatePatientManager(config)
    
    # Test cases: patients that should have PDFs with MRN/DOB
    test_patient_ids = [
        # Add some patient IDs here to test
        "example-patient-id-1",
        "example-patient-id-2"
    ]
    
    print("=" * 60)
    print("TESTING MRN AND DOB EXTRACTION FROM PDFs")
    print("=" * 60)
    
    for patient_id in test_patient_ids:
        print(f"\n--- Testing Patient ID: {patient_id} ---")
        
        try:
            # Create mock patient for testing
            mock_patient = {
                'id': patient_id,
                'agencyInfo': {
                    'patientFName': 'Test',
                    'patientLName': 'Patient',
                    'dob': '',
                    'medicalRecordNo': ''
                }
            }
            
            # Test PDF data extraction
            pdf_data = manager.verify_patient_data_from_pdf(mock_patient)
            
            print(f"Extracted Data:")
            print(f"  MRN: '{pdf_data.get('mrn', 'N/A')}'")
            print(f"  DOB: '{pdf_data.get('dob', 'N/A')}'")
            
            if pdf_data.get('mrn') or pdf_data.get('dob'):
                print("  ✅ Successfully extracted data from PDF")
            else:
                print("  ❌ No data extracted from PDF")
                
        except Exception as e:
            print(f"  ❌ Error testing patient {patient_id}: {e}")
    
    print("\n" + "=" * 60)

def test_duplicate_matching_with_mrn_dob():
    """Test duplicate matching with Name+MRN and Name+DOB combinations"""
    
    config = Config()
    manager = DuplicatePatientManager(config)
    
    print("=" * 60)
    print("TESTING DUPLICATE MATCHING WITH MRN/DOB")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {
            'description': 'Same Name + Same MRN (different DOB)',
            'patient1': {
                'id': 'test1',
                'agencyInfo': {
                    'patientFName': 'John',
                    'patientLName': 'Doe',
                    'dob': '1990-01-01',
                    'medicalRecordNo': 'MRN123456',
                    'pgcompanyID': 'company-1'
                }
            },
            'patient2': {
                'id': 'test2',
                'agencyInfo': {
                    'patientFName': 'John',
                    'patientLName': 'Doe',
                    'dob': '1990-01-02',  # Different DOB
                    'medicalRecordNo': 'MRN123456',  # Same MRN
                    'pgcompanyID': 'company-1'
                }
            }
        },
        {
            'description': 'Same Name + Same DOB (different MRN)',
            'patient1': {
                'id': 'test3',
                'agencyInfo': {
                    'patientFName': 'Jane',
                    'patientLName': 'Smith',
                    'dob': '1985-05-15',
                    'medicalRecordNo': 'MRN111111',
                    'pgcompanyID': 'company-1'
                }
            },
            'patient2': {
                'id': 'test4',
                'agencyInfo': {
                    'patientFName': 'Jane',
                    'patientLName': 'Smith',
                    'dob': '1985-05-15',  # Same DOB
                    'medicalRecordNo': 'MRN222222',  # Different MRN
                    'pgcompanyID': 'company-1'
                }
            }
        },
        {
            'description': 'Same Name + Empty MRN/DOB',
            'patient1': {
                'id': 'test5',
                'agencyInfo': {
                    'patientFName': 'Bob',
                    'patientLName': 'Johnson',
                    'dob': '',
                    'medicalRecordNo': '',
                    'pgcompanyID': 'company-1'
                }
            },
            'patient2': {
                'id': 'test6',
                'agencyInfo': {
                    'patientFName': 'Bob',
                    'patientLName': 'Johnson',
                    'dob': '',
                    'medicalRecordNo': '',
                    'pgcompanyID': 'company-1'
                }
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['description']} ---")
        
        patient1 = test_case['patient1']
        patient2 = test_case['patient2']
        
        # Display patient info
        p1_info = patient1['agencyInfo']
        p2_info = patient2['agencyInfo']
        
        print(f"Patient 1: {p1_info['patientFName']} {p1_info['patientLName']}")
        print(f"  DOB: '{p1_info['dob']}'")
        print(f"  MRN: '{p1_info['medicalRecordNo']}'")
        
        print(f"Patient 2: {p2_info['patientFName']} {p2_info['patientLName']}")
        print(f"  DOB: '{p2_info['dob']}'")
        print(f"  MRN: '{p2_info['medicalRecordNo']}'")
        
        # Test duplicate matching
        result = manager.are_patients_duplicates(patient1, patient2)
        
        print(f"Result:")
        print(f"  Is Duplicate: {result['is_duplicate']}")
        print(f"  Name Match: {result['name_match']}")
        print(f"  DOB Match: {result['dob_match']}")
        print(f"  MRN Match: {result['mrn_match']}")
        print(f"  Company Match: {result.get('pg_company_match', 'N/A')}")
        
        if result['is_duplicate']:
            print("  ✅ Correctly identified as duplicate")
        else:
            print("  ❌ Not identified as duplicate")

def test_document_finding():
    """Test document finding logic for various patients"""
    
    config = Config()
    manager = DuplicatePatientManager(config)
    
    print("\n" + "=" * 60)
    print("TESTING DOCUMENT FINDING LOGIC")
    print("=" * 60)
    
    # This would need actual patient IDs to test
    print("To test document finding with real data:")
    print("1. Update test_patient_ids in test_patient_pdf_extraction()")
    print("2. Run the test with actual patient IDs")
    print("3. Check logs for document finding results")
    
    print("\nDocument keywords being searched:")
    keywords = ['485', 'plan', 'cert', 'poc', 'care plan', 'physician', 'recert']
    for keyword in keywords:
        print(f"  - '{keyword}'")
    
    print("\nFallback keywords:")
    fallback_keywords = ['home', 'health', 'medical', 'patient', 'intake', 'assessment', 'evaluation']
    for keyword in fallback_keywords:
        print(f"  - '{keyword}'")

if __name__ == "__main__":
    print("MRN and DOB Extraction Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: PDF extraction (needs real patient IDs)
        # test_patient_pdf_extraction()
        
        # Test 2: Duplicate matching logic
        test_duplicate_matching_with_mrn_dob()
        
        # Test 3: Document finding logic
        test_document_finding()
        
        print("\n" + "=" * 60)
        print("TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
