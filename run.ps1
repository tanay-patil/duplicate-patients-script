# Duplicate Patient Manager - PowerShell Runner
# This script provides an easy way to run the duplicate patient manager using PowerShell

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("setup", "test", "production", "test-patient", "test-name", "test-duplicate")]
    [string]$Mode = "menu",
    
    [Parameter(Mandatory=$false)]
    [string]$PgCompanyId = "",
    
    [Parameter(Mandatory=$false)]
    [string]$TestPatientId = ""
)

# Function to display header
function Show-Header {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "   Duplicate Patient Manager - PowerShell Runner" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
}

# Function to check Python installation
function Test-Python {
    try {
        $pythonVersion = python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Python version: $pythonVersion" -ForegroundColor Green
            return $true
        } else {
            Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
            Write-Host "Please install Python 3.8+ and add it to your PATH" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "ERROR: Cannot check Python installation" -ForegroundColor Red
        return $false
    }
}

# Function to setup virtual environment
function Setup-VirtualEnv {
    if (-not (Test-Path "venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv venv
    }
    
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
    
    if (Test-Path "requirements.txt") {
        Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt
    }
}

# Function to check .env file
function Test-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Host ""
        Write-Host "WARNING: .env file not found!" -ForegroundColor Red
        Write-Host "Please run setup mode first to create the environment template:" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 -Mode setup" -ForegroundColor Yellow
        Write-Host ""
        return $false
    }
    return $true
}

# Function to get user input
function Get-UserInput {
    param([string]$Prompt, [bool]$Required = $true)
    
    do {
        $input = Read-Host $Prompt
        if (-not $Required -or $input) {
            return $input
        }
        Write-Host "This field is required." -ForegroundColor Red
    } while ($true)
}

# Function to run setup
function Run-Setup {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "              ENVIRONMENT SETUP" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    python setup.py
    Read-Host "Press Enter to continue"
}

# Function to run tests
function Run-Tests {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "                 RUN TESTS" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    
    if (-not $PgCompanyId) {
        $PgCompanyId = Get-UserInput "Enter PG Company ID"
    }
    
    if (-not $TestPatientId) {
        $TestPatientId = Get-UserInput "Enter Test Patient ID (optional, press Enter to skip)" $false
    }

    if ($TestPatientId) {
        python test_duplicate_manager.py --pg-company-id $PgCompanyId --test-patient-id $TestPatientId
    } else {
        python test_duplicate_manager.py --pg-company-id $PgCompanyId
    }
    Read-Host "Press Enter to continue"
}

# Function to run production
function Run-Production {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "              PRODUCTION MODE" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "WARNING: This will process and modify actual patient data!" -ForegroundColor Red
    
    $confirm = Read-Host "Are you sure you want to continue? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        return
    }

    if (-not $PgCompanyId) {
        $PgCompanyId = Get-UserInput "Enter PG Company ID"
    }
    
    python duplicate_patient_manager.py --mode production --pg-company-id $PgCompanyId
    Read-Host "Press Enter to continue"
}

# Function to test single patient
function Test-SinglePatient {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "            TEST SINGLE PATIENT" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    
    if (-not $PgCompanyId) {
        $PgCompanyId = Get-UserInput "Enter PG Company ID"
    }
    
    if (-not $TestPatientId) {
        $TestPatientId = Get-UserInput "Enter Patient ID"
    }
    
    python test_duplicate_manager.py --pg-company-id $PgCompanyId --test-patient-id $TestPatientId --test-type single-patient
    Read-Host "Press Enter to continue"
}

# Function to test name matching
function Test-NameMatching {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "            TEST NAME MATCHING" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    
    if (-not $PgCompanyId) {
        $PgCompanyId = Get-UserInput "Enter PG Company ID"
    }
    
    python test_duplicate_manager.py --pg-company-id $PgCompanyId --test-type name-matching
    Read-Host "Press Enter to continue"
}

# Function to test duplicate detection
function Test-DuplicateDetection {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "          TEST DUPLICATE DETECTION" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    
    if (-not $PgCompanyId) {
        $PgCompanyId = Get-UserInput "Enter PG Company ID"
    }
    
    python test_duplicate_manager.py --pg-company-id $PgCompanyId --test-type duplicate-detection
    Read-Host "Press Enter to continue"
}

# Function to show menu
function Show-Menu {
    while ($true) {
        Write-Host ""
        Write-Host "================================================" -ForegroundColor Cyan
        Write-Host "                   MAIN MENU" -ForegroundColor Cyan
        Write-Host "================================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "1. Setup Environment (First Time Setup)" -ForegroundColor White
        Write-Host "2. Run Tests" -ForegroundColor White
        Write-Host "3. Run Production Mode" -ForegroundColor White
        Write-Host "4. Test Single Patient" -ForegroundColor White
        Write-Host "5. Test Name Matching" -ForegroundColor White
        Write-Host "6. Test Duplicate Detection" -ForegroundColor White
        Write-Host "7. Exit" -ForegroundColor White
        Write-Host ""
        
        $choice = Read-Host "Select an option (1-7)"
        
        switch ($choice) {
            "1" { Run-Setup }
            "2" { Run-Tests }
            "3" { Run-Production }
            "4" { Test-SinglePatient }
            "5" { Test-NameMatching }
            "6" { Test-DuplicateDetection }
            "7" { 
                Write-Host ""
                Write-Host "Thank you for using Duplicate Patient Manager!" -ForegroundColor Green
                return 
            }
            default { 
                Write-Host "Invalid choice. Please try again." -ForegroundColor Red 
            }
        }
    }
}

# Main execution
Show-Header

if (-not (Test-Python)) {
    exit 1
}

Setup-VirtualEnv

# Handle command line parameters
switch ($Mode) {
    "setup" { 
        Run-Setup 
        exit 0
    }
    "test" { 
        if (-not (Test-EnvFile)) { exit 1 }
        Run-Tests 
        exit 0
    }
    "production" { 
        if (-not (Test-EnvFile)) { exit 1 }
        Run-Production 
        exit 0
    }
    "test-patient" { 
        if (-not (Test-EnvFile)) { exit 1 }
        Test-SinglePatient 
        exit 0
    }
    "test-name" { 
        if (-not (Test-EnvFile)) { exit 1 }
        Test-NameMatching 
        exit 0
    }
    "test-duplicate" { 
        if (-not (Test-EnvFile)) { exit 1 }
        Test-DuplicateDetection 
        exit 0
    }
    "menu" { 
        if (-not (Test-EnvFile)) { exit 1 }
        Show-Menu 
    }
}

Write-Host ""
Write-Host "Script completed." -ForegroundColor Green
