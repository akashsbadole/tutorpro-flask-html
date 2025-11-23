from datetime import datetime, timedelta
from app import db

class Booking(db.Model):
    """
    Enhanced booking model for marketplace
    """
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Participants
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)
    
    # Booking details
    booking_type = db.Column(db.Enum(
        'One-on-One', 
        'Group Session', 
        'Workshop', 
        'Trial Session', 
        'Consultation',
        name='booking_types'
    ), nullable=False, default='One-on-One')
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    learning_objectives = db.Column(db.Text)  # JSON array
    
    # Schedule
    scheduled_start_time = db.Column(db.DateTime, nullable=False, index=True)
    scheduled_end_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    timezone = db.Column(db.String(50), default='UTC')
    
    # Recurrence (for recurring bookings)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.Text)  # JSON: frequency, days, end_date, etc.
    recurring_booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))  # Parent booking for series
    
    # Location/Mode
    session_mode = db.Column(db.Enum(
        'Online', 
        'Offline', 
        'Hybrid', 
        name='session_modes'
    ), nullable=False, default='Online')
    
    online_meeting_url = db.Column(db.String(500))
    online_meeting_id = db.Column(db.String(100))
    online_meeting_password = db.Column(db.String(50))
    
    offline_location = db.Column(db.String(500))  # Physical address
    offline_location_lat = db.Column(db.Float)  # Latitude
    offline_location_lng = db.Column(db.Float)  # Longitude
    
    # Pricing
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    coupon_code = db.Column(db.String(50))
    final_price = db.Column(db.Numeric(10, 2), nullable=False)
    price_per_student = db.Column(db.Numeric(10, 2))  # For group sessions
    
    # Group session details
    max_participants = db.Column(db.Integer, default=1)
    current_participants = db.Column(db.Integer, default=1)
    min_participants = db.Column(db.Integer, default=1)
    
    # Status
    status = db.Column(db.Enum(
        'Requested', 
        'Confirmed', 
        'In Progress', 
        'Completed', 
        'Cancelled', 
        'No Show', 
        'Rescheduled',
        name='booking_statuses'
    ), nullable=False, default='Requested', index=True)
    
    cancellation_reason = db.Column(db.Text)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    cancellation_date = db.Column(db.DateTime)
    
    # Rescheduling
    reschedule_count = db.Column(db.Integer, default=0)
    original_start_time = db.Column(db.DateTime)
    rescheduled_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reschedule_reason = db.Column(db.Text)
    
    # Student preparation
    student_requirements = db.Column(db.Text)  # JSON array of materials needed
    pre_session_materials = db.Column(db.Text)  # URLs to materials
    
    # Session outcomes
    session_notes = db.Column(db.Text)  # Tutor's notes after session
    homework_assigned = db.Column(db.Text)  # JSON array
    next_session_suggested = db.Column(db.Boolean, default=False)
    
    # Feedback
    student_attended = db.Column(db.Boolean, default=False)  # Whether student actually attended
    tutor_attended = db.Column(db.Boolean, default=False)  # Whether tutor actually attended
    attendance_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='student_bookings')
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='tutor_bookings')
    tutor_profile = db.relationship('TutorProfile', backref='bookings')
    subject = db.relationship('Subject', backref='bookings')
    canceller = db.relationship('User', foreign_keys=[cancelled_by])
    rescheduler = db.relationship('User', foreign_keys=[rescheduled_by])
    recurring_sessions = db.relationship('Booking', remote_side=[id], backref='parent_booking')
    sessions = db.relationship('BookingSession', backref='booking', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='booking_payments', lazy='dynamic')
    
    def __repr__(self):
        return f'<Booking {self.id}: {self.student_id}->{self.tutor_id} ({self.status})>'
    
    def get_learning_objectives_list(self):
        """Get learning objectives as list"""
        import json
        try:
            return json.loads(self.learning_objectives) if self.learning_objectives else []
        except:
            return []
    
    def get_student_requirements_list(self):
        """Get student requirements as list"""
        import json
        try:
            return json.loads(self.student_requirements) if self.student_requirements else []
        except:
            return []
    
    def get_homework_assigned_list(self):
        """Get homework assigned as list"""
        import json
        try:
            return json.loads(self.homework_assigned) if self.homework_assigned else []
        except:
            return []
    
    def get_recurrence_pattern_dict(self):
        """Get recurrence pattern as dictionary"""
        import json
        try:
            return json.loads(self.recurrence_pattern) if self.recurrence_pattern else {}
        except:
            return {}
    
    def is_upcoming(self):
        """Check if booking is upcoming"""
        return self.status in ['Requested', 'Confirmed'] and self.scheduled_start_time > datetime.utcnow()
    
    def is_past(self):
        """Check if booking is in the past"""
        return self.scheduled_end_time < datetime.utcnow()
    
    def is_ongoing(self):
        """Check if booking is currently in progress"""
        now = datetime.utcnow()
        return self.status == 'In Progress' or (
            self.status == 'Confirmed' and 
            self.scheduled_start_time <= now <= self.scheduled_end_time
        )
    
    def can_be_cancelled(self, user_id):
        """Check if booking can be cancelled by user"""
        if self.status in ['Completed', 'Cancelled']:
            return False
        
        # Check cancellation policy based on notice period
        hours_until_start = (self.scheduled_start_time - datetime.utcnow()).total_seconds() / 3600
        notice_required = 24  # Default 24 hours notice
        
        if self.tutor_profile:
            notice_required = self.tutor_profile.notice_required_hours or 24
        
        return hours_until_start >= notice_required
    
    def get_refund_eligibility(self):
        """Calculate refund eligibility based on cancellation timing"""
        if self.status != 'Cancelled':
            return 0
        
        hours_until_start = (self.scheduled_start_time - self.cancellation_date).total_seconds() / 3600
        
        if hours_until_start >= 48:
            return 100  # Full refund
        elif hours_until_start >= 24:
            return 50   # 50% refund
        elif hours_until_start >= 12:
            return 25   # 25% refund
        else:
            return 0    # No refund
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'tutor_id': self.tutor_id,
            'tutor_profile_id': self.tutor_profile_id,
            'subject_id': self.subject_id,
            'booking_type': self.booking_type,
            'title': self.title,
            'description': self.description,
            'learning_objectives': self.get_learning_objectives_list(),
            'scheduled_start_time': self.scheduled_start_time.isoformat(),
            'scheduled_end_time': self.scheduled_end_time.isoformat(),
            'duration_minutes': self.duration_minutes,
            'timezone': self.timezone,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.get_recurrence_pattern_dict(),
            'recurring_booking_id': self.recurring_booking_id,
            'session_mode': self.session_mode,
            'offline_location': self.offline_location if include_sensitive else None,
            'offline_location_lat': self.offline_location_lat if include_sensitive else None,
            'offline_location_lng': self.offline_location_lng if include_sensitive else None,
            'base_price': float(self.base_price),
            'currency': self.currency,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'coupon_code': self.coupon_code,
            'final_price': float(self.final_price),
            'price_per_student': float(self.price_per_student) if self.price_per_student else None,
            'max_participants': self.max_participants,
            'current_participants': self.current_participants,
            'min_participants': self.min_participants,
            'status': self.status,
            'cancellation_reason': self.cancellation_reason,
            'cancelled_by': self.cancelled_by,
            'cancellation_date': self.cancellation_date.isoformat() if self.cancellation_date else None,
            'reschedule_count': self.reschedule_count,
            'original_start_time': self.original_start_time.isoformat() if self.original_start_time else None,
            'rescheduled_by': self.rescheduled_by,
            'reschedule_reason': self.reschedule_reason,
            'student_requirements': self.get_student_requirements_list(),
            'pre_session_materials': self.pre_session_materials,
            'session_notes': self.session_notes,
            'homework_assigned': self.get_homework_assigned_list(),
            'next_session_suggested': self.next_session_suggested,
            'student_attended': self.student_attended,
            'tutor_attended': self.tutor_attended,
            'attendance_notes': self.attendance_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_upcoming': self.is_upcoming(),
            'is_past': self.is_past(),
            'is_ongoing': self.is_ongoing(),
            'refund_eligibility': self.get_refund_eligibility()
        }
        
        if include_sensitive:
            data['online_meeting_url'] = self.online_meeting_url
            data['online_meeting_id'] = self.online_meeting_id
            data['online_meeting_password'] = self.online_meeting_password
            
        return data


class BookingSession(db.Model):
    """
    Individual sessions within a booking (for recurring bookings)
    """
    __tablename__ = 'booking_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, index=True)
    
    # Session details
    session_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    session_start_time = db.Column(db.DateTime, nullable=False)
    session_end_time = db.Column(db.DateTime, nullable=False)
    
    # Session-specific data
    session_title = db.Column(db.String(200))
    session_description = db.Column(db.Text)
    session_materials = db.Column(db.Text)  # JSON array of URLs
    
    # Status
    status = db.Column(db.Enum(
        'Scheduled', 
        'In Progress', 
        'Completed', 
        'Cancelled', 
        'No Show',
        name='session_statuses'
    ), nullable=False, default='Scheduled')
    
    # Attendance
    student_attended = db.Column(db.Boolean, default=False)
    tutor_attended = db.Column(db.Boolean, default=False)
    attendance_notes = db.Column(db.Text)
    
    # Session outcomes
    session_notes = db.Column(db.Text)  # Tutor's notes
    homework_assigned = db.Column(db.Text)  # JSON array
    topics_covered = db.Column(db.Text)  # JSON array
    
    # Recording
    recording_url = db.Column(db.String(500))
    recording_duration = db.Column(db.Integer)  # Duration in minutes
    recording_size = db.Column(db.Integer)  # Size in bytes
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<BookingSession {self.id}: Booking {self.booking_id} Session {self.session_number}>'
    
    def get_session_materials_list(self):
        """Get session materials as list"""
        import json
        try:
            return json.loads(self.session_materials) if self.session_materials else []
        except:
            return []
    
    def get_homework_assigned_list(self):
        """Get homework assigned as list"""
        import json
        try:
            return json.loads(self.homework_assigned) if self.homework_assigned else []
        except:
            return []
    
    def get_topics_covered_list(self):
        """Get topics covered as list"""
        import json
        try:
            return json.loads(self.topics_covered) if self.topics_covered else []
        except:
            return []
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'session_number': self.session_number,
            'session_start_time': self.session_start_time.isoformat(),
            'session_end_time': self.session_end_time.isoformat(),
            'session_title': self.session_title,
            'session_description': self.session_description,
            'session_materials': self.get_session_materials_list(),
            'status': self.status,
            'student_attended': self.student_attended,
            'tutor_attended': self.tutor_attended,
            'attendance_notes': self.attendance_notes,
            'session_notes': self.session_notes,
            'homework_assigned': self.get_homework_assigned_list(),
            'topics_covered': self.get_topics_covered_list(),
            'recording_url': self.recording_url,
            'recording_duration': self.recording_duration,
            'recording_size': self.recording_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class GroupSession(db.Model):
    """
    Group session management for multiple students
    """
    __tablename__ = 'group_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, index=True)
    
    # Student information
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    enrollment_status = db.Column(db.Enum(
        'Enrolled', 
        'Waitlisted', 
        'Cancelled', 
        'Completed',
        name='enrollment_statuses'
    ), nullable=False, default='Enrolled')
    
    # Enrollment details
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.Text)
    
    # Payment for this student's participation
    individual_price = db.Column(db.Numeric(10, 2))
    payment_status = db.Column(db.Enum(
        'Pending', 
        'Paid', 
        'Refunded', 
        'Partial Refund',
        name='payment_statuses'
    ), default='Pending')
    
    # Participation tracking
    sessions_attended = db.Column(db.Integer, default=0)
    total_sessions = db.Column(db.Integer, default=0)
    last_attended_session = db.Column(db.DateTime)
    
    # Notes
    student_notes = db.Column(db.Text)  # Student's notes about the session
    tutor_notes = db.Column(db.Text)  # Tutor's notes about this student
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User', backref='group_enrollments')
    booking = db.relationship('Booking', backref='group_participants')
    
    def __repr__(self):
        return f'<GroupSession {self.id}: Student {self.student_id} in Booking {self.booking_id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'student_id': self.student_id,
            'enrollment_status': self.enrollment_status,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'cancellation_reason': self.cancellation_reason,
            'individual_price': float(self.individual_price) if self.individual_price else None,
            'payment_status': self.payment_status,
            'sessions_attended': self.sessions_attended,
            'total_sessions': self.total_sessions,
            'last_attended_session': self.last_attended_session.isoformat() if self.last_attended_session else None,
            'student_notes': self.student_notes,
            'tutor_notes': self.tutor_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AvailabilityConflict(db.Model):
    """
    Tracking of booking conflicts and resolutions
    """
    __tablename__ = 'availability_conflicts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Conflict details
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    conflicting_booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, index=True)
    existing_booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, index=True)
    
    # Conflict resolution
    resolution_status = db.Column(db.Enum(
        'Detected', 
        'Student Notified', 
        'Tutor Notified', 
        'Resolved', 
        'Escalated',
        name='conflict_resolution_statuses'
    ), nullable=False, default='Detected')
    
    resolution_action = db.Column(db.Enum(
        'New Booking Cancelled', 
        'Existing Booking Rescheduled', 
        'New Booking Rescheduled', 
        'Manual Resolution',
        name='conflict_resolution_actions'
    ))
    
    resolution_notes = db.Column(db.Text)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='availability_conflicts')
    conflicting_booking = db.relationship('Booking', foreign_keys=[conflicting_booking_id], backref='conflict_as_new')
    existing_booking = db.relationship('Booking', foreign_keys=[existing_booking_id], backref='conflict_as_existing')
    resolver = db.relationship('User', foreign_keys=[resolved_by])
    
    def __repr__(self):
        return f'<AvailabilityConflict {self.id}: Tutor {self.tutor_id} between bookings {self.conflicting_booking_id} and {self.existing_booking_id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'tutor_id': self.tutor_id,
            'conflicting_booking_id': self.conflicting_booking_id,
            'existing_booking_id': self.existing_booking_id,
            'resolution_status': self.resolution_status,
            'resolution_action': self.resolution_action,
            'resolution_notes': self.resolution_notes,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }