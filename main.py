#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for Duplicate Patient Manager

This script provides an interactive interface to run the duplicate patient manager.
It prompts for the PG Company ID and runs the duplicate processing.
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config import Config
from duplicate_patient_manager import DuplicatePatientManager


def main():
    """Main interactive entry point"""
    print("=" * 60)
    print("DUPLICATE PATIENT MANAGER")
    print("=" * 60)
    print()
    
    try:
        # Load configuration
        print("Loading configuration...")
        config = Config()
        print("Configuration loaded successfully")
        print()
        
        # Get PG Company ID from user
        while True:
            pg_company_id = input("Enter PG Company ID: ").strip()
            
            if not pg_company_id:
                print("PG Company ID cannot be empty. Please try again.")
                continue
            
            # Validate format (basic UUID format check)
            if len(pg_company_id) != 36 or pg_company_id.count('-') != 4:
                print("Warning: PG Company ID doesn't look like a valid UUID format.")
                confirm = input("Do you want to continue anyway? (y/n): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    continue
            
            break
        
        print(f"Processing duplicates for PG Company ID: {pg_company_id}")
        print()
        
        # Initialize manager
        manager = DuplicatePatientManager(config)
        
        # Ask for operation mode
        print("Select operation mode:")
        print("1. TEST MODE - Dry run to see what would be processed")
        print("2. PRODUCTION MODE - Actually process and merge duplicates")
        print()
        
        while True:
            mode_choice = input("Enter your choice (1 or 2): ").strip()
            
            if mode_choice == "1":
                print("\nRunning in TEST MODE...")
                # For test mode, just show what would be processed
                test_results = manager.process_duplicates_test_mode(pg_company_id)
                print_test_results(test_results)
                break
            elif mode_choice == "2":
                print("\nPRODUCTION MODE WARNING:")
                print("This will actually merge and delete duplicate patients!")
                print("Make sure you have a backup of your data.")
                confirm = input("Are you sure you want to continue? (yes/no): ").strip().lower()
                
                if confirm == "yes":
                    print("\nRunning in PRODUCTION MODE...")
                    manager.run_production(pg_company_id)
                    print("Production run completed!")
                    print("Check your email for the detailed report.")
                else:
                    print("Production run cancelled.")
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        print("\nCheck the log files for more details.")
        sys.exit(1)


def print_test_results(results):
    """Print test results in a user-friendly format"""
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    print(f"Total Patients: {results.get('total_patients', 0)}")
    print(f"Duplicate Groups Found: {results.get('duplicate_groups_found', 0)}")
    print(f"Patients That Would Be Processed: {results.get('patients_processed', 0)}")
    print(f"Patients That Would Be Deleted: {results.get('patients_deleted', 0)}")
    print(f"Orders That Would Be Moved: {results.get('orders_moved', 0)}")
    print(f"CC Notes That Would Be Moved: {results.get('cc_notes_moved', 0)}")
    
    if results.get('errors'):
        print(f"Errors: {len(results.get('errors', []))}")
    
    print("\n" + "-" * 50)
    print("PROCESSING DETAILS")
    print("-" * 50)
    
    if results.get('processing_details'):
        for detail in results.get('processing_details', []):
            print(f"\nGroup {detail.get('group_number', 'N/A')}:")
            print(f"   Primary Patient: {detail.get('primary_patient_name', 'N/A')} ({detail.get('primary_patient_id', 'N/A')})")
            
            # Show PDF extraction details if available
            if detail.get('pdf_extractions'):
                print(f"   PDF Extraction Results:")
                for extraction in detail.get('pdf_extractions', []):
                    print(f"      {extraction.get('patient_name', 'Unknown')}: MRN='{extraction.get('pdf_mrn', 'Not found')}', DOB='{extraction.get('pdf_dob', 'Not found')}' (Score: {extraction.get('score', 0)})")
            
            deleted_ids = detail.get('deleted_patient_ids', [])
            if deleted_ids:
                print(f"   Would Delete: {len(deleted_ids)} patient(s)")
                for patient_id in deleted_ids:
                    print(f"      - {patient_id}")
            
            print(f"   Orders to Move: {detail.get('moved_orders', 0)}")
            print(f"   CC Notes to Move: {detail.get('moved_cc_notes', 0)}")
            
            if detail.get('errors'):
                print(f"   Errors: {len(detail.get('errors', []))}")
    else:
        print("No duplicate groups found - no action needed!")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
