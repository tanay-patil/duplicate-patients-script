#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Duplicate Patient Manager

This script processes all specified PG Company IDs automatically in production mode
without requiring user confirmation for each step.
"""

import sys
import os
import logging
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config import Config
from duplicate_patient_manager import DuplicatePatientManager


def setup_logging():
    """Set up comprehensive logging"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Set up logging with both console and file output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'logs/automated_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
        ]
    )


def main():
    """Main automated processing function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # List of all PG Company IDs to process
    pg_companies = [
        # Texas/Southern Region
        {"name": "HousecallMD", "id": "bc3a6a28-dd03-4cf3-95ba-2c5976619818"},
        {"name": "Los Cerros", "id": "9d8d2765-0b51-489b-868c-a217b4283c62"},
        {"name": "Paragon Medical Associates", "id": "84e35202-3422-4de4-b5cb-efe5461b1312"},
        {"name": "Rocky Mountain", "id": "4e594a84-7340-469e-82fb-b41b91930db5"},
        {"name": "Brownfield Family Physicians", "id": "b62429db-642c-4fdb-9bf3-29e381d20e22"},
        {"name": "WellLife Family Medicine", "id": "1a959ae5-7ba2-47e5-b044-64690eeced93"},
        {"name": "APPLEMD", "id": "83de8c79-1a28-4d0b-90bc-5deaf95949e5"},
        {"name": "ANAND BALASUBRIMUNIUM", "id": "1726e467-f4b0-4c11-b2b7-a39eb1328d91"},
        {"name": "WoundCentrics, LLC", "id": "0367ce80-57a9-45e7-8afe-18f665a6a640"},
        {"name": "Visiting Practitioners And Palliative Care LLC", "id": "f6464e98-d46b-4c7a-a9bc-254c02aa8e1c"},
        {"name": "Responsive Infectious Diseases Solutions", "id": "ee74f247-b46e-480c-a4e4-9ae6b8a5dc35"},
        {"name": "Doctor at your service", "id": "e749dda4-60ab-48d3-afc6-728a15d74182"},
        {"name": "san antonio family phsician", "id": "6c2414e8-b2d3-4d94-953e-967a64c31488"},
        {"name": "UT Health Geriatrics & Supportive Care Clinic", "id": "b50483ad-042c-4d64-96d7-4427c7862f9e"},
        {"name": "Centric Physicians Group", "id": "5bce99a2-a71f-48e4-9c06-c16d9ab78ad5"},
        {"name": "Goldstein Alasdair MD", "id": "ea4c3d61-28fa-473f-8bdd-685075343711"},
        {"name": "BSZ Medical PA", "id": "3e387a9f-5535-4984-9419-483bed5e63f1"},
        {"name": "Boyer family practice", "id": "8b15ea65-269e-412f-88ce-785959be023f"},
        {"name": "Clinic of north Texas", "id": "398b825d-5e6d-4a86-88df-79992a36f536"},
        {"name": "Diverse care", "id": "daf14002-92e8-4024-b6bf-62cd1a2f8606"},
        {"name": "Doctors at Home - Mary Snellings MD", "id": "de385408-1cd6-46a2-be58-ff4b8eeeddc7"},
        {"name": "Morning Star Healthcare Services PA", "id": "9c9bd7d0-bd70-4197-98f7-a77b4e781ab1"},
        {"name": "Spectrum (Community First Primary Care)", "id": "6f4180aa-b472-4d5c-b7aa-98e06bb4fd6f"},
        {"name": "Royal V.P., LLC", "id": "eaba3c1c-217f-458d-aa2f-172e3ffbab1e"},
        {"name": "CityWide Housecalls, LLC", "id": "534ca7a5-2db0-4c75-8988-89f73064c5e5"},
        {"name": "Prime MD Geriatrics", "id": "ef8847e7-ed2a-4dc0-a08b-49b1d6b2b5f7"},
        {"name": "Americare Medical Group", "id": "c147e1f1-ccdb-4e22-8526-60a93ad4a678"},
        {"name": "Texas Infectious Disease Institute", "id": "a3b8a6c5-db61-42b4-8eee-64e1098c0336"},
        {"name": "Atrium HouseCall", "id": "bb158a70-b51a-4008-9600-e94484485b61"},
        
        # Oklahoma Region
        {"name": "Traveling at doctors", "id": "8cd766e5-6e19-492e-a1a9-6595d81d20ee"},
        {"name": "SSM Health Bone & Joint Hospital.", "id": "3bc728e7-6839-4807-92ed-bb6c712020de"},
        {"name": "The Clinic @ Central Oklahoma Family Medical Center", "id": "3642cb84-6d4f-492c-8be1-4dd388bcea19"},
        {"name": "SSM Health Shawnee", "id": "ee54c7f2-a7ba-4b9a-90b0-7df96330b9f7"},
        {"name": "Community Physician Group-CPG Clinics", "id": "45d72b92-6c6c-4bef-84f0-a36852d5f868"},
        {"name": "Infectious Diseases Consultants of Oklahoma City- (Idcokc)", "id": "198e2b2d-c22a-415d-9ebd-9656091d0308"},
        {"name": "Pushmataha Family Medical Center", "id": "ecad2da6-91a7-4e26-8152-58d588eab134"},
        {"name": "Crescent Infectious Diseases", "id": "f86dc96a-777c-4bdc-ae87-f147b1e5568e"},
        {"name": "Norman Regional - Ortho Central", "id": "3c002ed5-f9b5-4d07-914a-4856c268c977"},
        {"name": "Triton Health PLLC Dr. Sullivan, Cary", "id": "d09df8cc-a549-4229-a03a-ce29fb09aea2"},
        {"name": "Internal Medicine Associates OKC", "id": "c6ad87d9-79de-49bd-aa0a-6ef01400a83d"},
        {"name": "Chickasaw Nation Medical Center", "id": "e8f2df67-c5a5-4c74-9daa-d9b41d8eb5d7"},
        {"name": "Southeast Oklahoma Medical Clinic - Dr. Richard Helton", "id": "108bbba4-5d5d-41d9-b1c6-0eaac5538f6c"},
        {"name": "Terry Draper / Restore Family Medical clinic", "id": "be52e9cc-f825-4ff2-b336-508d6b9ad63b"},
        {"name": "TPCH Practice/ Dr. Tradewell", "id": "8e53f8ea-bb0b-472f-8560-0b9b4808c0fa"},
        {"name": "Community Health Centers,Inc Oklahoma", "id": "69f909d4-b4c5-4d8a-8d2e-eb52d467ef3c"},
        {"name": "KATES, LINDSAY / Primary care of Ada", "id": "2aeb18f5-4461-496d-8f74-66ba6f269cd3"},
        {"name": "Anibal Avila MA P,C", "id": "13c9e1d2-fbde-498a-b384-f530c29d0745"},
        {"name": "Doctors 2 U", "id": "ced25ca7-8e1e-401b-b8fe-d181f688ac90"},
        {"name": "Grace At Home", "id": "2f607136-c370-422c-890d-f01bdaba6bae"},
        {"name": "Covenant care", "id": "ec35b120-0883-4d1f-b63d-89bd43d6d89e"},
        {"name": "MD Primary care", "id": "29e46ad6-8ca8-400b-b049-48c17c0b831d"},
        {"name": "Prima CARE", "id": "d10f46ad-225d-4ba2-882c-149521fcead5"},
        {"name": "Hawthorn", "id": "4b51c8b7-c8c4-4779-808c-038c057f026b"},
        {"name": "Trucare", "id": "7c40b6f6-5874-4ab8-96d4-e03b0d2f8201"},
        
        # Massachusetts/Eastern Region  
        {"name": "AcoHealth", "id": "d074279d-8ff6-47ab-b340-04f21c0f587e"},
        {"name": "Carney Hospital", "id": "14761337-cd76-4e76-8bdd-18a96465624e"},
        {"name": "Dr. Resil Claude", "id": "042a7278-25b6-4a9b-a18d-1981ab0daf11"},
        {"name": "Health Quality Primary Care", "id": "f0d98fdc-c432-4e05-b75e-af146aa0e27d"},
        {"name": "Caring", "id": "03657233-8677-4c81-92c8-c19c3f64fc84"},
        {"name": "BestSelf Primary Care", "id": "c5c1a894-08ac-4cb9-bfd1-0ad1384b890e"},
        {"name": "CARE DIMENSION", "id": "da7d760b-e3a8-4c92-9006-eca464ce8e1e"},
        {"name": "Riverside Medical Group", "id": "ca5314fe-cf71-42e5-9482-81507666328c"},
        {"name": "Family medical associates", "id": "38511e46-cc15-4856-92bc-718c5ec56cbf"},
        {"name": "Upham", "id": "acfcd97b-0533-4c95-9f5d-4744c5f9c64c"},
        {"name": "Orthopaedic Specialists of Massachusetts", "id": "cdabc85a-9c13-4fae-9dbf-d2e22e12f466"},
        {"name": "Brockton", "id": "d80b9f6a-d8e8-42bc-8db7-043675a5b86b"},
        {"name": "Total Family Healthcare Clinic PLLC", "id": "7ec965fe-9777-4d52-8124-b056b4d90224"},
        {"name": "Lowell", "id": "b92e8240-61f7-475f-8cbe-f1442b6389b5"},
        {"name": "Associates in Internal Medicine - Norwood", "id": "0245a889-31da-445b-9f1e-51f97ea6d37e"},
        {"name": "Northeast Medical Group", "id": "e7ca529f-bc5e-4706-b61f-0f682a3f6e23"},
        {"name": "New Bedford Internal Medicine and Geriatrics", "id": "716be0f8-9710-4fee-90b2-09dc30f229c9"},
        {"name": "Renaissance Primary Care", "id": "251b9883-1316-4689-bb95-9124cc1e3e43"},
        {"name": "Hyde Park Health Associates", "id": "a48aa403-d9c4-4778-88c5-36e68fa5f246"},
        {"name": "Boston Senior Medicine", "id": "61e6dd93-452b-41b0-aca4-8d67fbe71e78"},
        {"name": "BIDMC", "id": "0c2c11e0-ce99-4282-9172-7d06c7a12dda"},
        {"name": "Bowdoin", "id": "5f173aaa-338d-4510-9d2d-c856d8771aa8"},
        {"name": "St. Elizabeth Medical Center Orthopedics", "id": "ceece087-093e-421d-92c0-b1aff03405e6"},
        {"name": "Neurology Center Of New England, PC", "id": "c0926069-e956-4ed5-8775-1f462f6cff36"}
    ]
    
    print("=" * 80)
    print("AUTOMATED DUPLICATE PATIENT PROCESSING - PRODUCTION MODE")
    print(f"Processing {len(pg_companies)} PG Companies")
    print("=" * 80)
    
    logger.info("=" * 80)
    logger.info("STARTING AUTOMATED DUPLICATE PATIENT PROCESSING")
    logger.info(f"Total PG Companies to process: {len(pg_companies)}")
    logger.info("=" * 80)
    
    # Initialize tracking variables
    total_companies = len(pg_companies)
    successful_companies = 0
    failed_companies = 0
    
    # Processing summary for final report
    processing_summary = []
    
    try:
        # Load configuration
        config = Config()
        manager = DuplicatePatientManager(config)
        
        # Process each company
        for i, company in enumerate(pg_companies, 1):
            company_name = company["name"]
            company_id = company["id"]
            
            print(f"\n{'='*60}")
            print(f"[{i}/{total_companies}] Processing: {company_name}")
            print(f"PG Company ID: {company_id}")
            print(f"{'='*60}")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"[{i}/{total_companies}] PROCESSING: {company_name}")
            logger.info(f"PG Company ID: {company_id}")
            logger.info(f"{'='*60}")
            
            company_start_time = datetime.now()
            
            try:
                # Run production processing (no confirmation needed)
                logger.info(f"Starting production processing for {company_name}...")
                manager.run_production(company_id, company_name)
                
                processing_time = datetime.now() - company_start_time
                successful_companies += 1
                
                logger.info(f"✓ COMPLETED: {company_name} (Processing time: {processing_time})")
                print(f"✓ COMPLETED: {company_name}")
                
                # Add to summary
                processing_summary.append({
                    'company_name': company_name,
                    'company_id': company_id,
                    'status': 'SUCCESS',
                    'processing_time': str(processing_time),
                    'error': None
                })
                
            except Exception as e:
                processing_time = datetime.now() - company_start_time
                failed_companies += 1
                error_msg = str(e)
                
                logger.error(f"✗ FAILED: {company_name} - {error_msg} (Processing time: {processing_time})")
                print(f"✗ FAILED: {company_name} - {error_msg}")
                
                # Add to summary
                processing_summary.append({
                    'company_name': company_name,
                    'company_id': company_id,
                    'status': 'FAILED',
                    'processing_time': str(processing_time),
                    'error': error_msg
                })
                
                # Continue with next company even if this one failed
                continue
        
        # Final summary
        print(f"\n{'='*80}")
        print("AUTOMATED PROCESSING COMPLETED")
        print(f"{'='*80}")
        print(f"Total Companies: {total_companies}")
        print(f"Successful: {successful_companies}")
        print(f"Failed: {failed_companies}")
        print(f"Success Rate: {(successful_companies/total_companies*100):.1f}%")
        print(f"{'='*80}")
        
        logger.info(f"\n{'='*80}")
        logger.info("AUTOMATED PROCESSING COMPLETED")
        logger.info(f"{'='*80}")
        logger.info(f"Total Companies: {total_companies}")
        logger.info(f"Successful: {successful_companies}")
        logger.info(f"Failed: {failed_companies}")
        logger.info(f"Success Rate: {(successful_companies/total_companies*100):.1f}%")
        
        # Detailed summary
        logger.info(f"\nDETAILED RESULTS:")
        for summary in processing_summary:
            status_symbol = "✓" if summary['status'] == 'SUCCESS' else "✗"
            logger.info(f"{status_symbol} {summary['company_name']}: {summary['status']} ({summary['processing_time']})")
            if summary['error']:
                logger.info(f"    Error: {summary['error']}")
        
        logger.info(f"{'='*80}")
        
        if failed_companies == 0:
            print("🎉 ALL COMPANIES PROCESSED SUCCESSFULLY!")
            logger.info("🎉 ALL COMPANIES PROCESSED SUCCESSFULLY!")
        else:
            print(f"⚠️  {failed_companies} companies had processing errors - check logs for details")
            logger.warning(f"⚠️  {failed_companies} companies had processing errors")
        
        print("\nDetailed reports and logs have been generated in the output/ and logs/ directories.")
        logger.info("Processing completed. Check output/ directory for reports and logs/ for detailed logs.")
            
    except Exception as e:
        logger.error(f"Critical error in automated processing: {e}")
        print(f"❌ Critical error: {e}")
        return 1
    
    return 0 if failed_companies == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
