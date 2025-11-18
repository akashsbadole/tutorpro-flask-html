"""
Error handling utilities for the application
"""

from functools import wraps
from flask import jsonify, current_app, request
from werkzeug.exceptions import HTTPException
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv


def handle_api_errors(f):
    """Decorator to handle API errors and return consistent JSON responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            logger.error(f"API Error: {e.message}")
            return jsonify({
                'success': False,
                'error': e.message,
                'status_code': e.status_code
            }), e.status_code
        except Exception as e:
            logger.error(f"Unhandled Exception: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred',
                'status_code': 500
            }), 500
    return decorated_function


def handle_validation_errors(form):
    """Helper function to handle form validation errors"""
    errors = {}
    for field, field_errors in form.errors.items():
        errors[field] = field_errors[0] if field_errors else 'Invalid input'
    
    return {
        'success': False,
        'error': 'Validation failed',
        'validation_errors': errors
    }


def log_error(error_message, details=None):
    """Log error with optional details"""
    if details:
        logger.error(f"{error_message}: {details}")
    else:
        logger.error(error_message)


def log_info(info_message, details=None):
    """Log info with optional details"""
    if details:
        logger.info(f"{info_message}: {details}")
    else:
        logger.info(info_message)


def log_warning(warning_message, details=None):
    """Log warning with optional details"""
    if details:
        logger.warning(f"{warning_message}: {details}")
    else:
        logger.warning(warning_message)


def safe_int(value, default=0):
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value, default=False):
    """Safely convert value to boolean"""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def validate_date_string(date_string, date_format='%Y-%m-%d'):
    """Validate and parse date string"""
    if not date_string:
        return None
    
    try:
        from datetime import datetime
        return datetime.strptime(date_string, date_format)
    except ValueError:
        return None


def validate_time_string(time_string, time_format='%H:%M'):
    """Validate and parse time string"""
    if not time_string:
        return None
    
    try:
        from datetime import datetime
        return datetime.strptime(time_string, time_format).time()
    except ValueError:
        return None


def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Phone is optional
    
    import re
    # Remove non-digit characters
    digits_only = re.sub(r'[^\d]', '', phone)
    
    # Check if it has a reasonable number of digits (10-15)
    return 10 <= len(digits_only) <= 15


def sanitize_string(input_string, max_length=None):
    """Sanitize string input"""
    if not input_string:
        return ''
    
    # Remove HTML tags
    import re
    sanitized = re.sub(r'<[^>]*>', '', input_string)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_file_upload(file, allowed_extensions=None, max_size_mb=None):
    """Validate uploaded file"""
    if not file:
        return {'valid': True, 'error': None}
    
    errors = []
    
    # Check file extension
    if allowed_extensions:
        import os
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            errors.append(f'File type {file_ext} is not allowed')
    
    # Check file size
    if max_size_mb:
        file_size_mb = file.content_length / (1024 * 1024)
        if file_size_mb > max_size_mb:
            errors.append(f'File size {file_size_mb:.2f}MB exceeds maximum allowed size of {max_size_mb}MB')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def handle_database_error(e):
    """Handle database errors consistently"""
    logger.error(f"Database Error: {str(e)}")
    logger.error(traceback.format_exc())
    
    # Check if it's a known database error
    error_message = "A database error occurred"
    
    # Check for specific error types
    if "foreign key constraint" in str(e).lower():
        error_message = "Referenced record does not exist"
    elif "unique constraint" in str(e).lower():
        error_message = "Record already exists with these details"
    elif "connection" in str(e).lower():
        error_message = "Database connection error"
    
    return error_message


def create_error_response(error_type, message, details=None, status_code=400):
    """Create a standardized error response"""
    response = {
        'success': False,
        'error_type': error_type,
        'message': message
    }
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code


def create_success_response(message, data=None, status_code=200):
    """Create a standardized success response"""
    response = {
        'success': True,
        'message': message
    }
    
    if data:
        response['data'] = data
    
    return jsonify(response), status_code


def rate_limit_exceeded_handler(e):
    """Handler for rate limit exceeded"""
    return create_error_response(
        error_type='rate_limit_exceeded',
        message='Rate limit exceeded. Please try again later.',
        details={'limit': e.description},
        status_code=429
    )


def unauthorized_handler():
    """Handler for unauthorized access"""
    return create_error_response(
        error_type='unauthorized',
        message='You are not authorized to access this resource.',
        status_code=401
    )


def forbidden_handler():
    """Handler for forbidden access"""
    return create_error_response(
        error_type='forbidden',
        message='You do not have permission to access this resource.',
        status_code=403
    )


def not_found_handler():
    """Handler for not found resources"""
    return create_error_response(
        error_type='not_found',
        message='The requested resource was not found.',
        status_code=404
    )


def method_not_allowed_handler():
    """Handler for disallowed HTTP methods"""
    return create_error_response(
        error_type='method_not_allowed',
        message='The method is not allowed for this resource.',
        status_code=405
    )


def server_error_handler(e):
    """Handler for internal server errors"""
    log_error(f"Internal Server Error: {str(e)}", traceback.format_exc())
    return create_error_response(
        error_type='server_error',
        message='An internal server error occurred.',
        status_code=500
    )


def register_error_handlers(app):
    """Register error handlers with the Flask app"""
    app.register_error_handler(APIError, handle_api_error)
    app.register_error_handler(429, rate_limit_exceeded_handler)
    app.register_error_handler(401, unauthorized_handler)
    app.register_error_handler(403, forbidden_handler)
    app.register_error_handler(404, not_found_handler)
    app.register_error_handler(405, method_not_allowed_handler)
    app.register_error_handler(500, server_error_handler)
    app.register_error_handler(Exception, server_error_handler)


def handle_api_error(e):
    """Handle APIError exceptions"""
    return jsonify(e.to_dict()), e.status_code