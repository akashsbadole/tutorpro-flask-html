import secrets
import hashlib
import hmac
import re
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models.meeting import Meeting, MeetingParticipant


class MeetingSecurity:
    """Security utilities for meeting management"""
    
    @staticmethod
    def generate_secure_meeting_id():
        """Generate a secure meeting ID"""
        return secrets.token_urlsafe(16)
    
    @staticmethod
    def generate_secure_password(length=8):
        """Generate a secure meeting password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def generate_host_key():
        """Generate a secure host key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_one_time_link(meeting_id, expires_in_hours=24):
        """Generate a one-time meeting link"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Store token in database (this would be implemented in a separate model)
        # For now, return the token and expiry
        return {
            'token': token,
            'expires_at': expires_at,
            'link': f"/meeting/join/{meeting_id}?token={token}"
        }
    
    @staticmethod
    def validate_one_time_link(meeting_id, token):
        """Validate a one-time meeting link"""
        # Check if token exists and is not expired
        # This would typically check against a database table
        # For now, return True as placeholder
        return True
    
    @staticmethod
    def hash_password(password, salt=None):
        """Hash a password securely"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for password hashing
        import hashlib
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        
        key = kdf.derive(password.encode())
        return {
            'hash': key.hex(),
            'salt': salt
        }
    
    @staticmethod
    def verify_password(password, hashed_password, salt):
        """Verify a password against its hash"""
        import hashlib
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        
        key = kdf.derive(password.encode())
        return hmac.compare_digest(key.hex(), hashed_password)
    
    @staticmethod
    def validate_meeting_url(url):
        """Validate meeting URL format"""
        url_pattern = re.compile(
            r'^(https?:\/\/)?(www\.)?(zoom\.us|meet\.google\.com|teams\.microsoft\.com)\/.+$',
            re.IGNORECASE
        )
        
        return bool(url_pattern.match(url))
    
    @staticmethod
    def sanitize_meeting_data(data):
        """Sanitize meeting data to prevent XSS"""
        import html
        
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = html.escape(value)
            elif isinstance(value, dict):
                sanitized[key] = MeetingSecurity.sanitize_meeting_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def check_meeting_permissions(user, meeting, action):
        """Check if user has permission to perform action on meeting"""
        # Admin can do everything
        if user.is_admin():
            return True
        
        # Host can do everything on their meetings
        if meeting.host_id == user.id:
            return True
        
        # Participants can join and view
        if action in ['join', 'view']:
            participant = MeetingParticipant.query.filter_by(
                meeting_id=meeting.id, user_id=user.id
            ).first()
            
            return participant is not None
        
        return False
    
    @staticmethod
    def is_meeting_expired(meeting):
        """Check if meeting link has expired"""
        if not meeting.link_expires_at:
            return False
        
        return datetime.utcnow() > meeting.link_expires_at
    
    @staticmethod
    def generate_webhook_signature(payload, secret):
        """Generate webhook signature for verification"""
        import json
        
        message = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def verify_webhook_signature(payload, signature, secret):
        """Verify webhook signature"""
        expected_signature = MeetingSecurity.generate_webhook_signature(payload, secret)
        return hmac.compare_digest(expected_signature, signature)
    
    @staticmethod
    def encrypt_meeting_data(data, key):
        """Encrypt sensitive meeting data"""
        from cryptography.fernet import Fernet
        
        f = Fernet(key)
        encrypted_data = f.encrypt(json.dumps(data).encode())
        
        return encrypted_data
    
    @staticmethod
    def decrypt_meeting_data(encrypted_data, key):
        """Decrypt sensitive meeting data"""
        from cryptography.fernet import Fernet
        
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data).decode()
        
        return json.loads(decrypted_data)
    
    @staticmethod
    def generate_meeting_checksum(meeting_data):
        """Generate checksum for meeting data integrity"""
        data_string = json.dumps(meeting_data, sort_keys=True)
        checksum = hashlib.sha256(data_string.encode()).hexdigest()
        
        return checksum
    
    @staticmethod
    def verify_meeting_checksum(meeting_data, checksum):
        """Verify meeting data integrity"""
        expected_checksum = MeetingSecurity.generate_meeting_checksum(meeting_data)
        return hmac.compare_digest(expected_checksum, checksum)
    
    @staticmethod
    def rate_limit_check(user_id, action, limit=10, window_minutes=60):
        """Check if user has exceeded rate limit"""
        # This would typically use Redis or similar for rate limiting
        # For now, return False (not rate limited)
        return False
    
    @staticmethod
    def validate_meeting_time(scheduled_time, duration_minutes):
        """Validate meeting time constraints"""
        now = datetime.utcnow()
        
        # Check if meeting is in the future
        if scheduled_time <= now:
            return False, "Meeting must be scheduled for a future time"
        
        # Check if meeting is too far in the future (e.g., more than 1 year)
        max_future = now + timedelta(days=365)
        if scheduled_time > max_future:
            return False, "Meeting cannot be scheduled more than 1 year in advance"
        
        # Check duration constraints
        if duration_minutes < 15:
            return False, "Meeting duration must be at least 15 minutes"
        
        if duration_minutes > 480:  # 8 hours
            return False, "Meeting duration cannot exceed 8 hours"
        
        # Check if meeting is during business hours (optional)
        hour = scheduled_time.hour
        if hour < 6 or hour > 22:
            return False, "Meetings should be scheduled between 6 AM and 10 PM"
        
        return True, "Valid meeting time"
    
    @staticmethod
    def validate_participant_capacity(meeting, new_participants=0):
        """Validate meeting participant capacity"""
        current_participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id).count()
        total_participants = current_participants + new_participants
        
        if total_participants > meeting.max_participants:
            return False, f"Meeting capacity exceeded. Maximum {meeting.max_participants} participants allowed"
        
        return True, "Participant capacity valid"
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename to prevent directory traversal"""
        import os
        
        # Remove directory separators
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename
    
    @staticmethod
    def validate_file_upload(file, allowed_extensions=None, max_size_mb=100):
        """Validate uploaded file"""
        if allowed_extensions is None:
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.png', '.mp4', '.mp3']
        
        # Check file extension
        filename = file.filename.lower()
        allowed = any(filename.endswith(ext) for ext in allowed_extensions)
        
        if not allowed:
            return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell() / (1024 * 1024)  # Convert to MB
        
        if file_size > max_size_mb:
            return False, f"File size exceeds maximum allowed size of {max_size_mb}MB"
        
        return True, "File validation passed"
    
    @staticmethod
    def audit_log(meeting_id, user_id, action, details=None):
        """Log meeting-related actions for audit trail"""
        # This would typically write to a secure audit log
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'meeting_id': meeting_id,
            'user_id': user_id,
            'action': action,
            'details': details,
            'ip_address': request.remote_addr if 'request' in globals() else None
        }
        
        # Log to application logger (in production, this would go to a secure audit system)
        current_app.logger.info(f"Meeting Audit: {audit_entry}")
        
        return audit_entry


class MeetingValidator:
    """Meeting data validation utilities"""
    
    @staticmethod
    def validate_meeting_creation(data, user):
        """Validate meeting creation data"""
        errors = []
        
        # Required fields
        required_fields = ['title', 'scheduled_time', 'duration_minutes', 'platform']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field} is required")
        
        # Title validation
        if 'title' in data:
            title = data['title']
            if len(title) < 3:
                errors.append("Title must be at least 3 characters long")
            elif len(title) > 200:
                errors.append("Title cannot exceed 200 characters")
        
        # Time validation
        if 'scheduled_time' in data and 'duration_minutes' in data:
            valid, message = MeetingSecurity.validate_meeting_time(
                data['scheduled_time'], 
                data['duration_minutes']
            )
            if not valid:
                errors.append(message)
        
        # Platform validation
        if 'platform' in data:
            platform = data['platform']
            valid_platforms = ['Zoom', 'Google Meet', 'Microsoft Teams', 'Custom']
            if platform not in valid_platforms:
                errors.append(f"Invalid platform. Must be one of: {', '.join(valid_platforms)}")
        
        # URL validation
        if 'meeting_url' in data and data['meeting_url']:
            url = data['meeting_url']
            if not MeetingSecurity.validate_meeting_url(url):
                errors.append("Invalid meeting URL format")
        
        # Password validation
        if 'require_password' in data and data['require_password']:
            if 'password' not in data or not data['password']:
                errors.append("Password is required when password protection is enabled")
            elif 'password' in data and len(data['password']) < 4:
                errors.append("Password must be at least 4 characters long")
        
        # Participant limit validation
        if 'max_participants' in data:
            max_participants = data['max_participants']
            if max_participants < 1 or max_participants > 1000:
                errors.append("Maximum participants must be between 1 and 1000")
        
        return errors
    
    @staticmethod
    def validate_meeting_update(data, meeting, user):
        """Validate meeting update data"""
        errors = []
        
        # Check if meeting is editable by user
        if not MeetingSecurity.check_meeting_permissions(user, meeting, 'edit'):
            errors.append("You don't have permission to edit this meeting")
            return errors
        
        # Additional validation for updates
        if meeting.status in ['Ongoing', 'Completed']:
            errors.append("Cannot edit a meeting that is ongoing or completed")
        
        return errors
    
    @staticmethod
    def validate_meeting_join(meeting, user):
        """Validate meeting join request"""
        errors = []
        
        # Check if meeting is joinable
        if meeting.status not in ['Scheduled', 'Ongoing']:
            errors.append("Meeting is not available for joining")
        
        # Check if user is a participant
        participant = MeetingParticipant.query.filter_by(
            meeting_id=meeting.id, user_id=user.id
        ).first()
        
        if not participant and meeting.host_id != user.id:
            errors.append("You are not authorized to join this meeting")
        
        # Check if meeting is expired
        if MeetingSecurity.is_meeting_expired(meeting):
            errors.append("Meeting link has expired")
        
        # Check capacity
        valid, message = MeetingSecurity.validate_participant_capacity(meeting)
        if not valid:
            errors.append(message)
        
        return errors