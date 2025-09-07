#!/usr/bin/env python3
"""
Duplicate Patient Manager

This script manages duplicate patients based on PG Company ID by:
1. Fetching all patients for a given PG Company ID
2. Identifying duplicates using fuzzy matching on name, DOB, MRN, Company ID, and PG Company ID
3. Merging duplicates by moving orders and CCNotes to the primary patient
4. Deleting duplicate patients
5. Calling RCM APIs for both patients
6. Sending a structured report via email

Author: DA Team
Date: September 2025
"""

import json
import logging
import sys
import base64
import io
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import argparse

import requests
import pdfplumber
from fuzzywuzzy import fuzz
from openai import AzureOpenAI

# OCR imports
try:
    import pytesseract
    from PIL import Image
    import pdf2image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: OCR libraries not available. Install pytesseract, PIL, and pdf2image for OCR fallback.")

from config import Config
from email_sender import EmailSender
from report_generator import ReportGenerator
from excel_generator import ExcelReportGenerator


class DuplicatePatientManager:
    """Main class for managing duplicate patients"""
    
    def __init__(self, config: Config):
        self.config = config
        self.output_dirs = self._create_output_directories()
        self.logger = self._setup_logging()
        self.openai_client = self._setup_openai()
        self.email_sender = EmailSender(config)
        self.report_generator = ReportGenerator()
        self.excel_generator = ExcelReportGenerator()
    
    def _create_output_directories(self) -> dict:
        """Create output directory structure and return paths"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_base = os.path.join(base_dir, "output")
        
        # Create timestamp for this run
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Define directory structure
        dirs = {
            'base': output_base,
            'logs': os.path.join(output_base, "logs"),
            'reports': os.path.join(output_base, "reports"),
            'excel': os.path.join(output_base, "reports", "excel"),
            'html': os.path.join(output_base, "reports", "html"),
            'temp': os.path.join(output_base, "temp")
        }
        
        # Create all directories
        for dir_path in dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        return dirs
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration with proper Unicode handling"""
        # Create log file in logs directory
        log_filename = f'duplicate_manager_{datetime.now().strftime("%Y%m%d")}.log'
        log_path = os.path.join(self.output_dirs['logs'], log_filename)
        
        # Create handlers with UTF-8 encoding
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        
        # Create console handler with UTF-8 encoding
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Set format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Configure logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Add new handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger
    
    def _setup_openai(self) -> AzureOpenAI:
        """Setup Azure OpenAI client"""
        return AzureOpenAI(
            api_key=self.config.AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=self.config.AZURE_OPENAI_ENDPOINT
        )
    
    def fetch_patients(self, pg_company_id: str) -> List[Dict[str, Any]]:
        """Fetch all patients for a given PG Company ID"""
        try:
            url = f"{self.config.BASE_URL}/api/Patient/company/pg/{pg_company_id}"
            response = requests.get(url, headers=self.config.HEADERS, timeout=30)
            response.raise_for_status()
            
            patients = response.json()
            self.logger.info(f"Fetched {len(patients)} patients for PG Company ID: {pg_company_id}")
            return patients
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching patients: {e}")
            raise
    
    def calculate_name_similarity(self, fname1: str, lname1: str, fname2: str, lname2: str) -> Dict[str, Any]:
        """
        Calculate name similarity between two patients with strict matching rules
        Returns detailed matching information including individual name component matches
        """
        # Clean and normalize names
        fname1_clean = fname1.strip().lower() if fname1 else ""
        lname1_clean = lname1.strip().lower() if lname1 else ""
        fname2_clean = fname2.strip().lower() if fname2 else ""
        lname2_clean = lname2.strip().lower() if lname2 else ""
        
        # Return early if any name is missing
        if not (fname1_clean and lname1_clean and fname2_clean and lname2_clean):
            return {
                'overall_similarity': 0,
                'is_name_match': False,
                'match_type': 'incomplete_data',
                'fname_similarity': 0,
                'lname_similarity': 0,
                'details': 'Missing name components'
            }
        
        # Calculate individual name similarities
        fname_similarity = fuzz.ratio(fname1_clean, fname2_clean)
        lname_similarity = fuzz.ratio(lname1_clean, lname2_clean)
        
        # Check for name interchange (first name matches last name and vice versa)
        fname_lname_cross = fuzz.ratio(fname1_clean, lname2_clean)
        lname_fname_cross = fuzz.ratio(lname1_clean, fname2_clean)
        
        # Determine match type and overall similarity
        match_details = {
            'fname_similarity': fname_similarity,
            'lname_similarity': lname_similarity,
            'fname_lname_cross': fname_lname_cross,
            'lname_fname_cross': lname_fname_cross,
            'is_name_match': False,
            'match_type': 'no_match',
            'overall_similarity': 0,
            'details': ''
        }
        
        # Case 1: Direct match (first names match AND last names match)
        if fname_similarity >= self.config.NAME_SIMILARITY_THRESHOLD and lname_similarity >= self.config.NAME_SIMILARITY_THRESHOLD:
            match_details['is_name_match'] = True
            match_details['match_type'] = 'direct_match'
            match_details['overall_similarity'] = min(fname_similarity, lname_similarity)
            match_details['details'] = f"Direct match: {fname1_clean} {lname1_clean} ≈ {fname2_clean} {lname2_clean}"
        
        # Case 2: Very high similarity match (for very similar names like Mary/Marie)
        elif fname_similarity >= 90 and lname_similarity >= self.config.NAME_SIMILARITY_THRESHOLD:
            match_details['is_name_match'] = True
            match_details['match_type'] = 'high_similarity_match'
            match_details['overall_similarity'] = min(fname_similarity, lname_similarity)
            match_details['details'] = f"High similarity match: {fname1_clean} {lname1_clean} ≈ {fname2_clean} {lname2_clean}"
        
        # Case 3: Interchange match (first name of patient1 matches last name of patient2 AND vice versa)
        elif fname_lname_cross >= self.config.NAME_SIMILARITY_THRESHOLD and lname_fname_cross >= self.config.NAME_SIMILARITY_THRESHOLD:
            match_details['is_name_match'] = True
            match_details['match_type'] = 'interchange_match'
            match_details['overall_similarity'] = min(fname_lname_cross, lname_fname_cross)
            match_details['details'] = f"Interchange match: {fname1_clean} {lname1_clean} ≈ {lname2_clean} {fname2_clean}"
        
        # Case 4: No match - don't consider as duplicate even if one name matches
        else:
            # Calculate best possible similarity for logging
            best_similarity = max(fname_similarity, lname_similarity, fname_lname_cross, lname_fname_cross)
            match_details['overall_similarity'] = best_similarity
            match_details['details'] = f"No sufficient match: best similarity {best_similarity}%"
        
        self.logger.debug(f"Name comparison: {fname1_clean} {lname1_clean} vs {fname2_clean} {lname2_clean} -> {match_details['match_type']} ({match_details['overall_similarity']}%)")
        
        return match_details
    
    def test_name_matching(self, fname1: str, lname1: str, fname2: str, lname2: str) -> None:
        """Test name matching logic with provided names"""
        print(f"\n=== Testing Name Matching ===")
        print(f"Patient 1: {fname1} {lname1}")
        print(f"Patient 2: {fname2} {lname2}")
        
        result = self.calculate_name_similarity(fname1, lname1, fname2, lname2)
        
        print(f"Result: {result['match_type']} (Similarity: {result['overall_similarity']}%)")
        print(f"Is Match: {result['is_name_match']}")
        print(f"Details: {result['details']}")
        print(f"Individual Scores:")
        print(f"  First Name: {result['fname_similarity']}%")
        print(f"  Last Name: {result['lname_similarity']}%")
        print(f"  Cross Match 1: {result['fname_lname_cross']}%") 
        print(f"  Cross Match 2: {result['lname_fname_cross']}%")
        print("=" * 40)

    def are_patients_duplicates(self, patient1: Dict[str, Any], patient2: Dict[str, Any]) -> Dict[str, Any]:
        """Check if two patients are duplicates and return match details"""
        agency1 = patient1.get('agencyInfo', {})
        agency2 = patient2.get('agencyInfo', {})
        
        # Extract relevant fields
        fname1 = agency1.get('patientFName', '').strip()
        lname1 = agency1.get('patientLName', '').strip()
        fname2 = agency2.get('patientFName', '').strip()
        lname2 = agency2.get('patientLName', '').strip()
        
        dob1 = agency1.get('dob', '')
        dob2 = agency2.get('dob', '')
        
        mrn1 = agency1.get('medicalRecordNo', '')
        mrn2 = agency2.get('medicalRecordNo', '')
        
        company_id1 = agency1.get('companyId', '')
        company_id2 = agency2.get('companyId', '')
        
        pg_company_id1 = agency1.get('pgcompanyID', '')
        pg_company_id2 = agency2.get('pgcompanyID', '')
        
        # Calculate name similarity using improved logic
        name_match_result = self.calculate_name_similarity(fname1, lname1, fname2, lname2)
        name_match = name_match_result['is_name_match']
        name_similarity = name_match_result['overall_similarity']
        
        # Match criteria for other fields
        dob_match = dob1 == dob2 if dob1 and dob2 else False
        mrn_match = mrn1 == mrn2 if mrn1 and mrn2 else False
        company_match = company_id1 == company_id2 if company_id1 and company_id2 else False
        pg_company_match = pg_company_id1 == pg_company_id2 if pg_company_id1 and pg_company_id2 else False
        
        # Enhanced logging for debugging
        patient1_name = f"{fname1} {lname1}".strip()
        patient2_name = f"{fname2} {lname2}".strip()
        
        if name_match:
            self.logger.debug(f"Name MATCH: '{patient1_name}' vs '{patient2_name}' - {name_match_result['match_type']} ({name_similarity}%)")
        else:
            self.logger.debug(f"Name NO MATCH: '{patient1_name}' vs '{patient2_name}' - {name_match_result['details']}")
        
        # Determine if duplicate - Enhanced criteria to support Name+MRN or Name+DOB matching
        # Case 1: Traditional matching - Name match + PG Company match + at least one other field
        traditional_match = (
            name_match and 
            pg_company_match and
            (dob_match or mrn_match or company_match)
        )
        
        # Case 2: Name+MRN match (even if DOB is different or missing)
        name_mrn_match = (
            name_match and
            mrn_match and
            mrn1 and mrn2  # Both must have MRN values
        )
        
        # Case 3: Name+DOB match (even if MRN is different or missing)  
        name_dob_match = (
            name_match and
            dob_match and
            dob1 and dob2  # Both must have DOB values
        )
        
        is_duplicate = traditional_match or name_mrn_match or name_dob_match
        
        # Enhanced logging for different match types
        if is_duplicate:
            match_type = ""
            if traditional_match:
                match_type = "Traditional (Name+Company+Other)"
            elif name_mrn_match:
                match_type = "Name+MRN"
            elif name_dob_match:
                match_type = "Name+DOB"
            
            self.logger.info(f"DUPLICATE FOUND ({match_type}): {patient1['id']} ({patient1_name}) <-> {patient2['id']} ({patient2_name})")
            
            # Additional details for MRN/DOB matches
            if name_mrn_match:
                self.logger.info(f"  -> Matching MRN: {mrn1}")
            if name_dob_match:
                self.logger.info(f"  -> Matching DOB: {dob1}")
        else:
            # Log why not a duplicate for debugging
            reasons = []
            if not name_match:
                reasons.append("Name mismatch")
            elif not pg_company_match and not mrn_match and not dob_match:
                reasons.append("No MRN/DOB/Company match")
            
            if reasons:
                self.logger.debug(f"Not duplicate: {patient1_name} vs {patient2_name} - {', '.join(reasons)}")
        
        # Determine match type for return value
        match_type = "no_match"
        if is_duplicate:
            if traditional_match:
                match_type = "traditional"
            elif name_mrn_match:
                match_type = "name_mrn"
            elif name_dob_match:
                match_type = "name_dob"
        
        return {
            'is_duplicate': is_duplicate,
            'match_type': match_type,
            'name_similarity': name_similarity,
            'name_match': name_match,
            'name_match_details': name_match_result,
            'dob_match': dob_match,
            'mrn_match': mrn_match,
            'company_match': company_match,
            'pg_company_match': pg_company_match,
            'differences': {
                'dob_different': dob1 != dob2 if dob1 and dob2 else False,
                'mrn_different': mrn1 != mrn2 if mrn1 and mrn2 else False,
                'name_details': name_match_result['details']
            }
        }
    
    def group_duplicates(self, patients: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group patients into duplicate clusters"""
        duplicate_groups = []
        used_indices = set()
        
        for i, patient1 in enumerate(patients):
            if i in used_indices:
                continue
                
            current_group = [patient1]
            used_indices.add(i)
            
            for j, patient2 in enumerate(patients[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                match_result = self.are_patients_duplicates(patient1, patient2)
                if match_result['is_duplicate']:
                    current_group.append(patient2)
                    used_indices.add(j)
            
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
        
        self.logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups
    
    def select_primary_patient(self, duplicate_group: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Select the primary patient to keep and return others to delete"""
        if len(duplicate_group) <= 1:
            return duplicate_group[0], []
        
        # Sort by criteria: total orders (desc), data completeness (desc), created date (asc)
        sorted_patients = sorted(duplicate_group, key=lambda p: (
            -int(p.get('agencyInfo', {}).get('totalOrders', '0') or '0'),
            -bool(p.get('agencyInfo', {}).get('dataCompleteness')),
            p.get('agencyInfo', {}).get('createdOn', '9999-12-31')
        ))
        
        primary = sorted_patients[0]
        to_delete = sorted_patients[1:]
        
        self.logger.info(f"Selected primary patient: {primary['id']} with {primary.get('agencyInfo', {}).get('totalOrders', '0')} orders")
        return primary, to_delete
    
    def fetch_pdf_from_url(self, url: str) -> Optional[bytes]:
        """Fetch PDF content from URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            self.logger.error(f"Error fetching PDF from URL {url}: {e}")
            return None
    
    def fetch_pdf_from_document_id(self, document_id: str) -> Optional[bytes]:
        """Fetch PDF content using document ID"""
        try:
            url = f"{self.config.DOCUMENT_API_URL}?docId.id={document_id}"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.config.DA_API_TOKEN}'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('isSuccess') and result.get('value', {}).get('documentBuffer'):
                document_buffer = result['value']['documentBuffer']
                return base64.b64decode(document_buffer)
            
        except Exception as e:
            self.logger.error(f"Error fetching PDF from document ID {document_id}: {e}")
        
        return None
    
    def extract_mrn_dob_from_pdf(self, pdf_content: bytes) -> Dict[str, str]:
        """Extract MRN and DOB from PDF using pdfplumber, with OCR fallback"""
        extracted_data = {'mrn': '', 'dob': ''}
        
        try:
            # Method 1: Direct text extraction using pdfplumber
            text = self._extract_text_with_pdfplumber(pdf_content)
            extraction_method = "pdfplumber"
            
            # Method 2: OCR fallback if text extraction failed or returned insufficient text
            if not text or len(text.strip()) < 50:  # Less than 50 characters is likely insufficient
                self.logger.info("Direct text extraction failed or insufficient. Attempting OCR...")
                text = self._extract_text_with_ocr(pdf_content)
                extraction_method = "OCR" if text else "failed"
            
            if not text.strip():
                self.logger.warning("No text could be extracted from PDF using either method")
                return extracted_data
            
            self.logger.info(f"Extracted {len(text)} characters of text from PDF using {extraction_method}")
            
            # Use OpenAI to extract MRN and DOB from the extracted text
            result = self._extract_mrn_dob_with_openai(text)
            result['extraction_method'] = extraction_method  # Add method info to result
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting MRN/DOB from PDF: {e}")
            return extracted_data
    
    def _extract_text_with_pdfplumber(self, pdf_content: bytes) -> str:
        """Extract text using pdfplumber"""
        try:
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                text = ""
                for page in pdf.pages[:3]:  # Only process first 3 pages
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            self.logger.warning(f"pdfplumber text extraction failed: {e}")
            return ""
    
    def _extract_text_with_ocr(self, pdf_content: bytes) -> str:
        """Extract text using OCR as fallback"""
        if not OCR_AVAILABLE:
            self.logger.warning("OCR libraries not available. Install pytesseract, PIL, and pdf2image for OCR support.")
            return ""
        
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_bytes(pdf_content, first_page=1, last_page=3)  # First 3 pages
            
            extracted_text = ""
            for i, image in enumerate(images):
                self.logger.info(f"Performing OCR on page {i+1}")
                
                # Perform OCR on the image
                page_text = pytesseract.image_to_string(image, lang='eng')
                if page_text:
                    extracted_text += page_text + "\n"
            
            self.logger.info(f"OCR extracted {len(extracted_text)} characters")
            return extracted_text
            
        except Exception as e:
            self.logger.error(f"OCR text extraction failed: {e}")
            return ""
    
    def _extract_mrn_dob_with_openai(self, text: str) -> Dict[str, str]:
        """Use OpenAI to extract MRN and DOB from text"""
        extracted_data = {'mrn': '', 'dob': ''}
        
        try:
            
            # Use OpenAI to extract MRN and DOB
            prompt = f"""
            Extract the Medical Record Number (MRN) and Date of Birth (DOB) from the following medical document text.
            Look for variations like "MRN:", "Medical Record Number:", "MR Number:", "DOB:", "Date of Birth:", "Birth Date:".
            
            Return the result in JSON format:
            {{"mrn": "extracted_mrn_value", "dob": "extracted_dob_value"}}
            
            If not found, use empty strings.
            
            Document text:
            {text[:3000]}  # Limit text to avoid token limits
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.config.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a medical document analyzer. Extract MRN and DOB accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                # Clean the response text to handle potential formatting issues
                result_text = result_text.strip()
                if result_text.startswith('```json'):
                    result_text = result_text.replace('```json', '').replace('```', '').strip()
                elif result_text.startswith('```'):
                    result_text = result_text.replace('```', '').strip()
                
                extracted_data = json.loads(result_text)
                # Ensure the extracted data has the required keys
                if not isinstance(extracted_data, dict):
                    extracted_data = {'mrn': '', 'dob': ''}
                else:
                    extracted_data = {
                        'mrn': str(extracted_data.get('mrn', '')).strip(),
                        'dob': str(extracted_data.get('dob', '')).strip()
                    }
            except json.JSONDecodeError:
                # If not valid JSON, try to extract manually
                extracted_data = {'mrn': '', 'dob': ''}
                lines = result_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if ('mrn' in line.lower() or 'medical record' in line.lower()) and ':' in line:
                        mrn_part = line.split(':', 1)[1].strip().strip('"').strip("'")
                        if mrn_part and mrn_part.lower() not in ['null', 'none', 'n/a', '']:
                            extracted_data['mrn'] = mrn_part
                    elif ('dob' in line.lower() or 'date of birth' in line.lower()) and ':' in line:
                        dob_part = line.split(':', 1)[1].strip().strip('"').strip("'")
                        if dob_part and dob_part.lower() not in ['null', 'none', 'n/a', '']:
                            extracted_data['dob'] = dob_part
            
        except Exception as e:
            self.logger.error(f"Error using OpenAI to extract MRN/DOB: {e}")
        
        return extracted_data
    
    def verify_patient_data_from_pdf(self, patient: Dict[str, Any]) -> Dict[str, str]:
        """Verify patient MRN and DOB from 485 form PDF"""
        agency_info = patient.get('agencyInfo', {})
        patient_id = patient['id']
        
        try:
            # Fetch orders for the patient
            orders_url = f"{self.config.BASE_URL}/api/Order/patient/{patient_id}"
            response = requests.get(orders_url, headers=self.config.HEADERS, timeout=30)
            response.raise_for_status()
            
            orders = response.json()
            
            # Find 485 form order or similar plan/certification documents
            form_485_order = None
            # Keywords to search for in document names (in order of preference)
            # These are partial matches - any order containing these words
            search_keywords = [
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
            
            self.logger.info(f"Searching through {len(orders)} orders for medical documents...")
            
            for order in orders:
                document_name = order.get('documentName', '')
                if not document_name:  # Skip if document name is None or empty
                    continue
                    
                document_name_lower = document_name.lower()
                order_url = order.get('orderUrl', '')
                
                self.logger.debug(f"Checking order: '{document_name}' (URL: {'Yes' if order_url else 'No'})")
                
                # Check if document name contains any of the key terms (partial matching)
                for keyword in search_keywords:
                    if keyword in document_name_lower:
                        form_485_order = order
                        self.logger.info(f"Found medical document with keyword '{keyword}': {document_name}")
                        self.logger.info(f"Order URL available: {'Yes' if order_url else 'No'}")
                        break
                if form_485_order:
                    break
            
            if not form_485_order:
                # Try to find any document that might contain patient info (broader search)
                self.logger.info("Primary keywords not found, trying fallback keywords...")
                fallback_keywords = ['home', 'health', 'patient', 'evaluation', 'order', 'note', 'communication']
                
                for order in orders:
                    document_name = order.get('documentName', '')
                    if not document_name:  # Skip if document name is None or empty
                        continue
                    document_name_lower = document_name.lower()
                    order_url = order.get('orderUrl', '')
                    
                    # Look for any medical document that might have patient info
                    for keyword in fallback_keywords:
                        if keyword in document_name_lower:
                            form_485_order = order
                            self.logger.info(f"Found fallback document with keyword '{keyword}': {document_name}")
                            self.logger.info(f"Order URL available: {'Yes' if order_url else 'No'}")
                            break
                    if form_485_order:
                        break
            
            # Try to get PDF content from the selected order
            pdf_content = None
            
            if not form_485_order:
                self.logger.warning(f"No medical document found for patient {patient_id}")
                return {'mrn': '', 'dob': ''}
            
            selected_doc_name = form_485_order.get('documentName', 'Unknown')
            self.logger.info(f"Selected document: '{selected_doc_name}' for PDF extraction")
            
            # First try from orderUrl (preferred method)
            if form_485_order.get('orderUrl'):
                order_url = form_485_order['orderUrl']
                self.logger.info(f"Attempting to fetch PDF from orderUrl: {order_url}")
                pdf_content = self.fetch_pdf_from_url(order_url)
                
                if pdf_content:
                    self.logger.info("Successfully fetched PDF from orderUrl")
                else:
                    self.logger.warning("Failed to fetch PDF from orderUrl, trying document ID...")
            else:
                self.logger.warning("No orderUrl found in selected order, trying document ID...")
            
            # If no PDF from URL, try document ID as fallback
            if not pdf_content and form_485_order.get('documentID'):
                document_id = form_485_order['documentID']
                self.logger.info(f"Attempting to fetch PDF from documentID: {document_id}")
                pdf_content = self.fetch_pdf_from_document_id(document_id)
                
                if pdf_content:
                    self.logger.info("Successfully fetched PDF from documentID")
                else:
                    self.logger.warning("Failed to fetch PDF from documentID")
            
            if pdf_content:
                self.logger.info("PDF content obtained, extracting MRN and DOB...")
                return self.extract_mrn_dob_from_pdf(pdf_content)
            else:
                self.logger.warning(f"Could not obtain PDF content for patient {patient_id}")
                return {'mrn': '', 'dob': ''}
            
        except Exception as e:
            self.logger.error(f"Error verifying patient data from PDF for {patient_id}: {e}")
        
        return {'mrn': '', 'dob': ''}
    
    def resolve_duplicate_conflicts(self, duplicate_group: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Resolve conflicts in duplicate groups by verifying data from PDFs"""
        if len(duplicate_group) <= 1:
            return duplicate_group[0], []
        
        # Check if there are conflicts in MRN or DOB
        mrns = set()
        dobs = set()
        
        for patient in duplicate_group:
            agency_info = patient.get('agencyInfo', {})
            mrn = agency_info.get('medicalRecordNo', '')
            dob = agency_info.get('dob', '')
            if mrn:
                mrns.add(mrn)
            if dob:
                dobs.add(dob)
        
        has_mrn_conflict = len(mrns) > 1
        has_dob_conflict = len(dobs) > 1
        
        if has_mrn_conflict or has_dob_conflict:
            self.logger.info(f"Found conflicts - MRN: {has_mrn_conflict}, DOB: {has_dob_conflict}")
            self.logger.info("Starting PDF verification for conflict resolution...")
            
            # Verify data from PDFs
            for i, patient in enumerate(duplicate_group, 1):
                patient_id = patient.get('id', 'Unknown')
                agency_info = patient.get('agencyInfo', {})
                patient_name = f"{agency_info.get('patientFName', '')} {agency_info.get('patientLName', '')}".strip()
                if not patient_name:
                    patient_name = 'Unknown'
                
                self.logger.info(f"[{i}/{len(duplicate_group)}] Extracting PDF data for: {patient_name} ({patient_id})")
                self.logger.info(f"   Current MRN: {agency_info.get('medicalRecordNo', 'Not set')}")
                self.logger.info(f"   Current DOB: {agency_info.get('dob', 'Not set')}")
                
                pdf_data = self.verify_patient_data_from_pdf(patient)
                patient['_pdf_verification'] = pdf_data
                
                if pdf_data.get('mrn') or pdf_data.get('dob'):
                    self.logger.info(f"   PDF Extracted MRN: {pdf_data.get('mrn', 'Not found')}")
                    self.logger.info(f"   PDF Extracted DOB: {pdf_data.get('dob', 'Not found')}")
                else:
                    self.logger.info(f"   No MRN/DOB data extracted from PDF")
            
            # Select primary based on PDF verification
            self.logger.info("Scoring patients based on PDF verification...")
            verified_patients = []
            for patient in duplicate_group:
                agency_info = patient.get('agencyInfo', {})
                pdf_data = patient.get('_pdf_verification', {})
                
                current_mrn = agency_info.get('medicalRecordNo', '')
                current_dob = agency_info.get('dob', '')
                pdf_mrn = pdf_data.get('mrn', '')
                pdf_dob = pdf_data.get('dob', '')
                
                # Score based on PDF verification
                score = 0
                score_details = []
                
                if pdf_mrn and current_mrn and pdf_mrn == current_mrn:
                    score += 2
                    score_details.append("MRN matches PDF (+2)")
                if pdf_dob and current_dob and pdf_dob == current_dob:
                    score += 2
                    score_details.append("DOB matches PDF (+2)")
                if pdf_mrn and not current_mrn:
                    score += 1
                    score_details.append("PDF has MRN, current doesn't (+1)")
                if pdf_dob and not current_dob:
                    score += 1
                    score_details.append("PDF has DOB, current doesn't (+1)")
                
                patient['_verification_score'] = score
                verified_patients.append(patient)
                
                agency_info = patient.get('agencyInfo', {})
                patient_name = f"{agency_info.get('patientFName', '')} {agency_info.get('patientLName', '')}".strip()
                if not patient_name:
                    patient_name = 'Unknown'
                self.logger.info(f"   {patient_name}: Score = {score} ({', '.join(score_details) if score_details else 'No PDF matches'})")
            
            # Sort by verification score, then by total orders
            verified_patients.sort(key=lambda p: (
                -p.get('_verification_score', 0),
                -int(p.get('agencyInfo', {}).get('totalOrders', '0') or '0')
            ))
            
            primary = verified_patients[0]
            to_delete = verified_patients[1:]
            
            primary_agency_info = primary.get('agencyInfo', {})
            primary_name = f"{primary_agency_info.get('patientFName', '')} {primary_agency_info.get('patientLName', '')}".strip()
            if not primary_name:
                primary_name = 'Unknown'
            self.logger.info(f"Selected primary patient after PDF verification: {primary_name} ({primary['id']}) - Score: {primary.get('_verification_score', 0)}")
            
            # Show what will happen to other patients
            for patient in to_delete:
                patient_agency_info = patient.get('agencyInfo', {})
                patient_name = f"{patient_agency_info.get('patientFName', '')} {patient_agency_info.get('patientLName', '')}".strip()
                if not patient_name:
                    patient_name = 'Unknown'
                self.logger.info(f"Will delete: {patient_name} ({patient['id']}) - Score: {patient.get('_verification_score', 0)}")
            
            return primary, to_delete
        
        # No conflicts, use standard selection
        return self.select_primary_patient(duplicate_group)
    
    def fetch_orders(self, patient_id: str) -> List[Dict[str, Any]]:
        """Fetch orders for a patient"""
        try:
            url = f"{self.config.BASE_URL}/api/Order/patient/{patient_id}"
            response = requests.get(url, headers=self.config.HEADERS, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching orders for patient {patient_id}: {e}")
            return []
    
    def fetch_cc_notes(self, patient_id: str) -> List[Dict[str, Any]]:
        """Fetch CC notes for a patient"""
        try:
            url = f"{self.config.BASE_URL}/api/CCNotes/patient/{patient_id}"
            response = requests.get(url, headers=self.config.HEADERS, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching CC notes for patient {patient_id}: {e}")
            return []
    
    def update_order(self, order_id: str, order_data: Dict[str, Any], new_patient_id: str) -> bool:
        """Update order with new patient ID"""
        try:
            order_data['patientId'] = new_patient_id
            
            url = f"{self.config.BASE_URL}/api/Order/{order_id}"
            response = requests.put(url, json=order_data, headers=self.config.HEADERS, timeout=30)
            response.raise_for_status()
            
            self.logger.info(f"Updated order {order_id} to patient {new_patient_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating order {order_id}: {e}")
            return False
    
    def update_cc_note(self, note_id: str, note_data: Dict[str, Any], new_patient_id: str) -> bool:
        """Update CC note with new patient ID"""
        try:
            note_data['patientId'] = new_patient_id
            
            url = f"{self.config.BASE_URL}/api/CCNotes/{note_id}"
            response = requests.put(url, json=note_data, headers=self.config.HEADERS, timeout=30)
            response.raise_for_status()
            
            self.logger.info(f"Updated CC note {note_id} to patient {new_patient_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating CC note {note_id}: {e}")
            return False
    
    def delete_patient(self, patient_id: str) -> bool:
        """Delete a patient"""
        try:
            url = f"{self.config.BASE_URL}/api/Patient/{patient_id}"
            response = requests.delete(url, headers=self.config.HEADERS, timeout=30)
            response.raise_for_status()
            
            self.logger.info(f"Deleted patient {patient_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting patient {patient_id}: {e}")
            return False
    
    def call_rcm_api(self, patient_id: str, is_deleted: bool) -> bool:
        """Call RCM API for patient with correct HTTP method"""
        try:
            if is_deleted:
                url = f"{self.config.BASE_URL}/api/RCM/rcm/patient/{patient_id}"
                api_type = "RCM (deleted)"
                # For deleted patients, try DELETE method first, then others
                methods = ['DELETE', 'POST', 'GET']
            else:
                url = f"{self.config.BASE_URL}/api/RCM/cron-new-patient/{patient_id}"
                api_type = "RCM New Patient (kept)"
                # For kept patients, use POST method as specified
                methods = ['POST']
            
            # Try different HTTP methods in order of preference
            for method in methods:
                try:
                    if method == 'GET':
                        response = requests.get(url, headers=self.config.HEADERS, timeout=60)
                    elif method == 'POST':
                        response = requests.post(url, headers=self.config.HEADERS, timeout=60)
                    elif method == 'PUT':
                        response = requests.put(url, headers=self.config.HEADERS, timeout=60)
                    elif method == 'DELETE':
                        response = requests.delete(url, headers=self.config.HEADERS, timeout=60)
                    
                    if response.status_code == 405:
                        # Method not allowed, try next method
                        continue
                    
                    response.raise_for_status()
                    self.logger.info(f"Called {api_type} API for patient {patient_id} using {method} method")
                    return True
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 405:
                        # Method not allowed, try next method
                        continue
                    else:
                        # Other HTTP error, log and continue to next method
                        self.logger.warning(f"{api_type} API call failed with {method} method: {e}")
                        continue
                except Exception as e:
                    # Other error, try next method
                    self.logger.warning(f"{api_type} API call failed with {method} method: {e}")
                    continue
            
            # If all methods failed
            self.logger.error(f"All HTTP methods failed for {api_type} API for patient {patient_id}")
            return False
            
        except Exception as e:
            api_type = "RCM (deleted)" if is_deleted else "RCM New Patient (kept)"
            self.logger.error(f"Error calling {api_type} API for patient {patient_id}: {e}")
            return False
    
    def merge_duplicate_patients(self, primary_patient: Dict[str, Any], patients_to_delete: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge duplicate patients by moving orders and CC notes"""
        primary_id = primary_patient['id']
        merge_results = {
            'primary_patient_id': primary_id,
            'deleted_patient_ids': [],
            'moved_orders': 0,
            'moved_cc_notes': 0,
            'errors': []
        }
        
        for patient_to_delete in patients_to_delete:
            patient_id = patient_to_delete['id']
            patient_name = f"{patient_to_delete.get('agencyInfo', {}).get('patientFName', '')} {patient_to_delete.get('agencyInfo', {}).get('patientLName', '')}".strip()
            
            # Track counts for this specific patient
            patient_orders_moved = 0
            patient_cc_notes_moved = 0
            
            try:
                # Fetch orders (exclude CCNote type)
                orders = self.fetch_orders(patient_id)
                orders_to_move = [order for order in orders if order.get('entityType') != 'CCNote']
                
                self.logger.info(f"Found {len(orders_to_move)} orders to move from patient {patient_id} to primary patient {primary_id}")
                
                # Move orders
                for order in orders_to_move:
                    order_type = order.get('entityType', 'Unknown')
                    order_id = order['id']
                    
                    if self.update_order(order_id, order, primary_id):
                        merge_results['moved_orders'] += 1
                        patient_orders_moved += 1
                        self.logger.info(f"   ✓ Moved order: {order_type} (ID: {order_id}) from {patient_name} ({patient_id}) to primary patient")
                    else:
                        merge_results['errors'].append(f"Failed to move order {order_id}")
                        self.logger.error(f"   ✗ Failed to move order: {order_type} (ID: {order_id}) from {patient_name} ({patient_id}) to primary patient")
                
                # Fetch and move CC notes
                cc_notes = self.fetch_cc_notes(patient_id)
                self.logger.info(f"Found {len(cc_notes)} CC notes to move from patient {patient_name} ({patient_id}) to primary patient")
                
                for note in cc_notes:
                    note_id = note['id']
                    note_type = note.get('noteType', 'CC Note')
                    
                    if self.update_cc_note(note_id, note, primary_id):
                        merge_results['moved_cc_notes'] += 1
                        patient_cc_notes_moved += 1
                        self.logger.info(f"   ✓ Moved CC Note: {note_type} (ID: {note_id}) from {patient_name} ({patient_id}) to primary patient")
                    else:
                        merge_results['errors'].append(f"Failed to move CC note {note_id}")
                        self.logger.error(f"   ✗ Failed to move CC Note: {note_type} (ID: {note_id}) from {patient_name} ({patient_id}) to primary patient")
                
                # Delete patient
                if self.delete_patient(patient_id):
                    merge_results['deleted_patient_ids'].append(patient_id)
                    
                    # Log summary for this patient
                    self.logger.info(f"✓ COMPLETED: {patient_name} ({patient_id}) - Moved {patient_orders_moved} orders and {patient_cc_notes_moved} CC notes, then deleted patient")
                    
                    # Call RCM APIs (non-blocking - failures don't stop processing)
                    if self.config.ENABLE_RCM_CALLS:
                        try:
                            self.call_rcm_api(patient_id, is_deleted=True)  # For deleted patient
                            self.call_rcm_api(primary_id, is_deleted=False)  # For kept patient
                        except Exception as rcm_error:
                            # Log RCM errors but don't fail the entire process
                            self.logger.warning(f"RCM API calls failed for patient {patient_id}: {rcm_error}")
                            merge_results['errors'].append(f"RCM API calls failed for patient {patient_id}: {rcm_error}")
                    else:
                        self.logger.info("RCM API calls disabled in configuration")
                else:
                    merge_results['errors'].append(f"Failed to delete patient {patient_id}")
                    self.logger.error(f"✗ FAILED: Could not delete {patient_name} ({patient_id}) after moving {patient_orders_moved} orders and {patient_cc_notes_moved} CC notes")
                
            except Exception as e:
                error_msg = f"Error processing patient {patient_id}: {e}"
                self.logger.error(error_msg)
                merge_results['errors'].append(error_msg)
        
        # Log final summary
        primary_name = f"{primary_patient.get('agencyInfo', {}).get('patientFName', '')} {primary_patient.get('agencyInfo', {}).get('patientLName', '')}".strip()
        self.logger.info(f"MERGE COMPLETE: Primary patient {primary_name} ({primary_id}) now has all data from {len(merge_results['deleted_patient_ids'])} deleted duplicate(s)")
        self.logger.info(f"TOTALS: {merge_results['moved_orders']} orders and {merge_results['moved_cc_notes']} CC notes moved")
        
        return merge_results
    
    def process_duplicates_test_mode(self, pg_company_id: str) -> Dict[str, Any]:
        """Test mode - process duplicates without making any changes"""
        self.logger.info(f"Starting TEST MODE duplicate processing for PG Company ID: {pg_company_id}")
        
        results = {
            'pg_company_id': pg_company_id,
            'total_patients': 0,
            'duplicate_groups_found': 0,
            'patients_processed': 0,
            'patients_deleted': 0,
            'orders_moved': 0,
            'cc_notes_moved': 0,
            'errors': [],
            'processing_details': []
        }
        
        try:
            # Fetch all patients
            patients = self.fetch_patients(pg_company_id)
            results['total_patients'] = len(patients)
            
            if not patients:
                self.logger.warning("No patients found")
                return results
            
            # Group duplicates
            duplicate_groups = self.group_duplicates(patients)
            results['duplicate_groups_found'] = len(duplicate_groups)
            
            if not duplicate_groups:
                self.logger.info("No duplicate groups found")
                return results
            
            # Process each duplicate group (simulation only)
            for group_idx, duplicate_group in enumerate(duplicate_groups, 1):
                self.logger.info(f"TEST: Processing duplicate group {group_idx}/{len(duplicate_groups)} with {len(duplicate_group)} patients")
                
                try:
                    # Resolve conflicts and select primary patient
                    primary_patient, patients_to_delete = self.resolve_duplicate_conflicts(duplicate_group)
                    
                    if not patients_to_delete:
                        self.logger.info("TEST: No patients to delete in this group")
                        continue
                    
                    # Collect PDF extraction details for display
                    pdf_extractions = []
                    for patient in duplicate_group:
                        pdf_data = patient.get('_pdf_verification', {})
                        if pdf_data:  # Only show if PDF extraction was attempted
                            patient_name = f"{patient.get('agencyInfo', {}).get('patientFName', '')} {patient.get('agencyInfo', {}).get('patientLName', '')}"
                            pdf_extractions.append({
                                'patient_name': patient_name.strip(),
                                'patient_id': patient.get('id', ''),
                                'pdf_mrn': pdf_data.get('mrn', ''),
                                'pdf_dob': pdf_data.get('dob', ''),
                                'score': patient.get('_verification_score', 0),
                                'current_mrn': patient.get('agencyInfo', {}).get('medicalRecordNo', ''),
                                'current_dob': patient.get('agencyInfo', {}).get('dob', '')
                            })
                    
                    # Simulate counting orders and CC notes that would be moved
                    total_orders_to_move = 0
                    total_cc_notes_to_move = 0
                    
                    for patient_to_delete in patients_to_delete:
                        patient_id = patient_to_delete['id']
                        
                        # Count orders (excluding CCNote type)
                        orders = self.fetch_orders(patient_id)
                        orders_to_move = [order for order in orders if order.get('entityType') != 'CCNote']
                        total_orders_to_move += len(orders_to_move)
                        
                        # Count CC notes
                        cc_notes = self.fetch_cc_notes(patient_id)
                        total_cc_notes_to_move += len(cc_notes)
                    
                    # Update results
                    results['patients_processed'] += len(duplicate_group)
                    results['patients_deleted'] += len(patients_to_delete)
                    results['orders_moved'] += total_orders_to_move
                    results['cc_notes_moved'] += total_cc_notes_to_move
                    
                    # Store processing details
                    group_details = {
                        'group_number': group_idx,
                        'primary_patient_id': primary_patient['id'],
                        'primary_patient_name': f"{primary_patient.get('agencyInfo', {}).get('patientFName', '')} {primary_patient.get('agencyInfo', {}).get('patientLName', '')}",
                        'deleted_patient_ids': [p['id'] for p in patients_to_delete],
                        'moved_orders': total_orders_to_move,
                        'moved_cc_notes': total_cc_notes_to_move,
                        'pdf_extractions': pdf_extractions,  # Include PDF extraction details
                        'errors': []
                    }
                    results['processing_details'].append(group_details)
                    
                except Exception as e:
                    error_msg = f"TEST: Error processing duplicate group {group_idx}: {e}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
            
        except Exception as e:
            error_msg = f"TEST: Error in duplicate processing: {e}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
        
        self.logger.info("TEST MODE duplicate processing completed")
        return results

    def process_duplicates(self, pg_company_id: str) -> Dict[str, Any]:
        """Main method to process duplicates for a PG Company ID"""
        self.logger.info(f"Starting duplicate processing for PG Company ID: {pg_company_id}")
        
        results = {
            'pg_company_id': pg_company_id,
            'total_patients': 0,
            'duplicate_groups_found': 0,
            'patients_processed': 0,
            'patients_deleted': 0,
            'orders_moved': 0,
            'cc_notes_moved': 0,
            'errors': [],
            'processing_details': []
        }
        
        try:
            # Fetch all patients
            patients = self.fetch_patients(pg_company_id)
            results['total_patients'] = len(patients)
            
            if not patients:
                self.logger.warning("No patients found")
                return results
            
            # Group duplicates
            duplicate_groups = self.group_duplicates(patients)
            results['duplicate_groups_found'] = len(duplicate_groups)
            
            if not duplicate_groups:
                self.logger.info("No duplicate groups found")
                return results
            
            # Process each duplicate group
            for group_idx, duplicate_group in enumerate(duplicate_groups, 1):
                self.logger.info(f"Processing duplicate group {group_idx}/{len(duplicate_groups)} with {len(duplicate_group)} patients")
                
                try:
                    # Resolve conflicts and select primary patient
                    primary_patient, patients_to_delete = self.resolve_duplicate_conflicts(duplicate_group)
                    
                    if not patients_to_delete:
                        self.logger.info("No patients to delete in this group")
                        continue
                    
                    # Merge patients
                    merge_results = self.merge_duplicate_patients(primary_patient, patients_to_delete)
                    
                    # Update results
                    results['patients_processed'] += len(duplicate_group)
                    results['patients_deleted'] += len(merge_results['deleted_patient_ids'])
                    results['orders_moved'] += merge_results['moved_orders']
                    results['cc_notes_moved'] += merge_results['moved_cc_notes']
                    results['errors'].extend(merge_results['errors'])
                    
                    # Store processing details
                    group_details = {
                        'group_number': group_idx,
                        'primary_patient_id': primary_patient['id'],
                        'primary_patient_name': f"{primary_patient.get('agencyInfo', {}).get('patientFName', '')} {primary_patient.get('agencyInfo', {}).get('patientLName', '')}",
                        'deleted_patient_ids': merge_results['deleted_patient_ids'],
                        'moved_orders': merge_results['moved_orders'],
                        'moved_cc_notes': merge_results['moved_cc_notes'],
                        'errors': merge_results['errors']
                    }
                    results['processing_details'].append(group_details)
                    
                except Exception as e:
                    error_msg = f"Error processing duplicate group {group_idx}: {e}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
            
        except Exception as e:
            error_msg = f"Error in duplicate processing: {e}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
        
        self.logger.info("Duplicate processing completed")
        return results
    
    def run_production(self, pg_company_id: str) -> None:
        """Run production duplicate management"""
        try:
            # Fetch all patients first for Excel export
            self.logger.info("Fetching all patients for Excel export...")
            all_patients = self.fetch_patients(pg_company_id)
            
            # Process duplicates
            results = self.process_duplicates(pg_company_id)
            
            # Generate Excel report
            excel_filename = ""
            try:
                excel_filename = self.excel_generator.generate_excel_report(results, all_patients, self.output_dirs['excel'])
            except Exception as e:
                self.logger.error(f"Failed to generate Excel report: {e}")
            
            # Generate HTML report
            report_html = self.report_generator.generate_html_report(results)
            
            # Prepare attachments
            attachments = []
            if excel_filename and os.path.exists(excel_filename):
                attachments.append(excel_filename)
            
            # Send email with attachments
            subject = f"Duplicate Patient Management Report - PG Company {pg_company_id}"
            self.email_sender.send_email(
                to_email=self.config.REPORT_EMAIL,
                subject=subject,
                html_body=report_html,
                attachments=attachments,
                output_dir=self.output_dirs['html']
            )
            
            self.logger.info("Production run completed successfully")
            if excel_filename:
                self.logger.info(f"Excel report generated: {excel_filename}")
            
        except Exception as e:
            self.logger.error(f"Error in production run: {e}")
            raise
    
    def run_test(self, patient_id: str) -> None:
        """Run test with a specific patient ID"""
        try:
            self.logger.info(f"Running test mode for patient: {patient_id}")
            
            # Fetch patient details
            # This would require implementing a method to fetch single patient
            # and simulate duplicate processing
            
            # For now, just log that test mode is running
            self.logger.info("Test mode - would process single patient here")
            
        except Exception as e:
            self.logger.error(f"Error in test run: {e}")
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Duplicate Patient Manager')
    parser.add_argument('--mode', choices=['production', 'test'], required=True, 
                       help='Run mode: production or test')
    parser.add_argument('--pg-company-id', required=True, 
                       help='PG Company ID to process')
    parser.add_argument('--test-patient-id', 
                       help='Patient ID for test mode')
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config()
    
    # Initialize manager
    manager = DuplicatePatientManager(config)
    
    try:
        if args.mode == 'production':
            manager.run_production(args.pg_company_id)
        elif args.mode == 'test':
            if not args.test_patient_id:
                print("Test mode requires --test-patient-id")
                sys.exit(1)
            manager.run_test(args.test_patient_id)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
