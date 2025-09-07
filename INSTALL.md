# Installation and Usage Guide

## Quick Start

### 1. Windows Users (Recommended)
```cmd
# Clone or download the project files
# Open Command Prompt or PowerShell in the project directory

# Run the Windows batch file
run.bat

# OR use PowerShell
.\run.ps1
```

### 2. Manual Installation
```bash
# Install Python 3.8+ if not already installed
# Verify installation
python --version

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run setup
python setup.py
```

## Configuration

### 1. Environment Setup
```bash
# Copy the environment template
cp .env.template .env

# Edit .env file with your credentials
# You MUST update the API_TOKEN with your actual token
```

### 2. Required API Tokens
- **API_TOKEN**: Main patient management API token (REQUIRED - update in .env)
- **DA_API_TOKEN**: Document API token (provided)
- **AZURE_OPENAI_KEY**: OpenAI key for PDF extraction (provided)
- **Gmail credentials**: For email reports (provided)

## Usage Examples

### Testing (Safe - No Data Changes)
```bash
# Test duplicate detection only
python test_duplicate_manager.py --pg-company-id "d10f46ad-225d-4ba2-882c-149521fcead5" --test-type duplicate-detection

# Test single patient (requires patient with orders/CCNotes)
python test_duplicate_manager.py --pg-company-id "d10f46ad-225d-4ba2-882c-149521fcead5" --test-patient-id "c964ab68-1ba3-47b7-b379-d6e6240b9e18" --test-type single-patient

# Comprehensive test suite
python test_duplicate_manager.py --pg-company-id "d10f46ad-225d-4ba2-882c-149521fcead5" --test-patient-id "c964ab68-1ba3-47b7-b379-d6e6240b9e18"

# Test RCM API endpoints
python test_rcm_api.py --patient-id "c964ab68-1ba3-47b7-b379-d6e6240b9e18"
```

### Production (Modifies Data - Use Carefully)
```bash
# Process all duplicates for a PG Company
python duplicate_patient_manager.py --mode production --pg-company-id "d10f46ad-225d-4ba2-882c-149521fcead5"
```

## File Structure
```
duplicate-patient-manager/
├── duplicate_patient_manager.py    # Main application
├── test_duplicate_manager.py       # Test suite
├── config.py                      # Configuration
├── email_sender.py                # Email functionality
├── report_generator.py            # HTML reports
├── setup.py                       # Environment setup
├── requirements.txt               # Dependencies
├── run.bat                        # Windows batch runner
├── run.ps1                        # PowerShell runner
├── .env.template                  # Environment template
├── README.md                      # Documentation
└── logs/                          # Log files
```

## What the Application Does

1. **Fetches Patients**: Gets all patients for a PG Company ID
2. **Identifies Duplicates**: Uses fuzzy name matching + exact field matching
3. **Resolves Conflicts**: Verifies MRN/DOB from PDF documents when needed
4. **Merges Data**: Moves orders and CC notes to the primary patient
5. **Cleans Up**: Deletes duplicate patients
6. **Calls RCM APIs**: Updates RCM system for both deleted and kept patients
7. **Sends Report**: Emails detailed HTML report of all changes

## Safety Features

- **Test Mode**: Analyze duplicates without making changes
- **Comprehensive Logging**: Track all operations
- **Data Validation**: Verify data integrity before processing
- **Backup Reports**: Save reports locally even if email fails
- **Error Handling**: Graceful handling of API failures

## Common Issues

### Python Not Found
```bash
# Install Python from python.org
# Add Python to system PATH
# Restart command prompt
python --version
```

### Import Errors
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### API Token Issues
- Update `API_TOKEN` in `.env` file with your actual token
- Verify token has required permissions
- Check token expiration

### No Duplicates Found
- Verify PG Company ID is correct
- Check that patients exist for that company
- Review similarity threshold settings

### RCM API Errors
- Test RCM endpoints: `python test_rcm_api.py --patient-id PATIENT_ID`
- If RCM APIs are not working, set `ENABLE_RCM_CALLS=False` in .env
- RCM failures don't stop duplicate processing

## Getting Help

1. Check the README.md for detailed documentation
2. Review log files for error details
3. Run tests first to validate setup
4. Contact support: support@doctoralliance.com

## Example Session

```bash
# 1. First time setup
python setup.py

# 2. Edit .env file with your API token
notepad .env  # Windows
vim .env      # Linux/Mac

# 3. Test with your PG Company ID
python test_duplicate_manager.py --pg-company-id "YOUR_PG_COMPANY_ID"

# 4. If tests pass, run production
python duplicate_patient_manager.py --mode production --pg-company-id "YOUR_PG_COMPANY_ID"
```

## Production Checklist

Before running in production:
- [ ] Setup completed successfully
- [ ] .env file configured with correct API tokens
- [ ] Tests run successfully
- [ ] PG Company ID verified
- [ ] Backup of data (if required)
- [ ] Email recipient configured
- [ ] Understanding of what changes will be made

## Support

For technical support or questions:
- Email: support@doctoralliance.com
- Check log files for detailed error information
- Run test mode first to diagnose issues
