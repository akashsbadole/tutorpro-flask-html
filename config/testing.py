import os
from datetime import timedelta

class TestingConfig:
    TESTING = True
    DEBUG = True
    
    # Database configuration (in-memory SQLite for testing)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key for session management and CSRF protection
    SECRET_KEY = 'test-secret-key'
    
    # Flask-Login configuration
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # Flask-WTF configuration (disabled CSRF for testing)
    WTF_CSRF_ENABLED = False
    
    # Flask-Mail configuration
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Application settings
    ITEMS_PER_PAGE = 20
    
    # Upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'app/static/uploads'
    
    # Cache configuration
    CACHE_TYPE = 'NullCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Disable CSRF tokens for testing
    WTF_CSRF_ENABLED = False