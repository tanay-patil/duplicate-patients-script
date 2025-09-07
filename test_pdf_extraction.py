#!/usr/bin/env python3
"""
Test script to specifically test Azure OpenAI PDF extraction functionality
"""

import logging
import sys
from duplicate_patient_manager import DuplicatePatientManager
from config import Config

def setup_logging():
    """Setup detailed logging for PDF extraction testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pdf_extraction_test.log')
        ]
    )

def test_azure_openai_pdf_extraction():
    """Test Azure OpenAI PDF extraction with real patient data"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("AZURE OPENAI PDF EXTRACTION TEST")
    logger.info("="*60)
    
    # Initialize the manager
    config = Config()
    manager = DuplicatePatientManager(config)
    
    # Test company ID that has patients with PDF documents
    test_pg_company_id = "c5c1a894-08ac-4cb9-bfd1-0ad1384b890e"
    
    logger.info(f"Testing PDF extraction for PG Company ID: {test_pg_company_id}")
    
    try:
        # Get patients
        logger.info("Fetching patients...")
        patients = manager.fetch_patients(test_pg_company_id)
        logger.info(f"Fetched {len(patients)} patients")
        
        # Find patients with conflicts to test PDF extraction
        duplicate_groups = manager.group_duplicates(patients)
        logger.info(f"Found {len(duplicate_groups)} duplicate groups for testing")
        
        pdf_extraction_results = []
        
        for i, group in enumerate(duplicate_groups[:3]):  # Test first 3 groups
            logger.info(f"\n--- Testing PDF extraction for duplicate group {i+1} ---")
            
            for patient in group:
                patient_id = patient['id']
                patient_name = patient.get('patientName', 'Unknown')
                
                logger.info(f"Testing PDF extraction for patient: {patient_name} ({patient_id})")
                
                # Get orders for this patient
                try:
                    orders_response = manager.api_client.get(
                        f"/Order/patient/{patient_id}"
                    )
                    orders = orders_response.json() if orders_response.status_code == 200 else []
                    logger.info(f"Found {len(orders)} orders for patient {patient_id}")
                    
                    if orders:
                        # Test PDF extraction
                        pdf_data = manager.verify_patient_data_from_pdf(patient_id, orders)
                        
                        result = {
                            'patient_id': patient_id,
                            'patient_name': patient_name,
                            'orders_count': len(orders),
                            'pdf_extracted_mrn': pdf_data.get('mrn', ''),
                            'pdf_extracted_dob': pdf_data.get('dob', ''),
                            'original_mrn': patient.get('medicalRecordNumber', ''),
                            'original_dob': patient.get('dateOfBirth', ''),
                            'extraction_success': bool(pdf_data.get('mrn') or pdf_data.get('dob'))
                        }
                        
                        pdf_extraction_results.append(result)
                        
                        logger.info(f"PDF Extraction Results:")
                        logger.info(f"  Original MRN: {result['original_mrn']}")
                        logger.info(f"  PDF MRN: {result['pdf_extracted_mrn']}")
                        logger.info(f"  Original DOB: {result['original_dob']}")
                        logger.info(f"  PDF DOB: {result['pdf_extracted_dob']}")
                        logger.info(f"  Extraction Success: {result['extraction_success']}")
                        
                        # Check if Azure OpenAI found better data
                        if result['pdf_extracted_mrn'] and result['pdf_extracted_mrn'] != result['original_mrn']:
                            logger.info("  🔍 Azure OpenAI found different MRN in PDF!")
                        if result['pdf_extracted_dob'] and result['pdf_extracted_dob'] != result['original_dob']:
                            logger.info("  🔍 Azure OpenAI found different DOB in PDF!")
                    else:
                        logger.warning(f"No orders found for patient {patient_id}")
                        
                except Exception as e:
                    logger.error(f"Error testing PDF extraction for patient {patient_id}: {str(e)}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("PDF EXTRACTION TEST SUMMARY")
        logger.info("="*60)
        
        total_tested = len(pdf_extraction_results)
        successful_extractions = sum(1 for r in pdf_extraction_results if r['extraction_success'])
        
        logger.info(f"Total patients tested: {total_tested}")
        logger.info(f"Successful PDF extractions: {successful_extractions}")
        logger.info(f"Success rate: {(successful_extractions/total_tested)*100:.1f}%" if total_tested > 0 else "0%")
        
        # Show Azure OpenAI effectiveness
        mrn_improvements = sum(1 for r in pdf_extraction_results 
                              if r['pdf_extracted_mrn'] and r['pdf_extracted_mrn'] != r['original_mrn'])
        dob_improvements = sum(1 for r in pdf_extraction_results 
                              if r['pdf_extracted_dob'] and r['pdf_extracted_dob'] != r['original_dob'])
        
        logger.info(f"Cases where Azure OpenAI found better MRN: {mrn_improvements}")
        logger.info(f"Cases where Azure OpenAI found better DOB: {dob_improvements}")
        
        if successful_extractions > 0:
            logger.info("✅ Azure OpenAI is working correctly for PDF extraction!")
        else:
            logger.warning("⚠️ Azure OpenAI may need configuration check")
            
        return pdf_extraction_results
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return []

def test_document_detection():
    """Test the document detection logic specifically"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "="*60)
    logger.info("DOCUMENT DETECTION TEST")
    logger.info("="*60)
    
    # Test document names
    test_documents = [
        "CMS-485 HOME HEALTH CERTIFICATION AND PLAN OF CARE",
        "Home Health Certification and Plan of Care", 
        "HOME HEALTH CERTIFICATION AND PLAN OF CARE",
        "Recertification",
        "Plan of Care",
        "Physician Orders",
        "Care Plan Document",
        "Some Random Document",
        "Home Health Assessment",
        "Medical Evaluation",
        "Patient Intake Form"
    ]
    
    search_keywords = [
        '485',           # CMS-485 Home Health Certification and Plan of Care
        'plan',          # Plan of Care
        'cert',          # Certification
        'poc',           # Plan of Care (abbreviated)
        'care plan',     # Care Plan
        'physician',     # Physician orders
        'recert'         # Recertification
    ]
    
    fallback_keywords = ['home', 'health', 'medical', 'patient', 'intake', 'assessment', 'evaluation']
    
    logger.info("Testing document detection with current keywords:")
    logger.info(f"Primary keywords: {search_keywords}")
    logger.info(f"Fallback keywords: {fallback_keywords}")
    
    detected_primary = 0
    detected_fallback = 0
    not_detected = 0
    
    for doc_name in test_documents:
        doc_lower = doc_name.lower()
        found_primary = False
        found_fallback = False
        
        # Check primary keywords
        for keyword in search_keywords:
            if keyword in doc_lower:
                logger.info(f"✅ PRIMARY: '{doc_name}' -> Found '{keyword}'")
                detected_primary += 1
                found_primary = True
                break
        
        if not found_primary:
            # Check fallback keywords
            for keyword in fallback_keywords:
                if keyword in doc_lower:
                    logger.info(f"🔍 FALLBACK: '{doc_name}' -> Found '{keyword}'")
                    detected_fallback += 1
                    found_fallback = True
                    break
        
        if not found_primary and not found_fallback:
            logger.info(f"❌ NOT DETECTED: '{doc_name}'")
            not_detected += 1
    
    logger.info(f"\nDocument detection results:")
    logger.info(f"Detected by primary keywords: {detected_primary}")
    logger.info(f"Detected by fallback keywords: {detected_fallback}")
    logger.info(f"Not detected: {not_detected}")
    logger.info(f"Total detection rate: {((detected_primary + detected_fallback) / len(test_documents)) * 100:.1f}%")

if __name__ == "__main__":
    # Test document detection logic
    test_document_detection()
    
    # Test actual PDF extraction with Azure OpenAI
    results = test_azure_openai_pdf_extraction()
    
    print(f"\nTest completed! Check 'pdf_extraction_test.log' for detailed results.")
    print(f"Tested PDF extraction on {len(results)} patients.")
