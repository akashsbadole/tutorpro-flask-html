import os
from datetime import timedelta

class DevelopmentConfig:
    DEBUG = True
    TESTING = False
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tutorPro_dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Flask-Login configuration
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # Flask-WTF configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
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
    
    # Course materials upload configuration
    COURSE_MATERIALS_FOLDER = os.path.join(UPLOAD_FOLDER, 'course_materials')
    ASSIGNMENT_SUBMISSIONS_FOLDER = os.path.join(UPLOAD_FOLDER, 'assignment_submissions')
    
    # Allowed file extensions
    ALLOWED_MATERIAL_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'mp4', 'avi', 'mov', 'jpg', 'jpeg', 'png', 'gif', 'txt', 'zip', 'rar'}
    ALLOWED_ASSIGNMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'zip', 'rar', 'jpg', 'jpeg', 'png', 'gif'}
    
    # File size limits (in bytes)
    MAX_MATERIAL_SIZE = 50 * 1024 * 1024  # 50MB for course materials
    MAX_ASSIGNMENT_SIZE = 20 * 1024 * 1024  # 20MB for assignment submissions
    
    # Cache configuration
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Security Settings
    FRAUD_MAX_AMOUNT = 5000.00
    ALLOWED_COUNTRIES = ['US', 'CA', 'GB', 'IN']
    RATE_LIMIT_PAYMENT = 10
    RATE_LIMIT_PAYMENT_WINDOW = 3600  # 1 hour in seconds
    RATE_LIMIT_REFUND = 5
    RATE_LIMIT_REFUND_WINDOW = 3600  # 1 hour in seconds
    
    # Payment Encryption
    PAYMENT_DB_ENCRYPTION_KEY = os.environ.get('PAYMENT_DB_ENCRYPTION_KEY', 'default-key-change-in-production')
    
    # Webhook Configuration
    PAYPAL_WEBHOOK_ID = os.environ.get('PAYPAL_WEBHOOK_ID')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET')
    
    # Email Configuration for Payment Notifications
    PAYMENT_NOTIFICATION_EMAIL = os.environ.get('PAYMENT_NOTIFICATION_EMAIL', 'payments@tutorpro.com')
    REFUND_NOTIFICATION_EMAIL = os.environ.get('REFUND_NOTIFICATION_EMAIL', 'refunds@tutorpro.com')
    PAYOUT_NOTIFICATION_EMAIL = os.environ.get('PAYOUT_NOTIFICATION_EMAIL', 'payouts@tutorpro.com')
    
    # Payment Gateway Configuration
    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
    PAYPAL_ENVIRONMENT = 'sandbox'  # 'sandbox' for development, 'live' for production
    
    # Razorpay Configuration (for UPI payments)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
    
    # Payment Settings
    PAYMENT_CURRENCY = 'USD'
    PAYMENT_TIMEOUT_MINUTES = 30
    REFUND_POLICY_DAYS = 7
    PAYOUT_PROCESSING_DAYS = 3
    MIN_PAYMENT_AMOUNT = 0.01
    MAX_PAYMENT_AMOUNT = 10000.00
    MIN_PAYOUT_AMOUNT = 10.00
    MIN_REFUND_AMOUNT = 0.01