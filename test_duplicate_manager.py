#!/usr/bin/env python3
"""
Test script for Duplicate Patient Manager

This script allows testing the duplicate patient management functionality
with sample data or specific patient IDs.
"""

import json
import logging
from typing import Dict, Any

from duplicate_patient_manager import DuplicatePatientManager
from config import Config


class DuplicatePatientTester:
    """Test class for duplicate patient management"""
    
    def __init__(self):
        self.config = Config()
        self.manager = DuplicatePatientManager(self.config)
        self.logger = logging.getLogger(__name__)
    
    def test_single_patient(self, patient_id: str) -> Dict[str, Any]:
        """Test processing for a single patient"""
        self.logger.info(f"Testing single patient: {patient_id}")
        
        try:
            # Fetch patient orders and CC notes to verify they exist
            orders = self.manager.fetch_orders(patient_id)
            cc_notes = self.manager.fetch_cc_notes(patient_id)
            
            test_results = {
                'patient_id': patient_id,
                'orders_found': len(orders),
                'cc_notes_found': len(cc_notes),
                'orders_with_ccnote_type': len([o for o in orders if o.get('entityType') == 'CCNote']),
                'regular_orders': len([o for o in orders if o.get('entityType') != 'CCNote']),
                'test_status': 'success',
                'message': f"Patient {patient_id} has {len(orders)} orders and {len(cc_notes)} CC notes"
            }
            
            # Log detailed information
            self.logger.info(f"Patient {patient_id} test results:")
            self.logger.info(f"  - Total orders: {len(orders)}")
            self.logger.info(f"  - Regular orders: {len([o for o in orders if o.get('entityType') != 'CCNote'])}")
            self.logger.info(f"  - CCNote type orders: {len([o for o in orders if o.get('entityType') == 'CCNote'])}")
            self.logger.info(f"  - CC Notes: {len(cc_notes)}")
            
            return test_results
            
        except Exception as e:
            error_msg = f"Error testing patient {patient_id}: {e}"
            self.logger.error(error_msg)
            return {
                'patient_id': patient_id,
                'test_status': 'error',
                'error_message': error_msg
            }
    
    def test_duplicate_detection(self, pg_company_id: str, limit: int = 10) -> Dict[str, Any]:
        """Test duplicate detection logic without processing"""
        self.logger.info(f"Testing duplicate detection for PG Company ID: {pg_company_id}")
        
        try:
            # Fetch patients
            patients = self.manager.fetch_patients(pg_company_id)
            if not patients:
                return {
                    'test_status': 'no_data',
                    'message': 'No patients found for the given PG Company ID'
                }
            
            # Limit patients for testing
            test_patients = patients[:limit] if len(patients) > limit else patients
            
            # Group duplicates without processing
            duplicate_groups = self.manager.group_duplicates(test_patients)
            
            test_results = {
                'pg_company_id': pg_company_id,
                'total_patients_available': len(patients),
                'patients_tested': len(test_patients),
                'duplicate_groups_found': len(duplicate_groups),
                'test_status': 'success',
                'duplicate_groups_details': []
            }
            
            # Add details for each duplicate group
            for i, group in enumerate(duplicate_groups, 1):
                group_details = {
                    'group_number': i,
                    'patients_in_group': len(group),
                    'patients': []
                }
                
                for patient in group:
                    agency_info = patient.get('agencyInfo', {})
                    patient_info = {
                        'id': patient['id'],
                        'name': f"{agency_info.get('patientFName', '')} {agency_info.get('patientLName', '')}",
                        'dob': agency_info.get('dob', ''),
                        'mrn': agency_info.get('medicalRecordNo', ''),
                        'total_orders': agency_info.get('totalOrders', '0'),
                        'company_id': agency_info.get('companyId', ''),
                        'pg_company_id': agency_info.get('pgcompanyID', '')
                    }
                    group_details['patients'].append(patient_info)
                
                test_results['duplicate_groups_details'].append(group_details)
            
            # Log results
            self.logger.info(f"Duplicate detection test results:")
            self.logger.info(f"  - Total patients available: {len(patients)}")
            self.logger.info(f"  - Patients tested: {len(test_patients)}")
            self.logger.info(f"  - Duplicate groups found: {len(duplicate_groups)}")
            
            return test_results
            
        except Exception as e:
            error_msg = f"Error testing duplicate detection: {e}"
            self.logger.error(error_msg)
            return {
                'test_status': 'error',
                'error_message': error_msg
            }
    
    def test_pdf_extraction(self, patient_id: str) -> Dict[str, Any]:
        """Test PDF extraction for MRN and DOB verification"""
        self.logger.info(f"Testing PDF extraction for patient: {patient_id}")
        
        try:
            # Get PDF verification data
            pdf_data = self.manager.verify_patient_data_from_pdf({'id': patient_id})
            
            test_results = {
                'patient_id': patient_id,
                'pdf_extraction_results': pdf_data,
                'test_status': 'success' if pdf_data.get('mrn') or pdf_data.get('dob') else 'no_data',
                'message': f"Extracted MRN: {pdf_data.get('mrn', 'Not found')}, DOB: {pdf_data.get('dob', 'Not found')}"
            }
            
            self.logger.info(f"PDF extraction test results for {patient_id}:")
            self.logger.info(f"  - MRN: {pdf_data.get('mrn', 'Not found')}")
            self.logger.info(f"  - DOB: {pdf_data.get('dob', 'Not found')}")
            
            return test_results
            
        except Exception as e:
            error_msg = f"Error testing PDF extraction for {patient_id}: {e}"
            self.logger.error(error_msg)
            return {
                'test_status': 'error',
                'error_message': error_msg
            }
    
    def test_name_matching(self) -> Dict[str, Any]:
        """Test fuzzy name matching logic"""
        self.logger.info("Testing name matching logic")
        
        test_cases = [
            ("John Smith", "Jon Smith", "Should match - minor spelling difference"),
            ("Mary Johnson", "Mary Johnston", "Should match - slight variation"),
            ("Robert Brown", "Bob Brown", "Might match - common nickname"),
            ("Elizabeth Davis", "Liz Davis", "Might match - common nickname"),
            ("Michael Wilson", "John Wilson", "Should not match - different first name"),
            ("Sarah Miller", "Sarah Miller", "Should match - exact match"),
            ("James Anderson", "Anderson, James", "Should match - different format"),
            ("", "John Doe", "Should not match - empty name"),
            ("A", "B", "Should not match - too short")
        ]
        
        test_results = {
            'test_status': 'success',
            'test_cases': []
        }
        
        for name1, name2, description in test_cases:
            similarity = self.manager.calculate_name_similarity(name1, name2)
            is_match = similarity >= self.config.NAME_SIMILARITY_THRESHOLD
            
            case_result = {
                'name1': name1,
                'name2': name2,
                'similarity_score': similarity,
                'is_match': is_match,
                'description': description,
                'threshold': self.config.NAME_SIMILARITY_THRESHOLD
            }
            
            test_results['test_cases'].append(case_result)
            
            self.logger.info(f"Name matching: '{name1}' vs '{name2}' = {similarity}% ({'Match' if is_match else 'No match'})")
        
        return test_results
    
    def run_comprehensive_test(self, pg_company_id: str, test_patient_id: str = None) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        self.logger.info("Running comprehensive test suite")
        
        comprehensive_results = {
            'test_timestamp': logging.Formatter().formatTime(logging.LogRecord(
                'test', logging.INFO, '', 0, '', (), None
            )),
            'tests_run': []
        }
        
        # Test 1: Name matching logic
        self.logger.info("Running name matching test...")
        name_test = self.test_name_matching()
        comprehensive_results['tests_run'].append({
            'test_name': 'Name Matching Logic',
            'results': name_test
        })
        
        # Test 2: Duplicate detection (without processing)
        self.logger.info("Running duplicate detection test...")
        duplicate_test = self.test_duplicate_detection(pg_company_id, limit=20)
        comprehensive_results['tests_run'].append({
            'test_name': 'Duplicate Detection',
            'results': duplicate_test
        })
        
        # Test 3: Single patient test (if provided)
        if test_patient_id:
            self.logger.info("Running single patient test...")
            patient_test = self.test_single_patient(test_patient_id)
            comprehensive_results['tests_run'].append({
                'test_name': 'Single Patient Analysis',
                'results': patient_test
            })
            
            # Test 4: PDF extraction test
            self.logger.info("Running PDF extraction test...")
            pdf_test = self.test_pdf_extraction(test_patient_id)
            comprehensive_results['tests_run'].append({
                'test_name': 'PDF Extraction',
                'results': pdf_test
            })
        
        return comprehensive_results
    
    def print_test_results(self, results: Dict[str, Any]) -> None:
        """Pretty print test results"""
        print("\n" + "="*80)
        print("DUPLICATE PATIENT MANAGER - TEST RESULTS")
        print("="*80)
        
        if 'tests_run' in results:
            for test_info in results['tests_run']:
                test_name = test_info['test_name']
                test_results = test_info['results']
                
                print(f"\n📋 {test_name}")
                print("-" * (len(test_name) + 3))
                
                if test_name == 'Name Matching Logic':
                    for case in test_results.get('test_cases', []):
                        status = "✅" if case['is_match'] else "❌"
                        print(f"{status} '{case['name1']}' vs '{case['name2']}' = {case['similarity_score']}%")
                
                elif test_name == 'Duplicate Detection':
                    print(f"Total patients available: {test_results.get('total_patients_available', 0)}")
                    print(f"Patients tested: {test_results.get('patients_tested', 0)}")
                    print(f"Duplicate groups found: {test_results.get('duplicate_groups_found', 0)}")
                    
                    for group in test_results.get('duplicate_groups_details', []):
                        print(f"\n  Group {group['group_number']} ({group['patients_in_group']} patients):")
                        for patient in group['patients']:
                            print(f"    - {patient['name']} ({patient['id']}) | MRN: {patient['mrn']} | DOB: {patient['dob']}")
                
                elif test_name == 'Single Patient Analysis':
                    print(f"Patient ID: {test_results.get('patient_id', 'N/A')}")
                    print(f"Orders found: {test_results.get('orders_found', 0)}")
                    print(f"CC Notes found: {test_results.get('cc_notes_found', 0)}")
                    print(f"Status: {test_results.get('test_status', 'unknown')}")
                
                elif test_name == 'PDF Extraction':
                    pdf_results = test_results.get('pdf_extraction_results', {})
                    print(f"Patient ID: {test_results.get('patient_id', 'N/A')}")
                    print(f"Extracted MRN: {pdf_results.get('mrn', 'Not found')}")
                    print(f"Extracted DOB: {pdf_results.get('dob', 'Not found')}")
                    print(f"Status: {test_results.get('test_status', 'unknown')}")
                
                # Show errors if any
                if 'error_message' in test_results:
                    print(f"❌ Error: {test_results['error_message']}")
        
        else:
            # Single test result
            print(json.dumps(results, indent=2))
        
        print("\n" + "="*80)


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Duplicate Patient Manager')
    parser.add_argument('--pg-company-id', required=True, 
                       help='PG Company ID to test')
    parser.add_argument('--test-patient-id', 
                       help='Specific patient ID to test (optional)')
    parser.add_argument('--test-type', 
                       choices=['comprehensive', 'duplicate-detection', 'single-patient', 'name-matching', 'pdf-extraction'],
                       default='comprehensive',
                       help='Type of test to run')
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = DuplicatePatientTester()
    
    try:
        if args.test_type == 'comprehensive':
            results = tester.run_comprehensive_test(args.pg_company_id, args.test_patient_id)
        elif args.test_type == 'duplicate-detection':
            results = tester.test_duplicate_detection(args.pg_company_id)
        elif args.test_type == 'single-patient':
            if not args.test_patient_id:
                print("Error: --test-patient-id required for single-patient test")
                return
            results = tester.test_single_patient(args.test_patient_id)
        elif args.test_type == 'name-matching':
            results = tester.test_name_matching()
        elif args.test_type == 'pdf-extraction':
            if not args.test_patient_id:
                print("Error: --test-patient-id required for pdf-extraction test")
                return
            results = tester.test_pdf_extraction(args.test_patient_id)
        
        # Print results
        tester.print_test_results(results)
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
