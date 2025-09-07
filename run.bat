@echo off
REM Duplicate Patient Manager - Windows Batch Runner
REM This script provides an easy way to run the duplicate patient manager on Windows

echo.
echo ================================================
echo   Duplicate Patient Manager - Windows Runner
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo Installing/updating dependencies...
    pip install -r requirements.txt
    echo.
)

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please run setup.py first to create the environment template:
    echo   python setup.py
    echo.
    pause
    exit /b 1
)

:MENU
echo.
echo ================================================
echo                   MAIN MENU
echo ================================================
echo.
echo 1. Setup Environment (First Time Setup)
echo 2. Run Tests
echo 3. Run Production Mode
echo 4. Test Single Patient
echo 5. Test Name Matching
echo 6. Test Duplicate Detection
echo 7. Exit
echo.
set /p choice="Select an option (1-7): "

if "%choice%"=="1" goto SETUP
if "%choice%"=="2" goto TEST
if "%choice%"=="3" goto PRODUCTION
if "%choice%"=="4" goto TEST_PATIENT
if "%choice%"=="5" goto TEST_NAME
if "%choice%"=="6" goto TEST_DUPLICATE
if "%choice%"=="7" goto EXIT
echo Invalid choice. Please try again.
goto MENU

:SETUP
echo.
echo ================================================
echo              ENVIRONMENT SETUP
echo ================================================
python setup.py
pause
goto MENU

:TEST
echo.
echo ================================================
echo                 RUN TESTS
echo ================================================
echo.
set /p pg_company="Enter PG Company ID: "
set /p test_patient="Enter Test Patient ID (optional, press Enter to skip): "

if "%test_patient%"=="" (
    python test_duplicate_manager.py --pg-company-id "%pg_company%"
) else (
    python test_duplicate_manager.py --pg-company-id "%pg_company%" --test-patient-id "%test_patient%"
)
pause
goto MENU

:PRODUCTION
echo.
echo ================================================
echo              PRODUCTION MODE
echo ================================================
echo.
echo WARNING: This will process and modify actual patient data!
set /p confirm="Are you sure you want to continue? (yes/no): "
if /i not "%confirm%"=="yes" (
    echo Operation cancelled.
    goto MENU
)

set /p pg_company="Enter PG Company ID: "
python duplicate_patient_manager.py --mode production --pg-company-id "%pg_company%"
pause
goto MENU

:TEST_PATIENT
echo.
echo ================================================
echo            TEST SINGLE PATIENT
echo ================================================
echo.
set /p pg_company="Enter PG Company ID: "
set /p patient_id="Enter Patient ID: "
python test_duplicate_manager.py --pg-company-id "%pg_company%" --test-patient-id "%patient_id%" --test-type single-patient
pause
goto MENU

:TEST_NAME
echo.
echo ================================================
echo            TEST NAME MATCHING
echo ================================================
echo.
set /p pg_company="Enter PG Company ID: "
python test_duplicate_manager.py --pg-company-id "%pg_company%" --test-type name-matching
pause
goto MENU

:TEST_DUPLICATE
echo.
echo ================================================
echo          TEST DUPLICATE DETECTION
echo ================================================
echo.
set /p pg_company="Enter PG Company ID: "
python test_duplicate_manager.py --pg-company-id "%pg_company%" --test-type duplicate-detection
pause
goto MENU

:EXIT
echo.
echo Deactivating virtual environment...
deactivate
echo.
echo Thank you for using Duplicate Patient Manager!
pause
exit /b 0
