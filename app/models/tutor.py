from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models.user import User

class TutorProfile(db.Model):
    """
    Enhanced tutor-specific profile information for marketplace
    """
    __tablename__ = 'tutor_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Basic Information
    title = db.Column(db.String(100))
    tagline = db.Column(db.String(200))  # Professional tagline
    description = db.Column(db.Text)
    bio = db.Column(db.Text)  # Detailed biography
    
    # Location & Availability
    country = db.Column(db.String(50))
    state = db.Column(db.String(50))
    city = db.Column(db.String(50))
    timezone = db.Column(db.String(50), default='UTC')
    willing_to_relocate = db.Column(db.Boolean, default=False)
    travel_radius_km = db.Column(db.Integer)  # Willing to travel this many km
    
    # Teaching Preferences
    teaching_modes = db.Column(db.Text)  # JSON: ['online', 'offline', 'hybrid']
    languages_spoken = db.Column(db.Text)  # JSON array of languages
    age_groups_taught = db.Column(db.Text)  # JSON: ['elementary', 'middle', 'high', 'adult']
    max_group_size = db.Column(db.Integer, default=1)  # Maximum students per session
    
    # Pricing
    hourly_rate = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(10), default='USD')
    price_per_group_session = db.Column(db.Numeric(10, 2))
    monthly_package_price = db.Column(db.Numeric(10, 2))
    offers_free_trial = db.Column(db.Boolean, default=False)
    trial_duration_minutes = db.Column(db.Integer, default=30)
    
    # Media
    profile_image_url = db.Column(db.String(255))
    banner_image_url = db.Column(db.String(255))
    video_intro_url = db.Column(db.String(255))
    gallery_images = db.Column(db.Text)  # JSON array of image URLs
    
    # Verification & Trust
    is_verified = db.Column(db.Boolean, default=False)
    verification_level = db.Column(db.Enum('Basic', 'Standard', 'Premium', name='verification_levels'), default='Basic')
    verification_badge_url = db.Column(db.String(255))
    background_check_status = db.Column(db.Enum('Not Started', 'Pending', 'Approved', 'Rejected', name='background_check_status'), default='Not Started')
    background_check_expiry = db.Column(db.DateTime)
    
    # Statistics
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    total_students = db.Column(db.Integer, default=0)
    total_hours_taught = db.Column(db.Float, default=0.0)
    completion_rate = db.Column(db.Float, default=0.0)  # Percentage of completed sessions
    response_time_hours = db.Column(db.Float, default=24.0)  # Average response time
    
    # Availability
    available_days = db.Column(db.Text)  # JSON: ['monday', 'tuesday', ...]
    available_hours_start = db.Column(db.Time)  # Start of daily availability
    available_hours_end = db.Column(db.Time)  # End of daily availability
    notice_required_hours = db.Column(db.Integer, default=24)  # Hours notice required for booking
    
    # SEO & Marketing
    slug = db.Column(db.String(100), unique=True, index=True)
    meta_title = db.Column(db.String(100))
    meta_description = db.Column(db.String(255))
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('tutor_profile', uselist=False))
    subjects = db.relationship('TutorSubject', backref='tutor_profile_subjects', lazy='dynamic', cascade='all, delete-orphan')
    certifications = db.relationship('TutorCertification', backref='tutor_profile_certs', lazy='dynamic', cascade='all, delete-orphan')
    availability_slots = db.relationship('TutorAvailability', backref='tutor_profile_availability', lazy='dynamic', cascade='all, delete-orphan')
    verification_documents = db.relationship('VerificationDocument', backref='tutor_profile_docs', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TutorProfile {self.user.email}>'
    
    @property
    def full_name(self):
        """Get tutor's full name from user profile"""
        if self.user.user_profile:
            return self.user.user_profile.full_name
        return self.user.email.split('@')[0]
    
    @property
    def average_rating(self):
        """Get average rating with decimal precision"""
        return round(self.rating, 1) if self.rating else 0.0
    
    def get_subjects_list(self):
        """Get list of subjects taught by this tutor"""
        return [ts.subject.name for ts in self.subjects.filter_by(is_active=True).all()]
    
    def get_languages_list(self):
        """Get list of languages spoken by tutor"""
        import json
        try:
            return json.loads(self.languages_spoken) if self.languages_spoken else []
        except:
            return []
    
    def get_teaching_modes_list(self):
        """Get list of teaching modes"""
        import json
        try:
            return json.loads(self.teaching_modes) if self.teaching_modes else ['online']
        except:
            return ['online']
    
    def get_age_groups_list(self):
        """Get list of age groups taught"""
        import json
        try:
            return json.loads(self.age_groups_taught) if self.age_groups_taught else []
        except:
            return []
    
    def is_available_now(self):
        """Check if tutor is currently available"""
        from datetime import datetime, time
        import pytz
        
        if not self.is_active:
            return False
            
        # Get tutor's timezone
        tz = pytz.timezone(self.timezone if self.timezone else 'UTC')
        now = datetime.now(tz)
        
        # Check if today is an available day
        available_days = self.get_available_days()
        if now.strftime('%A').lower() not in available_days:
            return False
            
        # Check if current time is within available hours
        current_time = now.time()
        if self.available_hours_start and self.available_hours_end:
            return self.available_hours_start <= current_time <= self.available_hours_end
            
        return True
    
    def get_available_days(self):
        """Get list of available days"""
        import json
        try:
            return json.loads(self.available_days) if self.available_days else []
        except:
            return []
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'tagline': self.tagline,
            'description': self.description,
            'bio': self.bio,
            'country': self.country,
            'state': self.state,
            'city': self.city,
            'timezone': self.timezone,
            'willing_to_relocate': self.willing_to_relocate,
            'travel_radius_km': self.travel_radius_km,
            'teaching_modes': self.get_teaching_modes_list(),
            'languages_spoken': self.get_languages_list(),
            'age_groups_taught': self.get_age_groups_list(),
            'max_group_size': self.max_group_size,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate else None,
            'currency': self.currency,
            'price_per_group_session': float(self.price_per_group_session) if self.price_per_group_session else None,
            'monthly_package_price': float(self.monthly_package_price) if self.monthly_package_price else None,
            'offers_free_trial': self.offers_free_trial,
            'trial_duration_minutes': self.trial_duration_minutes,
            'profile_image_url': self.profile_image_url,
            'banner_image_url': self.banner_image_url,
            'video_intro_url': self.video_intro_url,
            'is_verified': self.is_verified,
            'verification_level': self.verification_level,
            'verification_badge_url': self.verification_badge_url,
            'background_check_status': self.background_check_status,
            'rating': self.average_rating,
            'total_reviews': self.total_reviews,
            'total_students': self.total_students,
            'total_hours_taught': self.total_hours_taught,
            'completion_rate': self.completion_rate,
            'response_time_hours': self.response_time_hours,
            'available_days': self.get_available_days(),
            'available_hours_start': self.available_hours_start.strftime('%H:%M') if self.available_hours_start else None,
            'available_hours_end': self.available_hours_end.strftime('%H:%M') if self.available_hours_end else None,
            'notice_required_hours': self.notice_required_hours,
            'slug': self.slug,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'is_featured': self.is_featured,
            'is_active': self.is_active,
            'full_name': self.full_name,
            'subjects': self.get_subjects_list(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_active_at': self.last_active_at.isoformat() if self.last_active_at else None
        }
        
        if include_sensitive:
            import json
            data['gallery_images'] = json.loads(self.gallery_images) if self.gallery_images else []
            
        return data


class TutorSubject(db.Model):
    """
    Subjects taught by tutors with specific details
    """
    __tablename__ = 'tutor_subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)
    
    # Subject-specific details
    proficiency_level = db.Column(db.Enum('Beginner', 'Intermediate', 'Advanced', 'Expert', name='tutor_proficiency_levels'), default='Intermediate')
    hourly_rate = db.Column(db.Numeric(10, 2))  # Subject-specific rate override
    experience_years = db.Column(db.Integer, default=0)
    teaching_experience_years = db.Column(db.Integer, default=0)
    
    # Preferences
    preferred_age_groups = db.Column(db.Text)  # JSON array
    preferred_teaching_modes = db.Column(db.Text)  # JSON array
    max_group_size = db.Column(db.Integer)  # Subject-specific group size limit
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_featured = db.Column(db.Boolean, default=False)  # Featured subject for this tutor
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subject = db.relationship('Subject', backref='tutor_subjects_list')
    
    def __repr__(self):
        return f'<TutorSubject {self.tutor_profile_id}-{self.subject_id}>'
    
    def get_preferred_age_groups_list(self):
        """Get list of preferred age groups"""
        import json
        try:
            return json.loads(self.preferred_age_groups) if self.preferred_age_groups else []
        except:
            return []
    
    def get_preferred_teaching_modes_list(self):
        """Get list of preferred teaching modes"""
        import json
        try:
            return json.loads(self.preferred_teaching_modes) if self.preferred_teaching_modes else []
        except:
            return []
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'tutor_profile_id': self.tutor_profile_id,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'category_name': self.subject.category.name if self.subject and self.subject.category else None,
            'proficiency_level': self.proficiency_level,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate else None,
            'experience_years': self.experience_years,
            'teaching_experience_years': self.teaching_experience_years,
            'preferred_age_groups': self.get_preferred_age_groups_list(),
            'preferred_teaching_modes': self.get_preferred_teaching_modes_list(),
            'max_group_size': self.max_group_size,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TutorCertification(db.Model):
    """
    Tutor certifications and qualifications
    """
    __tablename__ = 'tutor_certifications'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False, index=True)
    
    # Certification details
    name = db.Column(db.String(200), nullable=False)
    issuing_organization = db.Column(db.String(200), nullable=False)
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    credential_id = db.Column(db.String(100))
    credential_url = db.Column(db.String(255))
    
    # Verification
    verification_status = db.Column(db.Enum('Not Submitted', 'Pending', 'Verified', 'Rejected', name='certification_verification_status'), default='Not Submitted')
    verification_notes = db.Column(db.Text)
    verification_date = db.Column(db.DateTime)
    
    # Media
    certificate_image_url = db.Column(db.String(255))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TutorCertification {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'tutor_profile_id': self.tutor_profile_id,
            'name': self.name,
            'issuing_organization': self.issuing_organization,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'credential_id': self.credential_id,
            'credential_url': self.credential_url,
            'verification_status': self.verification_status,
            'verification_notes': self.verification_notes,
            'verification_date': self.verification_date.isoformat() if self.verification_date else None,
            'certificate_image_url': self.certificate_image_url,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TutorAvailability(db.Model):
    """
    Tutor availability time slots
    """
    __tablename__ = 'tutor_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False, index=True)
    
    # Time slot details
    day_of_week = db.Column(db.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', name='availability_days'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Recurrence
    is_recurring = db.Column(db.Boolean, default=True)
    specific_date = db.Column(db.Date)  # For non-recurring slots
    
    # Status
    is_available = db.Column(db.Boolean, default=True)
    is_booked = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TutorAvailability {self.day_of_week} {self.start_time}-{self.end_time}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'tutor_profile_id': self.tutor_profile_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'is_recurring': self.is_recurring,
            'specific_date': self.specific_date.isoformat() if self.specific_date else None,
            'is_available': self.is_available,
            'is_booked': self.is_booked,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }