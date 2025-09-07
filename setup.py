#!/usr/bin/env python3
"""
Setup script for Duplicate Patient Manager

This script helps set up the environment and install dependencies.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📋 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        return False
    
    print(f"✅ Python version {python_version.major}.{python_version.minor}.{python_version.micro} is compatible")
    return True


def install_dependencies():
    """Install required dependencies"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    return run_command(
        f"pip install -r {requirements_file}",
        "Installing dependencies"
    )


def create_env_file():
    """Create .env file template"""
    env_file = Path(__file__).parent / ".env"
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    env_template = """# Duplicate Patient Manager Environment Variables
# Copy this file to .env and fill in the actual values

# API Authentication
API_TOKEN=YOUR_API_TOKEN_HERE
DA_API_TOKEN=ElPyARpbxZpjUS-gaFY5ueVU7n0JZab-VMaFWpFHZW8ql9QT8takHbCxKcfO4kFyALtZrR317_b3773dG976WGYaUWQcZKCJjqgXJLDh0ibvu39ogbt9k7jHzj-UD3zLXhpgUrQGze1kk9mPXE62icQ_8ecQGVRs1RwCV_k1jUuy5xDjyhq8pePMq-Uge7H5-h3cZKJQP4JdfVApvIUvTKXr6lFUB-J-k4FYZym66X2-asDJK-Ey1S-JhtlzFi5LLRgGPKSPDsGpmgDy5AEJoQ

# Azure OpenAI
AZURE_OPENAI_KEY=EVtCfEbXd2pvVrkOaByfss3HBMJy9x0FvwXdFhCmenum0RLvHCZNJQQJ99BDACYeBjFXJ3w3AAABACOGe7zr
AZURE_OPENAI_ENDPOINT=https://daplatformai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-35-turbo

# Gmail OAuth2
GMAIL_CLIENT_ID=592800963579-4gl24i96kfju80tgus3dh0aubjdgipi7.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=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

# Email Configuration
REPORT_EMAIL=tanay@doctoralliance.com
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_template)
        print("✅ Created .env template file")
        print("   📝 Please edit .env file and add your actual API tokens")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def test_imports():
    """Test if all required modules can be imported"""
    print("📋 Testing imports...")
    
    required_modules = [
        'requests',
        'pdfplumber', 
        'fuzzywuzzy',
        'openai'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"❌ Failed to import: {', '.join(failed_imports)}")
        return False
    
    print("✅ All required modules imported successfully")
    return True


def create_log_directory():
    """Create logs directory"""
    log_dir = Path(__file__).parent / "logs"
    
    try:
        log_dir.mkdir(exist_ok=True)
        print("✅ Created logs directory")
        return True
    except Exception as e:
        print(f"❌ Failed to create logs directory: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 Setting up Duplicate Patient Manager")
    print("=" * 50)
    
    setup_steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Testing imports", test_imports),
        ("Creating .env file template", create_env_file),
        ("Creating log directory", create_log_directory),
    ]
    
    failed_steps = []
    
    for step_name, step_function in setup_steps:
        print(f"\n📋 {step_name}...")
        if not step_function():
            failed_steps.append(step_name)
    
    print("\n" + "=" * 50)
    
    if failed_steps:
        print(f"❌ Setup completed with {len(failed_steps)} failed steps:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n🔧 Please resolve the failed steps before using the application")
        sys.exit(1)
    else:
        print("✅ Setup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Edit .env file with your actual API tokens")
        print("   2. Run tests: python test_duplicate_manager.py --pg-company-id YOUR_PG_COMPANY_ID")
        print("   3. Run production: python duplicate_patient_manager.py --mode production --pg-company-id YOUR_PG_COMPANY_ID")


if __name__ == "__main__":
    main()
