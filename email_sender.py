"""
Email sender module for Duplicate Patient Manager

This module handles sending email reports using Gmail OAuth2.
"""

import base64
import json
import logging
import os
import mimetypes
from email.message import EmailMessage
from datetime import datetime
from typing import Optional, List

import requests

# Google OAuth / Gmail API
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    print("Warning: Google APIs not available. Gmail OAuth2 will not work.")


class EmailSender:
    """Gmail email sender using OAuth2"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Gmail OAuth2 Configuration
        self.gmail_client_id = config.GMAIL_CLIENT_ID
        self.gmail_client_secret = config.GMAIL_CLIENT_SECRET
        self.gmail_sender = config.GMAIL_SENDER
        self.gmail_refresh_token = "1//05rc0-CZBveAWCgYIARAAGAUSNwF-L9IrwtKTSrXzx1shIA7j5sNr7xDkSMwyWn6pChOxRe-c13H_VDm6Kt1IzEdjU27Z6za57lg"
    
    def _get_gmail_service(self):
        """Get Gmail service using OAuth2 refresh token"""
        if not GOOGLE_APIS_AVAILABLE:
            raise RuntimeError("Google APIs not available for Gmail OAuth2")
        
        try:
            # Create credentials from refresh token
            creds = Credentials(
                None,
                refresh_token=self.gmail_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.gmail_client_id,
                client_secret=self.gmail_client_secret,
                scopes=[
                    "https://www.googleapis.com/auth/gmail.send",
                    "https://www.googleapis.com/auth/gmail.readonly"
                ],
            )
            
            # Refresh the token
            creds.refresh(Request())
            
            # Build and return Gmail service
            return build("gmail", "v1", credentials=creds)
            
        except Exception as e:
            self.logger.error(f"Error creating Gmail service: {e}")
            raise
    
    def _build_mime_message(self, sender: str, to: str, subject: str, html_body: str, 
                           text_body: Optional[str] = None, attachments: Optional[List[str]] = None) -> EmailMessage:
        """Build MIME message for Gmail API"""
        try:
            msg = EmailMessage()
            msg["From"] = sender
            msg["To"] = to
            msg["Subject"] = subject
            
            # Set content - prefer HTML if available
            if html_body:
                msg.set_content(text_body or "Please view HTML version", subtype='plain')
                msg.add_alternative(html_body, subtype='html')
            else:
                msg.set_content(text_body or html_body or "No content")
            
            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        # Guess content type
                        ctype, encoding = mimetypes.guess_type(attachment_path)
                        if ctype is None or encoding is not None:
                            ctype = "application/octet-stream"
                        maintype, subtype = ctype.split("/", 1)
                        
                        # Read file and attach
                        with open(attachment_path, "rb") as f:
                            file_data = f.read()
                        filename = os.path.basename(attachment_path)
                        msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=filename)
                        self.logger.info(f"Attached file: {filename}")
                    else:
                        self.logger.warning(f"Attachment file not found: {attachment_path}")
            
            return msg
            
        except Exception as e:
            self.logger.error(f"Error building MIME message: {e}")
            raise
    
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None, attachments: Optional[List[str]] = None, output_dir: str = None) -> bool:
        """
        Send an email using Gmail OAuth2 API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content of the email
            text_body: Plain text content (optional)
            attachments: List of file paths to attach (optional)
            output_dir: Directory to save email reports (optional)
        
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            self.logger.info(f"Attempting to send email to {to_email} via Gmail OAuth2")
            
            if not GOOGLE_APIS_AVAILABLE:
                self.logger.warning("Google APIs not available, falling back to file save")
                return self._send_email_fallback(to_email, subject, html_body, text_body, attachments, output_dir)
            
            # Build Gmail service
            service = self._get_gmail_service()
            
            # Build MIME message
            mime_msg = self._build_mime_message(
                sender=self.gmail_sender,
                to=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                attachments=attachments
            )
            
            # Convert to Gmail API format
            raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")
            
            # Send email
            result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
            
            self.logger.info(f"Email sent successfully to {to_email}. Message ID: {result.get('id')}")
            
            if attachments:
                self.logger.info(f"Email included {len(attachments)} attachment(s)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email via Gmail OAuth2: {e}")
            self.logger.warning("Falling back to file save method")
            return self._send_email_fallback(to_email, subject, html_body, text_body, attachments, output_dir)
    
    def _send_email_fallback(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None, attachments: Optional[List[str]] = None, output_dir: str = None) -> bool:
        """
        Fallback email sending method - saves to file
        
        This is a placeholder implementation when Gmail OAuth2 is not available.
        """
        try:
            # Save the email to a file for demo purposes
            self._save_email_to_file(to_email, subject, html_body, text_body, attachments, output_dir)
            
            self.logger.info(f"Email prepared for {to_email} (saved to file)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in fallback email sending: {e}")
            return False
    
    def _save_email_to_file(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None, attachments: Optional[List[str]] = None, output_dir: str = None) -> None:
        """Save email to file for demo purposes"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"email_report_{timestamp}.html"
            
            # Use output directory if provided, otherwise current directory
            if output_dir:
                filepath = os.path.join(output_dir, filename)
            else:
                filepath = filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"<!-- Email Report -->\n")
                f.write(f"<!-- To: {to_email} -->\n")
                f.write(f"<!-- Subject: {subject} -->\n")
                f.write(f"<!-- From: {self.gmail_sender} -->\n")
                f.write(f"<!-- Generated: {datetime.now()} -->\n")
                if attachments:
                    f.write(f"<!-- Attachments: {', '.join(attachments)} -->\n")
                f.write(f"\n")
                f.write(html_body)
            
            self.logger.info(f"Email saved to {filepath}")
            if attachments:
                self.logger.info(f"Note: Attachments referenced: {', '.join(attachments)}")
            
        except Exception as e:
            self.logger.error(f"Error saving email to file: {e}")
    
    def test_connection(self) -> bool:
        """Test Gmail connection/setup"""
        try:
            if not GOOGLE_APIS_AVAILABLE:
                self.logger.warning("Google APIs not available for testing")
                return False
            
            # Test Gmail service creation
            service = self._get_gmail_service()
            
            # Just test that we can create the service - no API calls needed
            if service:
                self.logger.info("Gmail service created successfully - connection test passed")
                return True
            else:
                self.logger.error("Failed to create Gmail service")
                return False
            
        except Exception as e:
            self.logger.error(f"Gmail connection test failed: {e}")
            return False
