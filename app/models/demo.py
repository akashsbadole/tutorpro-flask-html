"""
Demo Classes Models for TutorPro Marketplace
Free demo session booking and management system
"""

from datetime import datetime, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum as PyEnum
import json

from app import db

class DemoSessionStatus(PyEnum):
    """Demo session status"""
    REQUESTED = "Requested"
    ACCEPTED = "Accepted"
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No Show"
    RESCHEDULED = "Rescheduled"

class DemoSessionType(PyEnum):
    """Types of demo sessions"""
    ONE_ON_ONE = "One-on-One"
    GROUP = "Group"
    RECORDED = "Recorded"
    INTERACTIVE = "Interactive"

class DemoSession(db.Model):
    """Demo session booking model"""
    __tablename__ = 'demo_sessions'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    tutor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    
    # Session Details
    session_title = Column(String(200), nullable=False)
    session_description = Column(Text)
    session_type = Column(Enum(DemoSessionType), default=DemoSessionType.ONE_ON_ONE)
    duration_minutes = Column(Integer, default=30)  # Free demo duration
    max_participants = Column(Integer, default=1)  # For group demos
    
    # Scheduling
    requested_date_time = Column(DateTime, nullable=False)
    scheduled_date_time = Column(DateTime)
    timezone = Column(String(50), default='UTC')
    location_type = Column(String(20), default='online')  # online, offline, hybrid
    meeting_link = Column(String(500))
    meeting_password = Column(String(100))
    physical_address = Column(Text)
    
    # Status and Tracking
    status = Column(Enum(DemoSessionStatus), default=DemoSessionStatus.REQUESTED)
    cancellation_reason = Column(Text)
    cancellation_initiated_by = Column(String(10))  # student, tutor, system
    rescheduled_from = Column(Integer, ForeignKey('demo_sessions.id'))  # Reference to original session
    
    # Demo Content
    topics_to_cover = Column(JSON)  # List of topics for demo
    learning_objectives = Column(Text)
    materials_needed = Column(JSON)  # Materials student should prepare
    tutor_preparation_notes = Column(Text)
    
    # Follow-up and Conversion
    conversion_potential = Column(String(10), default='unknown')  # high, medium, low, unknown
    student_feedback = Column(Text)
    tutor_feedback = Column(Text)
    follow_up_actions = Column(JSON)  # Actions to take after demo
    booking_conversion_id = Column(Integer, ForeignKey('bookings.id'))  # If demo leads to paid booking
    
    # Communication
    reminder_sent = Column(Boolean, default=False)
    reminder_count = Column(Integer, default=0)
    last_communication = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime)  # When demo offer expires
    
    # Relationships
    student = relationship('User', foreign_keys=[student_id])
    tutor = relationship('User', foreign_keys=[tutor_id])
    subject = relationship('Subject')
    rescheduled_session = relationship('DemoSession', remote_side=[id])
    booking_conversion = relationship('Booking', foreign_keys=[booking_conversion_id])
    
    def __repr__(self):
        return f'<DemoSession {self.id}:{self.session_title}>'
    
    def to_dict(self, include_sensitive=False):
        """Convert demo session to dictionary"""
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'tutor_id': self.tutor_id,
            'subject_id': self.subject_id,
            'session_title': self.session_title,
            'session_description': self.session_description,
            'session_type': self.session_type.value if self.session_type else None,
            'duration_minutes': self.duration_minutes,
            'max_participants': self.max_participants,
            'requested_date_time': self.requested_date_time.isoformat() if self.requested_date_time else None,
            'scheduled_date_time': self.scheduled_date_time.isoformat() if self.scheduled_date_time else None,
            'timezone': self.timezone,
            'location_type': self.location_type,
            'meeting_link': self.meeting_link if include_sensitive else None,
            'meeting_password': self.meeting_password if include_sensitive else None,
            'physical_address': self.physical_address,
            'status': self.status.value if self.status else None,
            'cancellation_reason': self.cancellation_reason,
            'cancellation_initiated_by': self.cancellation_initiated_by,
            'rescheduled_from': self.rescheduled_from,
            'topics_to_cover': self.topics_to_cover or [],
            'learning_objectives': self.learning_objectives,
            'materials_needed': self.materials_needed or [],
            'tutor_preparation_notes': self.tutor_preparation_notes,
            'conversion_potential': self.conversion_potential,
            'student_feedback': self.student_feedback,
            'tutor_feedback': self.tutor_feedback,
            'follow_up_actions': self.follow_up_actions or [],
            'booking_conversion_id': self.booking_conversion_id,
            'reminder_sent': self.reminder_sent,
            'reminder_count': self.reminder_count,
            'last_communication': self.last_communication.isoformat() if self.last_communication else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'student': self.student.to_dict() if self.student else None,
            'tutor': self.tutor.to_dict() if self.tutor else None,
            'subject': self.subject.to_dict() if self.subject else None
        }
        
        return data
    
    @hybrid_property
    def is_upcoming(self):
        """Check if demo session is upcoming"""
        if not self.scheduled_date_time:
            return False
        return self.scheduled_date_time > datetime.now(timezone.utc)
    
    @hybrid_property
    def is_past(self):
        """Check if demo session is in the past"""
        if not self.scheduled_date_time:
            return False
        return self.scheduled_date_time < datetime.now(timezone.utc)
    
    @hybrid_property
    def is_today(self):
        """Check if demo session is today"""
        if not self.scheduled_date_time:
            return False
        today = datetime.now(timezone.utc).date()
        return self.scheduled_date_time.date() == today
    
    def can_be_rescheduled(self):
        """Check if demo can be rescheduled"""
        return (self.status in [DemoSessionStatus.REQUESTED, DemoSessionStatus.ACCEPTED, DemoSessionStatus.SCHEDULED] 
                and self.is_upcoming)
    
    def can_be_cancelled(self):
        """Check if demo can be cancelled"""
        return (self.status not in [DemoSessionStatus.COMPLETED, DemoSessionStatus.CANCELLED, DemoSessionStatus.NO_SHOW]
                and self.is_upcoming)
    
    def get_time_until_session(self):
        """Get time until session starts"""
        if not self.scheduled_date_time:
            return None
        return self.scheduled_date_time - datetime.now(timezone.utc)
    
    def update_status(self, new_status, reason=None, initiated_by=None):
        """Update demo session status with tracking"""
        old_status = self.status
        self.status = new_status
        
        if reason:
            self.cancellation_reason = reason
        
        if initiated_by:
            self.cancellation_initiated_by = initiated_by
        
        self.updated_at = datetime.now(timezone.utc)
        
        # Log status change if needed
        # This could trigger notifications, analytics, etc.
        
        return old_status, new_status

class DemoAvailability(db.Model):
    """Tutor demo availability slots"""
    __tablename__ = 'demo_availability'
    
    id = Column(Integer, primary_key=True)
    tutor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Availability Details
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Monday-Sunday)
    start_time = Column(String(10), nullable=False)  # HH:MM format
    end_time = Column(String(10), nullable=False)  # HH:MM format
    timezone = Column(String(50), default='UTC')
    
    # Demo Settings
    max_demo_sessions_per_day = Column(Integer, default=3)
    demo_duration_minutes = Column(Integer, default=30)
    buffer_between_sessions = Column(Integer, default=15)  # Minutes between demos
    
    # Subject Restrictions
    allowed_subject_ids = Column(JSON)  # Subjects tutor offers demos for
    excluded_subject_ids = Column(JSON)  # Subjects tutor doesn't offer demos for
    
    # Availability Constraints
    min_hours_notice = Column(Integer, default=24)  # Minimum hours notice required
    max_days_ahead = Column(Integer, default=14)  # Maximum days in advance
    blackout_dates = Column(JSON)  # Dates when demos are not available
    
    # Status
    is_active = Column(Boolean, default=True)
    seasonal_availability = Column(JSON)  # Seasonal availability patterns
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    tutor = relationship('User')
    
    def __repr__(self):
        return f'<DemoAvailability {self.tutor_id}:{self.day_of_week}>'
    
    def to_dict(self):
        """Convert demo availability to dictionary"""
        return {
            'id': self.id,
            'tutor_id': self.tutor_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'timezone': self.timezone,
            'max_demo_sessions_per_day': self.max_demo_sessions_per_day,
            'demo_duration_minutes': self.demo_duration_minutes,
            'buffer_between_sessions': self.buffer_between_sessions,
            'allowed_subject_ids': self.allowed_subject_ids or [],
            'excluded_subject_ids': self.excluded_subject_ids or [],
            'min_hours_notice': self.min_hours_notice,
            'max_days_ahead': self.max_days_ahead,
            'blackout_dates': self.blackout_dates or [],
            'is_active': self.is_active,
            'seasonal_availability': self.seasonal_availability or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_available_slots(self, date):
        """Get available demo slots for a specific date"""
        available_slots = []
        
        # Check if date is valid for this availability
        if not self._is_date_available(date):
            return available_slots
        
        # Parse start and end times
        start_hour, start_minute = map(int, self.start_time.split(':'))
        end_hour, end_minute = map(int, self.end_time.split(':'))
        
        # Create datetime objects for the date
        slot_start = datetime(date.year, date.month, date.day, start_hour, start_minute)
        slot_end = datetime(date.year, date.month, date.day, end_hour, end_minute)
        
        # Generate slots based on demo duration and buffer
        current_time = slot_start
        slot_count = 0
        
        while current_time + timedelta(minutes=self.demo_duration_minutes) <= slot_end:
            if slot_count >= self.max_demo_sessions_per_day:
                break
            
            slot_end_time = current_time + timedelta(minutes=self.demo_duration_minutes)
            
            available_slots.append({
                'start_time': current_time.isoformat(),
                'end_time': slot_end_time.isoformat(),
                'duration_minutes': self.demo_duration_minutes,
                'available': True
            })
            
            # Move to next slot with buffer
            current_time = slot_end_time + timedelta(minutes=self.buffer_between_sessions)
            slot_count += 1
        
        return available_slots
    
    def _is_date_available(self, date):
        """Check if a specific date is available for demos"""
        # Check day of week
        if date.weekday() != self.day_of_week:
            return False
        
        # Check minimum notice
        notice_hours = (date - datetime.now(timezone.utc).date()).days * 24
        if notice_hours < self.min_hours_notice:
            return False
        
        # Check maximum advance booking
        max_days = (date - datetime.now(timezone.utc).date()).days
        if max_days > self.max_days_ahead:
            return False
        
        # Check blackout dates
        if self.blackout_dates:
            date_str = date.isoformat()
            if date_str in self.blackout_dates:
                return False
        
        return True

class DemoTemplate(db.Model):
    """Predefined demo session templates"""
    __tablename__ = 'demo_templates'
    
    id = Column(Integer, primary_key=True)
    tutor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    
    # Template Details
    template_name = Column(String(200), nullable=False)
    description = Column(Text)
    target_audience = Column(String(200))
    prerequisites = Column(Text)
    
    # Session Structure
    duration_minutes = Column(Integer, default=30)
    agenda = Column(JSON)  # Structured agenda with timings
    topics_to_cover = Column(JSON)
    learning_objectives = Column(Text)
    
    # Materials and Preparation
    materials_needed = Column(JSON)
    tutor_preparation = Column(Text)
    student_preparation = Column(Text)
    
    # Interactive Elements
    interactive_elements = Column(JSON)  # Quizzes, exercises, demonstrations
    assessment_components = Column(JSON)  # How to assess student during demo
    
    # Follow-up
    post_demo_actions = Column(JSON)  # Actions to take after demo
    conversion_tips = Column(Text)  # Tips for converting demo to paid sessions
    
    # Usage Tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float)  # Conversion success rate
    average_rating = Column(Float)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)  # Can be used by other tutors
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    tutor = relationship('User')
    subject = relationship('Subject')
    
    def __repr__(self):
        return f'<DemoTemplate {self.template_name}>'
    
    def to_dict(self):
        """Convert demo template to dictionary"""
        return {
            'id': self.id,
            'tutor_id': self.tutor_id,
            'subject_id': self.subject_id,
            'template_name': self.template_name,
            'description': self.description,
            'target_audience': self.target_audience,
            'prerequisites': self.prerequisites,
            'duration_minutes': self.duration_minutes,
            'agenda': self.agenda or [],
            'topics_to_cover': self.topics_to_cover or [],
            'learning_objectives': self.learning_objectives,
            'materials_needed': self.materials_needed or [],
            'tutor_preparation': self.tutor_preparation,
            'student_preparation': self.student_preparation,
            'interactive_elements': self.interactive_elements or [],
            'assessment_components': self.assessment_components or [],
            'post_demo_actions': self.post_demo_actions or [],
            'conversion_tips': self.conversion_tips,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'average_rating': self.average_rating,
            'is_active': self.is_active,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tutor': self.tutor.to_dict() if self.tutor else None,
            'subject': self.subject.to_dict() if self.subject else None
        }
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()

class DemoFeedback(db.Model):
    """Feedback collected after demo sessions"""
    __tablename__ = 'demo_feedback'
    
    id = Column(Integer, primary_key=True)
    demo_session_id = Column(Integer, ForeignKey('demo_sessions.id'), nullable=False)
    
    # Feedback Provider
    provided_by = Column(Integer, ForeignKey('users.id'), nullable=False)  # Student or tutor
    provider_role = Column(String(10), nullable=False)  # student, tutor
    
    # Overall Rating
    overall_rating = Column(Integer)  # 1-5 scale
    would_recommend = Column(Boolean)
    would_book_paid = Column(Boolean)
    
    # Detailed Ratings
    content_quality = Column(Integer)  # 1-5 scale
    tutor_expertise = Column(Integer)  # 1-5 scale
    session_pace = Column(Integer)  # 1-5 scale
    interaction_level = Column(Integer)  # 1-5 scale
    technical_quality = Column(Integer)  # 1-5 scale (for online demos)
    
    # Qualitative Feedback
    what_went_well = Column(Text)
    what_could_improve = Column(Text)
    most_valuable_aspect = Column(Text)
    suggestions_for_future = Column(Text)
    
    # Conversion Factors
    main_decision_factors = Column(JSON)  # Factors influencing booking decision
    concerns_raised = Column(JSON)  # Concerns that might prevent booking
    price_sensitivity = Column(String(20))  # low, medium, high
    
    # Follow-up Preferences
    preferred_follow_up_method = Column(String(20))
    best_contact_time = Column(String(50))
    additional_questions = Column(Text)
    
    # Metadata
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_anonymous = Column(Boolean, default=False)
    
    # Relationships
    demo_session = relationship('DemoSession')
    feedback_provider = relationship('User')
    
    def __repr__(self):
        return f'<DemoFeedback {self.demo_session_id}:{self.provider_role}>'
    
    def to_dict(self):
        """Convert demo feedback to dictionary"""
        return {
            'id': self.id,
            'demo_session_id': self.demo_session_id,
            'provided_by': self.provided_by,
            'provider_role': self.provider_role,
            'overall_rating': self.overall_rating,
            'would_recommend': self.would_recommend,
            'would_book_paid': self.would_book_paid,
            'content_quality': self.content_quality,
            'tutor_expertise': self.tutor_expertise,
            'session_pace': self.session_pace,
            'interaction_level': self.interaction_level,
            'technical_quality': self.technical_quality,
            'what_went_well': self.what_went_well,
            'what_could_improve': self.what_could_improve,
            'most_valuable_aspect': self.most_valuable_aspect,
            'suggestions_for_future': self.suggestions_for_future,
            'main_decision_factors': self.main_decision_factors or [],
            'concerns_raised': self.concerns_raised or [],
            'price_sensitivity': self.price_sensitivity,
            'preferred_follow_up_method': self.preferred_follow_up_method,
            'best_contact_time': self.best_contact_time,
            'additional_questions': self.additional_questions,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'is_anonymous': self.is_anonymous,
            'demo_session': self.demo_session.to_dict() if self.demo_session else None,
            'feedback_provider': self.feedback_provider.to_dict() if self.feedback_provider and not self.is_anonymous else None
        }

class DemoAnalytics(db.Model):
    """Analytics for demo sessions"""
    __tablename__ = 'demo_analytics'
    
    id = Column(Integer, primary_key=True)
    tutor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Time Period
    analytics_date = Column(DateTime, nullable=False)  # Date for analytics
    period_type = Column(String(10), default='daily')  # daily, weekly, monthly
    
    # Session Metrics
    total_demos_requested = Column(Integer, default=0)
    total_demos_completed = Column(Integer, default=0)
    total_demos_cancelled = Column(Integer, default=0)
    total_demos_no_show = Column(Integer, default=0)
    
    # Conversion Metrics
    conversion_to_paid = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    average_time_to_conversion = Column(Float)  # Days from demo to paid booking
    
    # Performance Metrics
    average_rating = Column(Float)
    average_duration_minutes = Column(Float)
    student_satisfaction_score = Column(Float)
    
    # Engagement Metrics
    repeat_demo_students = Column(Integer, default=0)
    new_demo_students = Column(Integer, default=0)
    referral_demos = Column(Integer, default=0)
    
    # Revenue Impact
    estimated_revenue_from_conversions = Column(Float, default=0.0)
    cost_per_demo = Column(Float, default=0.0)
    return_on_investment = Column(Float, default=0.0)
    
    # Subject Breakdown
    subject_performance = Column(JSON)  # Performance by subject
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    tutor = relationship('User')
    
    def __repr__(self):
        return f'<DemoAnalytics {self.tutor_id}:{self.analytics_date}>'
    
    def to_dict(self):
        """Convert demo analytics to dictionary"""
        return {
            'id': self.id,
            'tutor_id': self.tutor_id,
            'analytics_date': self.analytics_date.isoformat() if self.analytics_date else None,
            'period_type': self.period_type,
            'total_demos_requested': self.total_demos_requested,
            'total_demos_completed': self.total_demos_completed,
            'total_demos_cancelled': self.total_demos_cancelled,
            'total_demos_no_show': self.total_demos_no_show,
            'conversion_to_paid': self.conversion_to_paid,
            'conversion_rate': self.conversion_rate,
            'average_time_to_conversion': self.average_time_to_conversion,
            'average_rating': self.average_rating,
            'average_duration_minutes': self.average_duration_minutes,
            'student_satisfaction_score': self.student_satisfaction_score,
            'repeat_demo_students': self.repeat_demo_students,
            'new_demo_students': self.new_demo_students,
            'referral_demos': self.referral_demos,
            'estimated_revenue_from_conversions': self.estimated_revenue_from_conversions,
            'cost_per_demo': self.cost_per_demo,
            'return_on_investment': self.return_on_investment,
            'subject_performance': self.subject_performance or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_conversion_rate(self):
        """Calculate conversion rate"""
        if self.total_demos_completed == 0:
            self.conversion_rate = 0.0
        else:
            self.conversion_rate = (self.conversion_to_paid / self.total_demos_completed) * 100
        
        return self.conversion_rate