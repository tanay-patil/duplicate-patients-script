#!/usr/bin/env python3
"""
Test script for Email Sender

This script tests the email functionality including connection and sending.
"""

import sys
import logging
from datetime import datetime
from config import Config
from email_sender import EmailSender


def setup_logging():
    """Setup basic logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def test_email_connection():
    """Test email connection"""
    print("=" * 60)
    print("EMAIL CONNECTION TEST")
    print("=" * 60)
    
    try:
        # Load configuration
        print("Loading configuration...")
        config = Config()
        
        # Initialize email sender
        print("Initializing email sender...")
        email_sender = EmailSender(config)
        
        # Test connection
        print("Testing Gmail connection...")
        if email_sender.test_connection():
            print("✓ Gmail connection test PASSED")
            return True
        else:
            print("✗ Gmail connection test FAILED")
            return False
            
    except Exception as e:
        print(f"✗ Error during connection test: {e}")
        return False


def test_send_email():
    """Test sending an email"""
    print("\n" + "=" * 60)
    print("EMAIL SEND TEST")
    print("=" * 60)
    
    try:
        # Load configuration
        config = Config()
        email_sender = EmailSender(config)
        
        # Get recipient email
        recipient = input("Enter recipient email address: ").strip()
        if not recipient:
            print("No recipient provided, skipping send test")
            return False
        
        # Prepare test email content
        subject = f"Test Email from Duplicate Patient Manager - {sys.platform}"
        html_body = """
        <html>
        <body>
        <h2>Email Test Successful!</h2>
        <p>This is a test email from the Duplicate Patient Manager system.</p>
        <p><strong>Test Details:</strong></p>
        <ul>
            <li>Platform: {platform}</li>
            <li>Python Version: {python_version}</li>
            <li>Time: {timestamp}</li>
        </ul>
        <p>If you received this email, the email system is working correctly.</p>
        </body>
        </html>
        """.format(
            platform=sys.platform,
            python_version=sys.version,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        text_body = f"""
        Email Test Successful!
        
        This is a test email from the Duplicate Patient Manager system.
        
        Test Details:
        - Platform: {sys.platform}
        - Python Version: {sys.version}
        - Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        If you received this email, the email system is working correctly.
        """
        
        print(f"Sending test email to: {recipient}")
        
        # Send email
        success = email_sender.send_email(
            to_email=recipient,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        
        if success:
            print("✓ Email send test PASSED")
            print(f"Check the inbox at {recipient} for the test email")
            return True
        else:
            print("✗ Email send test FAILED")
            return False
            
    except Exception as e:
        print(f"✗ Error during send test: {e}")
        return False


def main():
    """Main test function"""
    setup_logging()
    
    print("Starting Email Sender Tests...")
    print()
    
    # Test 1: Connection
    connection_ok = test_email_connection()
    
    if connection_ok:
        # Test 2: Send email (optional)
        print("\nDo you want to test sending an actual email?")
        choice = input("Enter 'y' to send test email, or any other key to skip: ").strip().lower()
        
        if choice == 'y':
            test_send_email()
        else:
            print("Skipping email send test")
    else:
        print("\nSkipping email send test due to connection failure")
    
    print("\n" + "=" * 60)
    print("EMAIL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
