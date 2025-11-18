import re
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from flask import current_app, request, session
from functools import wraps

logger = logging.getLogger(__name__)

class PaymentSecurity:
    """Security utilities for payment processing"""
    
    @staticmethod
    def validate_amount(amount):
        """Validate payment amount"""
        try:
            # Convert to Decimal for precise calculation
            decimal_amount = Decimal(str(amount))
            
            # Check minimum amount
            min_amount = Decimal(current_app.config.get('MIN_PAYMENT_AMOUNT', '0.01'))
            if decimal_amount < min_amount:
                return False, f"Amount must be at least {min_amount}"
            
            # Check maximum amount
            max_amount = Decimal(current_app.config.get('MAX_PAYMENT_AMOUNT', '10000.00'))
            if decimal_amount > max_amount:
                return False, f"Amount cannot exceed {max_amount}"
            
            # Check for reasonable decimal places (max 2)
            if decimal_amount.as_tuple().exponent < -2:
                return False, "Amount cannot have more than 2 decimal places"
            
            return True, None
            
        except (ValueError, TypeError) as e:
            return False, f"Invalid amount format: {str(e)}"
    
    @staticmethod
    def validate_upi_id(upi_id):
        """Validate UPI ID format"""
        if not upi_id:
            return False, "UPI ID is required"
        
        # Basic UPI ID format check
        upi_pattern = r'^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$'
        if not re.match(upi_pattern, upi_id):
            return False, "Invalid UPI ID format (e.g., username@upi)"
        
        # Additional checks
        if len(upi_id) > 256:
            return False, "UPI ID is too long (max 256 characters)"
        
        return True, None
    
    @staticmethod
    def validate_paypal_email(email):
        """Validate PayPal email address"""
        if not email:
            return False, "PayPal email is required"
        
        # Basic email format check
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        
        # Additional checks
        if len(email) > 254:
            return False, "Email address is too long"
        
        return True, None
    
    @staticmethod
    def validate_card_number(card_number):
        """Validate credit/debit card number"""
        if not card_number:
            return False, "Card number is required"
        
        # Remove spaces and dashes
        clean_number = re.sub(r'[\s-]', '', card_number)
        
        # Check if all digits
        if not clean_number.isdigit():
            return False, "Card number must contain only digits"
        
        # Check length (13-19 digits for most cards)
        if len(clean_number) < 13 or len(clean_number) > 19:
            return False, "Invalid card number length"
        
        # Luhn algorithm check
        if not PaymentSecurity._luhn_check(clean_number):
            return False, "Invalid card number"
        
        return True, None
    
    @staticmethod
    def _luhn_check(card_number):
        """Perform Luhn algorithm check on card number"""
        digits = [int(d) for d in card_number]
        checksum = digits.pop()
        
        # Double every second digit from right
        for i in range(len(digits) - 1, -1, -1):
            if i % 2 == len(digits) % 2:
                digits[i] *= 2
                if digits[i] > 9:
                    digits[i] -= 9
        
        total = sum(digits) + checksum
        return total % 10 == 0
    
    @staticmethod
    def validate_expiry_date(expiry_date):
        """Validate card expiry date"""
        if not expiry_date:
            return False, "Expiry date is required"
        
        # Parse MM/YY format
        try:
            parts = expiry_date.split('/')
            if len(parts) != 2:
                return False, "Invalid expiry date format (use MM/YY)"
            
            month = int(parts[0])
            year = 2000 + int(parts[1])  # Convert YY to YYYY
            
            # Validate month range
            if month < 1 or month > 12:
                return False, "Invalid month"
            
            # Check if not expired
            expiry_date_obj = datetime(year, month, 1)
            if expiry_date_obj < datetime.now():
                return False, "Card has expired"
            
            # Check if not too far in future
            max_future_years = 10
            if year > datetime.now().year + max_future_years:
                return False, f"Expiry date too far in future (max {max_future_years} years)"
            
            return True, None
            
        except (ValueError, IndexError):
            return False, "Invalid expiry date format (use MM/YY)"
    
    @staticmethod
    def validate_cvv(cvv):
        """Validate CVV/CVC"""
        if not cvv:
            return False, "CVV is required"
        
        # Remove spaces
        clean_cvv = re.sub(r'\s', '', cvv)
        
        # Check if all digits
        if not clean_cvv.isdigit():
            return False, "CVV must contain only digits"
        
        # Check length (3 or 4 digits)
        if len(clean_cvv) not in [3, 4]:
            return False, "CVV must be 3 or 4 digits"
        
        return True, None
    
    @staticmethod
    def validate_bank_account(account_number, routing_number=None):
        """Validate bank account details"""
        if not account_number:
            return False, "Account number is required"
        
        # Remove spaces and dashes
        clean_account = re.sub(r'[\s-]', '', account_number)
        
        # Check if all digits
        if not clean_account.isdigit():
            return False, "Account number must contain only digits"
        
        # Check length (typically 6-17 digits)
        if len(clean_account) < 6 or len(clean_account) > 17:
            return False, "Invalid account number length"
        
        # Validate routing number if provided
        if routing_number:
            clean_routing = re.sub(r'[\s-]', '', routing_number)
            
            if not clean_routing.isdigit():
                return False, "Routing number must contain only digits"
            
            if len(clean_routing) != 9:
                return False, "Routing number must be 9 digits"
        
        return True, None
    
    @staticmethod
    def validate_ifsc_code(ifsc_code):
        """Validate Indian IFSC code"""
        if not ifsc_code:
            return False, "IFSC code is required"
        
        # IFSC code format: 4 letters + 0 + 6 digits
        ifsc_pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
        if not re.match(ifsc_pattern, ifsc_code):
            return False, "Invalid IFSC code format (e.g., SBIN0001234)"
        
        return True, None
    
    @staticmethod
    def detect_fraud(payment_data):
        """Basic fraud detection for payment transactions"""
        fraud_score = 0
        fraud_reasons = []
        
        # Check for unusually high amount
        amount = Decimal(str(payment_data.get('amount', 0)))
        max_amount = Decimal(current_app.config.get('FRAUD_MAX_AMOUNT', '5000.00'))
        if amount > max_amount:
            fraud_score += 30
            fraud_reasons.append(f"High amount transaction (${amount})")
        
        # Check for rapid transactions from same user
        user_id = payment_data.get('user_id')
        recent_transactions = PaymentSecurity._get_recent_transactions(user_id, hours=1)
        if len(recent_transactions) > 5:
            fraud_score += 25
            fraud_reasons.append(f"Rapid transactions ({len(recent_transactions)} in last hour)")
        
        # Check for multiple payment methods
        payment_methods = PaymentSecurity._get_user_payment_methods(user_id)
        if len(payment_methods) > 5:
            fraud_score += 15
            fraud_reasons.append(f"Multiple payment methods ({len(payment_methods)})")
        
        # Check for international transactions (if not allowed)
        country = payment_data.get('country')
        allowed_countries = current_app.config.get('ALLOWED_COUNTRIES', ['US', 'CA', 'GB', 'IN'])
        if country and country not in allowed_countries:
            fraud_score += 20
            fraud_reasons.append(f"International transaction from {country}")
        
        # Determine fraud risk level
        if fraud_score >= 50:
            risk_level = "HIGH"
        elif fraud_score >= 25:
            risk_level = "MEDIUM"
        elif fraud_score > 0:
            risk_level = "LOW"
        else:
            risk_level = "NONE"
        
        return {
            'fraud_score': fraud_score,
            'risk_level': risk_level,
            'reasons': fraud_reasons,
            'blocked': fraud_score >= 50
        }
    
    @staticmethod
    def _get_recent_transactions(user_id, hours=24):
        """Get recent transactions for a user (simplified for demo)"""
        # In a real implementation, this would query the database
        # For now, return empty list
        return []
    
    @staticmethod
    def _get_user_payment_methods(user_id):
        """Get user's payment methods (simplified for demo)"""
        # In a real implementation, this would query the database
        # For now, return empty list
        return []
    
    @staticmethod
    def generate_payment_signature(payment_data, secret_key):
        """Generate HMAC signature for payment verification"""
        # Create a string from payment data
        data_string = "&".join([
            f"{k}={v}" for k, v in sorted(payment_data.items())
        ])
        
        # Generate HMAC signature
        signature = hmac.new(
            secret_key.encode('utf-8'),
            data_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def verify_payment_signature(payment_data, signature, secret_key):
        """Verify HMAC signature for payment"""
        # Generate expected signature
        expected_signature = PaymentSecurity.generate_payment_signature(
            payment_data, secret_key
        )
        
        # Compare signatures securely
        return hmac.compare_digest(
            expected_signature.encode('utf-8'),
            signature.encode('utf-8')
        )
    
    @staticmethod
    def sanitize_input(input_string):
        """Sanitize user input to prevent injection attacks"""
        if not input_string:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', 'script', 'javascript', 'onload', 'onerror']
        sanitized = input_string
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Limit length
        max_length = 255
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_refund_request(payment, refund_amount, refund_reason):
        """Validate refund request"""
        # Check if payment can be refunded
        if payment.status != 'Completed':
            return False, "Only completed payments can be refunded"
        
        # Check refund policy days
        refund_policy_days = current_app.config.get('REFUND_POLICY_DAYS', 7)
        if payment.processed_at:
            days_since_payment = (datetime.now() - payment.processed_at).days
            if days_since_payment > refund_policy_days:
                return False, f"Refund request exceeds {refund_policy_days} days policy"
        
        # Check refund amount
        if Decimal(str(refund_amount)) > payment.amount:
            return False, "Refund amount cannot exceed original payment amount"
        
        # Check minimum refund amount
        min_refund = Decimal(current_app.config.get('MIN_REFUND_AMOUNT', '0.01'))
        if Decimal(str(refund_amount)) < min_refund:
            return False, f"Refund amount must be at least {min_refund}"
        
        # Check refund reason
        if not refund_reason or len(refund_reason.strip()) < 10:
            return False, "Refund reason must be at least 10 characters"
        
        # Check maximum refund reason length
        if len(refund_reason) > 500:
            return False, "Refund reason is too long (max 500 characters)"
        
        return True, None
    
    @staticmethod
    def log_payment_attempt(payment_data, result, error_message=None):
        """Log payment attempt for audit trail"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': payment_data.get('user_id'),
            'payment_method': payment_data.get('payment_method'),
            'amount': payment_data.get('amount'),
            'currency': payment_data.get('currency'),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'result': result,
            'error_message': error_message
        }
        
        if result == 'SUCCESS':
            logger.info(f"Payment successful: {log_data}")
        elif result == 'FAILED':
            logger.warning(f"Payment failed: {log_data}")
        else:
            logger.error(f"Payment error: {log_data}")
    
    @staticmethod
    def rate_limit_check(user_id, action='payment'):
        """Check if user exceeds rate limits"""
        # Get rate limit settings
        max_attempts = current_app.config.get(f'RATE_LIMIT_{action.upper()}', 10)
        time_window = current_app.config.get(f'RATE_LIMIT_{action.upper()}_WINDOW', 3600)  # 1 hour
        
        # Check session for previous attempts
        session_key = f'{action}_attempts'
        attempts = session.get(session_key, [])
        
        # Clean old attempts
        current_time = datetime.utcnow().timestamp()
        valid_attempts = [
            attempt for attempt in attempts 
            if current_time - attempt['timestamp'] < time_window
        ]
        
        # Update session
        session[session_key] = valid_attempts
        
        # Check if limit exceeded
        if len(valid_attempts) >= max_attempts:
            return False, f"Rate limit exceeded. Maximum {max_attempts} attempts per {time_window//3600} hour(s)."
        
        # Add current attempt
        valid_attempts.append({
            'timestamp': current_time,
            'data': {
                'amount': request.form.get('amount'),
                'method': request.form.get('payment_method')
            }
        })
        session[session_key] = valid_attempts
        
        return True, None

def require_payment_security(f):
    """Decorator to add payment security checks to routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for CSRF token
        if not current_app.config.get('WTF_CSRF_ENABLED', True):
            return f(*args, **kwargs)
        
        # Validate CSRF token
        csrf_token = request.form.get('csrf_token')
        if not csrf_token or not csrf_token == session.get('csrf_token'):
            logger.warning(f"CSRF token mismatch from IP: {request.remote_addr}")
            return {"error": "Invalid CSRF token"}, 403
        
        # Check rate limiting
        user_id = getattr(request, 'user_id', None)
        if user_id:
            valid, message = PaymentSecurity.rate_limit_check(user_id)
            if not valid:
                logger.warning(f"Rate limit exceeded for user {user_id}: {message}")
                return {"error": message}, 429
        
        return f(*args, **kwargs)
    
    return decorated_function