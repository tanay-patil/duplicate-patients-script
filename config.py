"""
Configuration file for Duplicate Patient Manager

This file contains all the configuration settings, API endpoints,
and authentication details required for the application.
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class containing all settings"""
    
    # ======== API ENDPOINTS ========
    BASE_URL = "https://dawavorderpatient-hqe2apddbje9gte0.eastus-01.azurewebsites.net"
    DOCUMENT_API_URL = "https://api.doctoralliance.com/document/getfile"
    
    # ======== AUTHENTICATION ========
    # Note: In production, these should be environment variables
    API_TOKEN = "YOUR_API_TOKEN_HERE"  # Replace with actual token
    DA_API_TOKEN = "wel7QChenJgbZOgX76KQX_w5oebAR6Mi3SKt_BNP8rUNUp5lsry4FhleWttCw0KCqpC-cHlU0_tEv5dKOuwh6IB8ZSdb-rf-EwddsK047HIOEN6b4Jjhth766VTTF4Z8RzjLfvwCM3zrEIVGOVzojBR7_iqpUyUKZ3_2g3qVS8snSH1ATH8ZZHphNVkjPzEMqLFUiMUKvmohpTrZ-yTndsCIz7ocWqFhPO8Gx1F3JilZ5ecHd34aJeNeaIpGHEyaAEz-wt8jMZvVI82vkpNCXg"
    
    # ======== AZURE OPENAI CONFIG ========
    AZURE_OPENAI_KEY = "EVtCfEbXd2pvVrkOaByfss3HBMJy9x0FvwXdFhCmenum0RLvHCZNJQQJ99BDACYeBjFXJ3w3AAABACOGe7zr"
    AZURE_OPENAI_ENDPOINT = "https://daplatformai.openai.azure.com/"
    AZURE_OPENAI_DEPLOYMENT = "gpt-35-turbo"
    
    # ======== OAUTH / GMAIL CONFIG ========
    GMAIL_SENDER = "rpa@doctoralliance.com"
    GMAIL_CLIENT_ID = "592800963579-4gl24i96kfju80tgus3dh0aubjdgipi7.apps.googleusercontent.com"
    GMAIL_CLIENT_SECRET = "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"
    GMAIL_REDIRECT_URI = "https://dawavadmin-djb0f9atf8e6cwgx.eastus-01.azurewebsites.net/api/Gmail/oauth2callback"
    
    # ======== EMAIL CONFIG ========
    REPORT_EMAIL = "tanay@doctoralliance.com"
    
    # SMTP Email Configuration (Optional - for better email delivery)
    SMTP_SERVER = ""  # e.g., "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USE_TLS = True
    SMTP_USERNAME = ""  # Your email address
    SMTP_PASSWORD = ""  # Your email password or app-specific password
    SMTP_FROM_EMAIL = ""  # From email address
    
    # ======== PROCESSING CONFIG ========
    NAME_SIMILARITY_THRESHOLD = 85  # Minimum similarity percentage for name matching
    REQUEST_TIMEOUT = 30  # Timeout for API requests in seconds
    ENABLE_RCM_CALLS = True  # Set to False to disable RCM API calls
    
    # ======== API ENDPOINTS MAPPING ========
    ENDPOINTS = {
        'patients_by_pg_company': '/api/Patient/company/pg/{id}',
        'orders_by_patient': '/api/Order/patient/{id}',
        'ccnotes_by_patient': '/api/CCNotes/patient/{id}',
        'update_order': '/api/Order/{id}',
        'update_ccnote': '/api/CCNotes/{id}',
        'delete_patient': '/api/Patient/{id}',
        'rcm_deleted_patient': '/api/RCM/rcm/patient/{id}',
        'rcm_kept_patient': '/api/RCM/cron-by-patient/{id}'
    }
    
    @property
    def HEADERS(self) -> Dict[str, str]:
        """Return HTTP headers for API requests"""
        return {
            "Authorization": f"Bearer {self.API_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @property 
    def DA_HEADERS(self) -> Dict[str, str]:
        """Return HTTP headers for Doctor Alliance API requests"""
        return {
            "Authorization": f"Bearer {self.DA_API_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get_endpoint_url(self, endpoint_key: str, **kwargs) -> str:
        """Get full URL for an endpoint with parameter substitution"""
        endpoint = self.ENDPOINTS.get(endpoint_key)
        if not endpoint:
            raise ValueError(f"Unknown endpoint: {endpoint_key}")
        
        # Substitute parameters
        for key, value in kwargs.items():
            endpoint = endpoint.replace(f'{{{key}}}', str(value))
        
        return f"{self.BASE_URL}{endpoint}"
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables"""
        config = cls()
        
        # Override with environment variables if available
        config.API_TOKEN = os.getenv('API_TOKEN', config.API_TOKEN)
        config.DA_API_TOKEN = os.getenv('DA_API_TOKEN', config.DA_API_TOKEN)
        config.AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY', config.AZURE_OPENAI_KEY)
        config.AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', config.AZURE_OPENAI_ENDPOINT)
        config.AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', config.AZURE_OPENAI_DEPLOYMENT)
        config.GMAIL_CLIENT_ID = os.getenv('GMAIL_CLIENT_ID', config.GMAIL_CLIENT_ID)
        config.GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET', config.GMAIL_CLIENT_SECRET)
        config.REPORT_EMAIL = os.getenv('REPORT_EMAIL', config.REPORT_EMAIL)
        
        # SMTP configuration
        config.SMTP_SERVER = os.getenv('SMTP_SERVER', config.SMTP_SERVER)
        config.SMTP_PORT = int(os.getenv('SMTP_PORT', str(config.SMTP_PORT)))
        config.SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() in ('true', '1', 'yes', 'on')
        config.SMTP_USERNAME = os.getenv('SMTP_USERNAME', config.SMTP_USERNAME)
        config.SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', config.SMTP_PASSWORD)
        config.SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', config.SMTP_FROM_EMAIL)
        
        # Processing configuration
        config.NAME_SIMILARITY_THRESHOLD = int(os.getenv('NAME_SIMILARITY_THRESHOLD', str(config.NAME_SIMILARITY_THRESHOLD)))
        config.REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', str(config.REQUEST_TIMEOUT)))
        config.ENABLE_RCM_CALLS = os.getenv('ENABLE_RCM_CALLS', 'True').lower() in ('true', '1', 'yes', 'on')
        
        return config
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        required_fields = [
            'API_TOKEN', 'DA_API_TOKEN', 'AZURE_OPENAI_KEY', 
            'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_DEPLOYMENT',
            'GMAIL_CLIENT_ID', 'GMAIL_CLIENT_SECRET', 'REPORT_EMAIL'
        ]
        
        for field in required_fields:
            if not getattr(self, field) or getattr(self, field) == f"YOUR_{field}_HERE":
                print(f"Configuration validation failed: {field} is not set")
                return False
        
        return True
