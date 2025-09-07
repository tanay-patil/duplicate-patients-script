#!/usr/bin/env python3
"""
Comprehensive test for Azure OpenAI PDF extraction with real data
"""

import sys
import logging
from duplicate_patient_manager import DuplicatePatientManager
from config import Config

def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_openai_with_sample_text():
    """Test OpenAI with sample medical document text"""
    logger = logging.getLogger(__name__)
    
    try:
        config = Config()
        manager = DuplicatePatientManager(config)
        
        # Sample medical document text
        sample_pdf_text = """
        HOME HEALTH CERTIFICATION AND PLAN OF CARE
        
        Patient Information:
        Name: John Smith
        Medical Record Number: MRN123456
        Date of Birth: 03/15/1965
        
        Physician Information:
        Dr. Sarah Johnson
        
        Diagnosis: Diabetes Type 2
        
        Plan of Care:
        - Monitor blood glucose levels
        - Medication management
        - Patient education
        """
        
        # Convert to bytes (simulating PDF content)
        import io
        pdf_content = sample_pdf_text.encode('utf-8')
        
        logger.info("Testing OpenAI extraction with sample medical document...")
        result = manager.extract_mrn_dob_from_pdf(pdf_content)
        
        logger.info(f"Extraction result: {result}")
        
        # Verify results
        expected_mrn = "MRN123456"
        expected_dob = "03/15/1965"
        
        if result.get('mrn') == expected_mrn:
            logger.info("✅ MRN extraction successful")
        else:
            logger.warning(f"⚠️ MRN extraction issue - Expected: {expected_mrn}, Got: {result.get('mrn')}")
        
        if result.get('dob') == expected_dob:
            logger.info("✅ DOB extraction successful")
        else:
            logger.warning(f"⚠️ DOB extraction issue - Expected: {expected_dob}, Got: {result.get('dob')}")
            
        return result.get('mrn') == expected_mrn and result.get('dob') == expected_dob
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_real_patient_data():
    """Test with actual patient data"""
    logger = logging.getLogger(__name__)
    
    try:
        config = Config()
        manager = DuplicatePatientManager(config)
        
        # Use a test company that we know has patient data
        test_pg_company_id = "c5c1a894-08ac-4cb9-bfd1-0ad1384b890e"
        
        logger.info(f"Fetching patients for company: {test_pg_company_id}")
        patients = manager.fetch_patients(test_pg_company_id)
        logger.info(f"Found {len(patients)} patients")
        
        if len(patients) == 0:
            logger.warning("No patients found for testing")
            return False
        
        # Test with first patient that has conflicts
        duplicate_groups = manager.group_duplicates(patients)
        
        if len(duplicate_groups) == 0:
            logger.warning("No duplicate groups found for PDF testing")
            return False
        
        logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        
        # Test PDF extraction on first group
        test_group = duplicate_groups[0]
        logger.info(f"Testing PDF extraction on group with {len(test_group)} patients")
        
        extraction_count = 0
        for patient in test_group:
            patient_name = patient.get('patientName', 'Unknown')
            patient_id = patient.get('id', 'Unknown')
            
            logger.info(f"Testing PDF extraction for: {patient_name} ({patient_id})")
            
            try:
                pdf_data = manager.verify_patient_data_from_pdf(patient)
                logger.info(f"PDF extraction result: {pdf_data}")
                
                if pdf_data.get('mrn') or pdf_data.get('dob'):
                    extraction_count += 1
                    logger.info("✅ Successfully extracted data from PDF")
                else:
                    logger.info("ℹ️ No MRN/DOB data extracted (may be expected)")
                    
            except Exception as e:
                logger.error(f"Error in PDF extraction: {e}")
        
        logger.info(f"Successfully extracted data from {extraction_count}/{len(test_group)} patients")
        return extraction_count > 0
        
    except Exception as e:
        logger.error(f"Real data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("COMPREHENSIVE OPENAI PDF EXTRACTION TEST")
    logger.info("="*60)
    
    # Test 1: Sample text extraction
    logger.info("\n1. Testing with sample medical document text...")
    sample_test_passed = test_openai_with_sample_text()
    
    # Test 2: Real patient data
    logger.info("\n2. Testing with real patient data...")
    real_data_test_passed = test_with_real_patient_data()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Sample text extraction: {'✅ PASSED' if sample_test_passed else '❌ FAILED'}")
    logger.info(f"Real patient data extraction: {'✅ PASSED' if real_data_test_passed else '❌ FAILED'}")
    
    if sample_test_passed and real_data_test_passed:
        logger.info("🎉 Azure OpenAI PDF extraction is working correctly!")
        return True
    else:
        logger.error("❌ Some tests failed - OpenAI implementation needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
