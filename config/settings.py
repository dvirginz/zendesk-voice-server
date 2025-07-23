"""
Configuration settings for the Zendesk Voice Server.
"""

import os
from typing import Optional


class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Zendesk settings
    ZENDESK_DOMAIN = os.getenv('ZENDESK_DOMAIN', '')
    ZENDESK_EMAIL = os.getenv('ZENDESK_EMAIL', '')
    ZENDESK_API_TOKEN = os.getenv('ZENDESK_API_TOKEN', '')
    
    # Twilio settings
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_US_NUMBER = os.getenv('TWILIO_US_NUMBER')
    TWILIO_IL_NUMBER = os.getenv('TWILIO_IL_NUMBER')
    
    # Firebase settings
    FIREBASE_CREDENTIALS_FILE = os.getenv('FIREBASE_CREDENTIALS_FILE', 'firebase-credentials.json')
    FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL', '')
    
    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # API settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    REQUEST_TIMEOUT = 30  # seconds
    
    # Zendesk API settings
    ZENDESK_REQUEST_TIMEOUT = 30  # seconds
    ZENDESK_MAX_RETRIES = 3
    ZENDESK_RETRY_DELAY = 1  # seconds
    
    # Call processing settings
    CALL_PROCESSING_ENABLED = os.getenv('CALL_PROCESSING_ENABLED', 'True').lower() == 'true'
    DUPLICATE_CALL_CHECK = os.getenv('DUPLICATE_CALL_CHECK', 'True').lower() == 'true'
    
    # Ticket settings
    DEFAULT_TICKET_TAGS = ['voice-call', 'automated']
    MAX_SUBJECT_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 10000
    
    # Phone number settings
    DEFAULT_COUNTRY_CODE = '+1'
    PHONE_NUMBER_MIN_LENGTH = 7
    PHONE_NUMBER_MAX_LENGTH = 15


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # Override with production settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production")


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # Use test credentials
    ZENDESK_DOMAIN = 'test.zendesk.com'
    ZENDESK_EMAIL = 'test@example.com'
    ZENDESK_API_TOKEN = 'test-token'


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> Config:
    """
    Get configuration class based on environment.
    
    Args:
        config_name: Name of the configuration to use
        
    Returns:
        Configuration class instance
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default']) 