#!/usr/bin/env python3
"""
RCM API Tester

This script tests the RCM API endpoints to determine the correct HTTP methods.
"""

import requests
import argparse
import logging
from config import Config


def test_rcm_endpoint(base_url: str, headers: dict, patient_id: str, endpoint_type: str) -> dict:
    """Test an RCM endpoint with different HTTP methods"""
    if endpoint_type == 'deleted':
        url = f"{base_url}/api/RCM/rcm/patient/{patient_id}"
        description = "RCM (deleted patient)"
        # For delete operations, try DELETE first, then others
        methods = ['DELETE', 'POST', 'GET', 'PUT']
    else:
        url = f"{base_url}/api/RCM/cron-new-patient/{patient_id}"
        description = "RCM New Patient (kept patient)"
        # For new patient operations, try POST first as specified
        methods = ['POST', 'GET', 'PUT', 'DELETE']
    
    results = {
        'url': url,
        'description': description,
        'results': {}
    }
    
    for method in methods:
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            results['results'][method] = {
                'status_code': response.status_code,
                'success': response.status_code < 400,
                'error': None
            }
            
            if response.status_code < 400:
                print(f"✅ {description} - {method}: {response.status_code}")
            else:
                print(f"❌ {description} - {method}: {response.status_code}")
                
        except Exception as e:
            results['results'][method] = {
                'status_code': None,
                'success': False,
                'error': str(e)
            }
            print(f"❌ {description} - {method}: Error - {e}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Test RCM API endpoints')
    parser.add_argument('--patient-id', required=True, help='Patient ID to test')
    parser.add_argument('--config', action='store_true', help='Show current configuration')
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config()
    
    if args.config:
        print("Current Configuration:")
        print(f"  Base URL: {config.BASE_URL}")
        print(f"  RCM Calls Enabled: {config.ENABLE_RCM_CALLS}")
        print(f"  Request Timeout: {config.REQUEST_TIMEOUT}")
        print("")
    
    print(f"Testing RCM APIs for patient: {args.patient_id}")
    print("=" * 60)
    
    # Test both RCM endpoints
    deleted_results = test_rcm_endpoint(
        config.BASE_URL, 
        config.HEADERS, 
        args.patient_id, 
        'deleted'
    )
    
    print()
    
    kept_results = test_rcm_endpoint(
        config.BASE_URL, 
        config.HEADERS, 
        args.patient_id, 
        'kept'
    )
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    
    # Find working methods
    for result_set in [deleted_results, kept_results]:
        working_methods = [method for method, data in result_set['results'].items() if data['success']]
        if working_methods:
            print(f"✅ {result_set['description']}: {', '.join(working_methods)} methods work")
        else:
            print(f"❌ {result_set['description']}: No methods work")
    
    print("\nRecommendation:")
    if any(result['success'] for result in deleted_results['results'].values()) or \
       any(result['success'] for result in kept_results['results'].values()):
        print("✅ At least one RCM endpoint is working. Keep ENABLE_RCM_CALLS=True")
    else:
        print("❌ No RCM endpoints are working. Consider setting ENABLE_RCM_CALLS=False")


if __name__ == "__main__":
    main()
