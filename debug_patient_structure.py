#!/usr/bin/env python3
"""
Debug script to check patient data structure
"""

import json
import requests
from config import Config

def debug_patient_structure():
    config = Config()
    
    # Fetch a few patients to see the data structure
    pg_company_id = "c0926069-e956-4ed5-8775-1f462f6cff36"
    url = f"{config.BASE_URL}/api/Patient/company/pg/{pg_company_id}"
    
    try:
        response = requests.get(url, headers=config.HEADERS, timeout=30)
        response.raise_for_status()
        
        patients = response.json()
        print(f"Total patients: {len(patients)}")
        
        if patients:
            print("\n=== FIRST PATIENT STRUCTURE ===")
            print(json.dumps(patients[0], indent=2))
            
            print("\n=== PATIENT DATA FIELDS ===")
            first_patient = patients[0]
            print("Top level keys:", list(first_patient.keys()))
            
            if 'agencyInfo' in first_patient:
                agency_info = first_patient['agencyInfo']
                print("Agency info keys:", list(agency_info.keys()))
                print(f"Patient Name: {agency_info.get('patientFName', 'N/A')} {agency_info.get('patientLName', 'N/A')}")
                print(f"DOB: {agency_info.get('dob', 'N/A')}")
                print(f"MRN: {agency_info.get('medicalRecordNo', 'N/A')}")
                print(f"Company ID: {agency_info.get('companyId', 'N/A')}")
                print(f"PG Company ID: {agency_info.get('pgcompanyID', 'N/A')}")
            
            # Check for alternative field names
            print("\n=== CHECKING ALTERNATIVE FIELD NAMES ===")
            def search_for_dob_mrn(data, path=""):
                if isinstance(data, dict):
                    for key, value in data.items():
                        current_path = f"{path}.{key}" if path else key
                        if any(term in key.lower() for term in ['dob', 'birth', 'date']):
                            print(f"Found date field: {current_path} = {value}")
                        if any(term in key.lower() for term in ['mrn', 'medical', 'record']):
                            print(f"Found MRN field: {current_path} = {value}")
                        if any(term in key.lower() for term in ['fname', 'first', 'lname', 'last', 'name']):
                            print(f"Found name field: {current_path} = {value}")
                        if isinstance(value, dict):
                            search_for_dob_mrn(value, current_path)
                elif isinstance(data, list) and data:
                    if isinstance(data[0], dict):
                        search_for_dob_mrn(data[0], f"{path}[0]")
            
            search_for_dob_mrn(first_patient)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_patient_structure()
