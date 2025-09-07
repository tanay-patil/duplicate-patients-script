# Duplicate Patient Manager

A comprehensive Python application for managing duplicate patients based on PG Company ID. The system identifies duplicates using fuzzy name matching, DOB, MRN, Company ID, and PG Company ID, then merges them by moving orders and CC notes to the primary patient.

## Features

- 🔍 **Smart Duplicate Detection**: Uses fuzzy matching for names and exact matching for other fields
- 📄 **PDF Data Verification**: Extracts MRN and DOB from 485 forms using PDFPlumber and OpenAI
- 🔄 **Safe Data Migration**: Moves orders (except CCNote type) and CC notes to primary patient
- 📧 **Automated Reporting**: Generates and emails detailed HTML reports
- 🧪 **Comprehensive Testing**: Test suite for validation before production runs
- 📊 **RCM Integration**: Calls RCM APIs for deleted and kept patients

## Quick Start

1. **Setup Environment**
   ```bash
   python setup.py
   ```

2. **Configure API Tokens**
   Edit the `.env` file with your actual API tokens and credentials.

3. **Run Tests**
   ```bash
   python test_duplicate_manager.py --pg-company-id YOUR_PG_COMPANY_ID --test-patient-id PATIENT_WITH_ORDERS_AND_CCNS
   ```

4. **Run Production**
   ```bash
   python duplicate_patient_manager.py --mode production --pg-company-id YOUR_PG_COMPANY_ID
   ```

## Installation

### Prerequisites
- Python 3.8 or higher
- Valid API tokens for the patient management system
- Azure OpenAI API key
- Gmail OAuth2 credentials (for email reports)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure Environment
1. Copy the `.env.template` to `.env`
2. Fill in your actual API credentials and tokens
3. Update the `REPORT_EMAIL` with your desired recipient

## Usage

### Production Mode
Process all duplicates for a PG Company ID:
```bash
python duplicate_patient_manager.py --mode production --pg-company-id d10f46ad-225d-4ba2-882c-149521fcead5
```

### Test Mode
Test with a specific patient (requires a patient ID with orders and CC notes):
```bash
python duplicate_patient_manager.py --mode test --pg-company-id d10f46ad-225d-4ba2-882c-149521fcead5 --test-patient-id c964ab68-1ba3-47b7-b379-d6e6240b9e18
```

### Testing Suite
Run comprehensive tests:
```bash
# Full test suite
python test_duplicate_manager.py --pg-company-id YOUR_PG_COMPANY_ID --test-patient-id PATIENT_ID

# Test duplicate detection only
python test_duplicate_manager.py --pg-company-id YOUR_PG_COMPANY_ID --test-type duplicate-detection

# Test name matching logic
python test_duplicate_manager.py --pg-company-id YOUR_PG_COMPANY_ID --test-type name-matching

# Test single patient analysis
python test_duplicate_manager.py --pg-company-id YOUR_PG_COMPANY_ID --test-patient-id PATIENT_ID --test-type single-patient

# Test PDF extraction
python test_duplicate_manager.py --pg-company-id YOUR_PG_COMPANY_ID --test-patient-id PATIENT_ID --test-type pdf-extraction
```

## How It Works

### 1. Patient Fetching
Retrieves all patients for a given PG Company ID using the API:
```
GET /api/Patient/company/pg/{id}
```

### 2. Duplicate Detection
Groups patients as duplicates based on:
- **Name similarity** (≥85% fuzzy match by default)
- **PG Company ID** (exact match)
- **At least one of**: DOB, MRN, or Company ID (exact match)

### 3. Conflict Resolution
When duplicates have conflicting MRN or DOB:
- Fetches 485 form PDFs from orders
- Uses PDFPlumber to extract text
- Uses OpenAI to identify MRN and DOB from document
- Selects primary patient based on PDF verification

### 4. Primary Patient Selection
Prioritizes patients by:
1. PDF verification score (highest)
2. Total orders count (highest)
3. Data completeness (complete first)
4. Created date (oldest first)

### 5. Data Migration
For each patient to be deleted:
- Moves all orders (except those with `entityType: "CCNote"`)
- Moves all CC notes
- Updates `patientId` in moved records
- Preserves all existing data fields

### 6. Cleanup
- Deletes duplicate patients
- Calls RCM APIs for both deleted and kept patients
- Generates comprehensive report

## API Endpoints Used

| Purpose | Method | Endpoint |
|---------|--------|----------|
| Fetch Patients | GET | `/api/Patient/company/pg/{id}` |
| Fetch Orders | GET | `/api/Order/patient/{id}` |
| Fetch CC Notes | GET | `/api/CCNotes/patient/{id}` |
| Update Order | PUT | `/api/Order/{id}` |
| Update CC Note | PUT | `/api/CCNotes/{id}` |
| Delete Patient | DELETE | `/api/Patient/{id}` |
| RCM (Deleted) | POST | `/api/RCM/rcm/patient/{id}` |
| RCM (Kept) | POST | `/api/RCM/cron-by-patient/{id}` |
| Document PDF | GET | `https://api.doctoralliance.com/document/getfile?docId.id={id}` |

## Configuration

### Environment Variables
```bash
# API Authentication
API_TOKEN=your_main_api_token
DA_API_TOKEN=doctor_alliance_api_token

# Azure OpenAI
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://daplatformai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-35-turbo

# Gmail OAuth2
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret

# Email Configuration
REPORT_EMAIL=recipient@example.com
```

### Configuration Options
- `NAME_SIMILARITY_THRESHOLD`: Minimum percentage for name matching (default: 85)
- `REQUEST_TIMEOUT`: API request timeout in seconds (default: 30)
- `ENABLE_RCM_CALLS`: Enable/disable RCM API calls (default: True)

## Report Generation

The system generates comprehensive HTML reports including:
- **Processing Summary**: Total patients, duplicates found, patients deleted, errors
- **Processing Details**: Per-group breakdown with primary patient selection
- **Error Tracking**: Detailed error messages and warnings
- **Visual Design**: Responsive HTML with professional styling

Reports are automatically emailed and also saved locally as backup.

## Testing

The application includes comprehensive testing capabilities:

### Test Types
- **Name Matching**: Validates fuzzy string matching logic
- **Duplicate Detection**: Tests grouping algorithm without processing
- **Single Patient**: Analyzes orders and CC notes for a specific patient
- **PDF Extraction**: Tests MRN/DOB extraction from 485 forms
- **Comprehensive**: Runs all tests in sequence

### Safety Features
- Test mode processes only specified patients
- Dry-run capabilities for duplicate detection
- Extensive logging for troubleshooting
- Validation of API responses before processing

## Logging

Logs are written to both console and files:
- **Info Level**: Progress updates, successful operations
- **Warning Level**: Non-critical issues, missing data
- **Error Level**: Failed operations, API errors

Log files are created daily: `duplicate_manager_YYYYMMDD.log`

## Error Handling

Robust error handling includes:
- **API Failures**: Retry logic and graceful degradation
- **Data Validation**: Checks for required fields before processing
- **PDF Processing**: Handles corrupted or inaccessible documents
- **Email Failures**: Falls back to local file storage

## Security Considerations

- API tokens are stored in environment variables
- OAuth2 flow for Gmail integration
- Secure HTTPS connections for all API calls
- Sensitive data is not logged

## File Structure

```
duplicate-patient-manager/
├── duplicate_patient_manager.py    # Main application
├── config.py                      # Configuration management
├── email_sender.py                # Email functionality
├── report_generator.py            # HTML report generation
├── test_duplicate_manager.py      # Test suite
├── setup.py                       # Environment setup
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── .env.template                  # Environment variables template
└── logs/                          # Log files directory
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **API Authentication Failures**
   - Check your API tokens in `.env`
   - Verify token permissions and expiration

3. **RCM API Issues**
   - The system automatically tries GET, POST, and PUT methods for RCM endpoints
   - RCM API failures don't stop the duplicate processing
   - Set `ENABLE_RCM_CALLS=False` in .env to disable RCM calls entirely

3. **PDF Extraction Issues**
   - Ensure Azure OpenAI credentials are correct
   - Check if documents are accessible via provided URLs

4. **RCM API Issues**
   - The system automatically tries GET, POST, and PUT methods for RCM endpoints
   - RCM API failures don't stop the duplicate processing
   - Set `ENABLE_RCM_CALLS=False` in .env to disable RCM calls entirely

5. **Email Delivery Problems**
   - Verify Gmail OAuth2 credentials
   - Check spam folders for delivered emails

### Debug Mode
Enable verbose logging by setting log level to DEBUG in the application.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review log files for detailed error messages
- Contact: support@doctoralliance.com

## License

This project is proprietary software developed for Doctor Alliance.

---

**Version**: 1.0  
**Last Updated**: September 2025  
**Author**: DA Development Team
