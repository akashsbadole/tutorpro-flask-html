from datetime import datetime, timedelta
from app import db
import uuid
import qrcode
import io
import base64

class Certificate(db.Model):
    """
    Certificate model for course completion and achievements
    """
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Certificate details
    certificate_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Unique certificate identifier
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Recipient details
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    recipient_name = db.Column(db.String(200), nullable=False)
    recipient_email = db.Column(db.String(255))
    
    # Issuer details
    issuer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)  # Tutor who issued
    issuer_name = db.Column(db.String(200), nullable=False)
    issuer_title = db.Column(db.String(200))
    
    # Course details
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True, index=True)
    course_name = db.Column(db.String(200))
    course_description = db.Column(db.Text)
    
    # Certificate template
    template_id = db.Column(db.Integer, db.ForeignKey('certificate_templates.id'), nullable=False, index=True)
    
    # Certificate content
    completion_date = db.Column(db.Date, nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expiry_date = db.Column(db.Date)
    
    # Certificate metadata
    grade = db.Column(db.String(20))  # e.g., "A+", "Pass", "Excellent"
    score = db.Column(db.Float)  # Numeric score if applicable
    total_hours = db.Column(db.Float)  # Total learning hours
    
    # Certificate verification
    verification_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    qr_code_data = db.Column(db.Text)  # Base64 encoded QR code image
    verification_url = db.Column(db.String(500))
    
    # Certificate status
    status = db.Column(db.Enum(
        'Draft',
        'Issued',
        'Revoked',
        'Expired',
        name='certificate_statuses'
    ), nullable=False, default='Draft', index=True)
    
    revocation_reason = db.Column(db.String(500))
    revoked_at = db.Column(db.DateTime)
    revoked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Certificate settings
    is_public = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Additional fields
    custom_fields = db.Column(db.Text)  # JSON object for custom certificate fields
    digital_signature = db.Column(db.Text)  # Digital signature data
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_certificates')
    issuer = db.relationship('User', foreign_keys=[issuer_id], backref='issued_certificates')
    revoker = db.relationship('User', foreign_keys=[revoked_by])
    course = db.relationship('Course', backref='certificates')
    template = db.relationship('CertificateTemplate', backref='certificates')
    sharing = db.relationship('CertificateSharing', backref='certificate', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Certificate, self).__init__(**kwargs)
        if not self.certificate_id:
            self.certificate_id = self.generate_certificate_id()
        if not self.verification_code:
            self.verification_code = self.generate_verification_code()
        if not self.verification_url:
            self.verification_url = f"/verify/{self.verification_code}"
    
    def __repr__(self):
        return f'<Certificate {self.id}: {self.title}>'
    
    def generate_certificate_id(self):
        """Generate unique certificate ID"""
        prefix = "CERT"
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"{prefix}-{timestamp}-{unique_id}"
    
    def generate_verification_code(self):
        """Generate unique verification code"""
        return str(uuid.uuid4())[:12].upper()
    
    def generate_qr_code(self):
        """Generate QR code for certificate verification"""
        if not self.verification_url:
            return None
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.verification_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for storage
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    
    def is_valid(self):
        """Check if certificate is valid"""
        if self.status != 'Issued':
            return False
        
        if self.expiry_date and self.expiry_date < datetime.utcnow().date():
            return False
        
        return True
    
    def is_expired(self):
        """Check if certificate has expired"""
        if not self.expiry_date:
            return False
        return self.expiry_date < datetime.utcnow().date()
    
    def revoke(self, reason, revoked_by):
        """Revoke certificate"""
        self.status = 'Revoked'
        self.revocation_reason = reason
        self.revoked_at = datetime.utcnow()
        self.revoked_by = revoked_by
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'certificate_id': self.certificate_id,
            'title': self.title,
            'description': self.description,
            'recipient_id': self.recipient_id,
            'recipient_name': self.recipient_name,
            'recipient_email': self.recipient_email,
            'issuer_id': self.issuer_id,
            'issuer_name': self.issuer_name,
            'issuer_title': self.issuer_title,
            'course_id': self.course_id,
            'course_name': self.course_name,
            'course_description': self.course_description,
            'template_id': self.template_id,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'grade': self.grade,
            'score': self.score,
            'total_hours': self.total_hours,
            'verification_code': self.verification_code,
            'qr_code_data': self.qr_code_data,
            'verification_url': self.verification_url,
            'status': self.status,
            'revocation_reason': self.revocation_reason,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'revoked_by': self.revoked_by,
            'is_public': self.is_public,
            'is_featured': self.is_featured,
            'custom_fields': self.custom_fields,
            'digital_signature': self.digital_signature,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_valid': self.is_valid(),
            'is_expired': self.is_expired()
        }


class CertificateTemplate(db.Model):
    """
    Certificate template model for different certificate designs
    """
    __tablename__ = 'certificate_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template details
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    template_type = db.Column(db.Enum(
        'Course Completion',
        'Achievement',
        'Excellence',
        'Participation',
        'Custom',
        name='certificate_types'
    ), nullable=False)
    
    # Template design
    background_image_url = db.Column(db.String(500))
    background_color = db.Column(db.String(20), default='#FFFFFF')
    text_color = db.Column(db.String(20), default='#000000')
    accent_color = db.Column(db.String(20), default='#FFD700')
    
    # Template layout
    layout_style = db.Column(db.Enum(
        'Traditional',
        'Modern',
        'Minimal',
        'Creative',
        name='layout_styles'
    ), nullable=False, default='Traditional')
    
    # Template content
    header_text = db.Column(db.String(500), default='Certificate of Completion')
    body_template = db.Column(db.Text, nullable=False)
    footer_text = db.Column(db.String(500), default='This certifies that the above named has successfully completed')
    
    # Template fields
    fields_config = db.Column(db.Text)  # JSON object defining field positions and styles
    
    # Template settings
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    # Template dimensions
    width = db.Column(db.Integer, default=800)  # Width in pixels
    height = db.Column(db.Integer, default=600)  # Height in pixels
    
    # Template fonts
    font_family = db.Column(db.String(100), default='Arial')
    font_size = db.Column(db.Integer, default=16)
    
    # Template preview
    preview_image_url = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CertificateTemplate {self.id}: {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_type': self.template_type,
            'background_image_url': self.background_image_url,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'accent_color': self.accent_color,
            'layout_style': self.layout_style,
            'header_text': self.header_text,
            'body_template': self.body_template,
            'footer_text': self.footer_text,
            'fields_config': self.fields_config,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'width': self.width,
            'height': self.height,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'preview_image_url': self.preview_image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CertificateSharing(db.Model):
    """
    Certificate sharing model for social media and public profiles
    """
    __tablename__ = 'certificate_sharing'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Certificate details
    certificate_id = db.Column(db.Integer, db.ForeignKey('certificates.id'), nullable=False, index=True)
    
    # Sharing details
    sharing_type = db.Column(db.Enum(
        'Public Link',
        'LinkedIn',
        'Facebook',
        'Twitter',
        'Email',
        'WhatsApp',
        name='sharing_types'
    ), nullable=False)
    
    # Sharing settings
    is_public = db.Column(db.Boolean, default=False)
    share_url = db.Column(db.String(500))  # Unique sharing URL
    share_token = db.Column(db.String(100))  # Token for private sharing
    
    # Access control
    password_protected = db.Column(db.Boolean, default=False)
    access_password = db.Column(db.String(255))
    expires_at = db.Column(db.DateTime)
    
    # Sharing metadata
    shared_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    shared_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Tracking
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    last_viewed_at = db.Column(db.DateTime)
    
    # Social media specific
    social_media_post_id = db.Column(db.String(200))  # ID of the social media post
    social_media_response = db.Column(db.Text)  # Response from social media API
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shared_by_user = db.relationship('User', backref='shared_certificates')
    
    def __init__(self, **kwargs):
        super(CertificateSharing, self).__init__(**kwargs)
        if not self.share_token:
            self.share_token = self.generate_share_token()
        if not self.share_url and self.share_token:
            self.share_url = f"/share/certificate/{self.share_token}"
    
    def __repr__(self):
        return f'<CertificateSharing {self.id}: {self.sharing_type}>'
    
    def generate_share_token(self):
        """Generate unique sharing token"""
        return str(uuid.uuid4())[:16].lower()
    
    def is_accessible(self):
        """Check if sharing link is accessible"""
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def increment_view_count(self):
        """Increment view count and update last viewed time"""
        self.view_count += 1
        self.last_viewed_at = datetime.utcnow()
    
    def increment_download_count(self):
        """Increment download count"""
        self.download_count += 1
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'certificate_id': self.certificate_id,
            'sharing_type': self.sharing_type,
            'is_public': self.is_public,
            'share_url': self.share_url,
            'share_token': self.share_token,
            'password_protected': self.password_protected,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'shared_by': self.shared_by,
            'shared_at': self.shared_at.isoformat() if self.shared_at else None,
            'view_count': self.view_count,
            'download_count': self.download_count,
            'last_viewed_at': self.last_viewed_at.isoformat() if self.last_viewed_at else None,
            'social_media_post_id': self.social_media_post_id,
            'social_media_response': self.social_media_response,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_accessible': self.is_accessible()
        }