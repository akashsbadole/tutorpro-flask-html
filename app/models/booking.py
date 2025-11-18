from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.course import Course


class TutorAvailability(db.Model):
    """
    Model for tutor availability
    """
    __tablename__ = 'tutor_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6 (Monday-Sunday)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tutor = db.relationship('TutorProfile', backref='availabilities')
    
    # Index for faster queries
    __table_args__ = (db.Index('idx_tutor_day', 'tutor_id', 'day_of_week'),)
    
    def __repr__(self):
        return f'<TutorAvailability {self.tutor.user.email} - Day {self.day_of_week}>'


class Booking(db.Model):
    """
    Model for lesson scheduling
    """
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('Pending', 'Confirmed', 'Completed', 'Cancelled', 'No-Show', name='booking_statuses'), 
                      nullable=False, default='Pending')
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='student_bookings')
    tutor = db.relationship('TutorProfile', foreign_keys=[tutor_id], backref='tutor_bookings')
    course = db.relationship('Course', foreign_keys=[course_id])
    payments = db.relationship('Payment', backref='booking', lazy=True, cascade='all, delete-orphan')
    meeting_link = db.relationship('MeetingLink', backref='booking', uselist=False, cascade='all, delete-orphan')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_student_booking', 'student_id', 'scheduled_time'),
        db.Index('idx_tutor_booking', 'tutor_id', 'scheduled_time'),
    )
    
    def __repr__(self):
        return f'<Booking {self.student.email} with {self.tutor.user.email} on {self.scheduled_time}>'
    
    @property
    def end_time(self):
        """Calculate end time based on scheduled time and duration"""
        return self.scheduled_time + timedelta(minutes=self.duration_minutes)
    
    def is_upcoming(self):
        """Check if booking is in the future"""
        return self.scheduled_time > datetime.utcnow()
    
    def is_past(self):
        """Check if booking is in the past"""
        return self.scheduled_time <= datetime.utcnow()


class MeetingLink(db.Model):
    """
    Model for video conference links
    """
    __tablename__ = 'meeting_links'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    platform = db.Column(db.Enum('Zoom', 'Google Meet', 'Microsoft Teams', name='meeting_platforms'), 
                        nullable=False, default='Zoom')
    meeting_url = db.Column(db.String(500), nullable=False)
    meeting_id = db.Column(db.String(100))
    password = db.Column(db.String(50))
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MeetingLink {self.platform} for Booking {self.booking_id}>'
    
    @property
    def is_expired(self):
        """Check if meeting link has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class DemoRequest(db.Model):
    """
    Model for demo class scheduling
    """
    __tablename__ = 'demo_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    status = db.Column(db.Enum('Pending', 'Confirmed', 'Completed', 'Cancelled', name='demo_statuses'), 
                      nullable=False, default='Pending')
    notes = db.Column(db.Text)
    scheduled_time = db.Column(db.DateTime)  # Actual scheduled time when confirmed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='demo_requests')
    tutor = db.relationship('TutorProfile', foreign_keys=[tutor_id], backref='demo_requests')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_student_demo', 'student_id', 'preferred_date'),
        db.Index('idx_tutor_demo', 'tutor_id', 'preferred_date'),
    )
    
    def __repr__(self):
        return f'<DemoRequest {self.student.email} with {self.tutor.user.email} on {self.preferred_date}>'


class SpecialAvailability(db.Model):
    """
    Model for special/one-time availability overrides
    """
    __tablename__ = 'special_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tutor = db.relationship('TutorProfile', backref='special_availabilities')
    
    # Index for faster queries
    __table_args__ = (db.Index('idx_tutor_date', 'tutor_id', 'date'),)
    
    def __repr__(self):
        return f'<SpecialAvailability {self.tutor.user.email} - {self.date}>'


class BookingFeedback(db.Model):
    """
    Model for booking feedback
    """
    __tablename__ = 'booking_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    teaching_quality = db.Column(db.Integer, nullable=False)
    communication = db.Column(db.Integer, nullable=False)
    preparation = db.Column(db.Integer, nullable=False)
    value_for_money = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    would_recommend = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    booking = db.relationship('Booking', backref='feedback')
    
    def __repr__(self):
        return f'<BookingFeedback {self.booking_id} - {self.rating}>'


class DemoFeedback(db.Model):
    """
    Model for demo feedback
    """
    __tablename__ = 'demo_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    demo_request_id = db.Column(db.Integer, db.ForeignKey('demo_requests.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    teaching_quality = db.Column(db.Integer, nullable=False)
    communication = db.Column(db.Integer, nullable=False)
    preparation = db.Column(db.Integer, nullable=False)
    value_for_money = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    would_recommend = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    demo_request = db.relationship('DemoRequest', backref='feedback')
    
    def __repr__(self):
        return f'<DemoFeedback {self.demo_request_id} - {self.rating}>'