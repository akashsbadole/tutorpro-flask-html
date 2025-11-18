from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.course import Course
import json


class DemoClass(db.Model):
    """
    Comprehensive demo class model for trial sessions
    """
    __tablename__ = 'demo_classes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Demo scheduling
    scheduled_time = db.Column(db.DateTime, nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    timezone = db.Column(db.String(50), default='UTC')
    
    # Demo status
    status = db.Column(db.Enum('Requested', 'Confirmed', 'Scheduled', 'Ongoing', 'Completed', 'Cancelled', 'No-Show', name='demo_statuses'), 
                      nullable=False, default='Requested')
    
    # Participants
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    
    # Meeting details
    meeting_url = db.Column(db.String(500))
    meeting_password = db.Column(db.String(50))
    meeting_platform = db.Column(db.Enum('Zoom', 'Google Meet', 'Microsoft Teams', 'Custom', name='demo_platforms'), 
                                default='Zoom')
    
    # Demo settings
    preparation_materials = db.Column(db.Text)  # JSON array of material URLs
    max_participants = db.Column(db.Integer, default=1)
    is_group_demo = db.Column(db.Boolean, default=False)
    
    # Conversion tracking
    conversion_status = db.Column(db.Enum('Not_Converted', 'Interested', 'Enrolled', 'Not_Interested', name='conversion_statuses'), 
                                 default='Not_Converted')
    conversion_notes = db.Column(db.Text)
    follow_up_required = db.Column(db.Boolean, default=True)
    follow_up_date = db.Column(db.DateTime)
    
    # Demo analytics
    student_attended = db.Column(db.Boolean)
    tutor_attended = db.Column(db.Boolean)
    actual_start_time = db.Column(db.DateTime)
    actual_end_time = db.Column(db.DateTime)
    attendance_notes = db.Column(db.Text)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='demo_classes')
    tutor = db.relationship('TutorProfile', foreign_keys=[tutor_id], backref='demo_classes')
    course = db.relationship('Course', foreign_keys=[course_id])
    feedback = db.relationship('DemoFeedback', backref='demo_class', uselist=False, cascade='all, delete-orphan')
    materials = db.relationship('DemoMaterial', backref='demo_class', cascade='all, delete-orphan')
    follow_ups = db.relationship('DemoFollowUp', backref='demo_class', cascade='all, delete-orphan')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_student_demo', 'student_id', 'scheduled_time'),
        db.Index('idx_tutor_demo', 'tutor_id', 'scheduled_time'),
        db.Index('idx_demo_status', 'status', 'scheduled_time'),
        db.Index('idx_conversion', 'conversion_status', 'follow_up_date'),
    )
    
    def __repr__(self):
        return f'<DemoClass {self.title} - {self.student.email} with {self.tutor.user.email}>'
    
    @property
    def end_time(self):
        """Calculate end time based on scheduled time and duration"""
        return self.scheduled_time + timedelta(minutes=self.duration_minutes)
    
    @property
    def is_upcoming(self):
        """Check if demo is in the future"""
        return self.scheduled_time > datetime.utcnow()
    
    @property
    def is_past(self):
        """Check if demo is in the past"""
        return self.scheduled_time <= datetime.utcnow()
    
    @property
    def is_ongoing(self):
        """Check if demo is currently ongoing"""
        now = datetime.utcnow()
        return self.scheduled_time <= now <= self.end_time
    
    def confirm_demo(self, meeting_url=None, meeting_password=None):
        """Confirm the demo class"""
        self.status = 'Confirmed'
        if meeting_url:
            self.meeting_url = meeting_url
        if meeting_password:
            self.meeting_password = meeting_password
        db.session.commit()
    
    def start_demo(self):
        """Mark demo as ongoing"""
        self.status = 'Ongoing'
        self.actual_start_time = datetime.utcnow()
        self.tutor_attended = True
        db.session.commit()
    
    def complete_demo(self, student_attended=True):
        """Mark demo as completed"""
        self.status = 'Completed'
        self.actual_end_time = datetime.utcnow()
        self.student_attended = student_attended
        db.session.commit()
    
    def convert_to_enrollment(self, notes=None):
        """Mark demo as converted to enrollment"""
        self.conversion_status = 'Enrolled'
        if notes:
            self.conversion_notes = notes
        self.follow_up_required = False
        db.session.commit()


class DemoFeedback(db.Model):
    """
    Model for demo class feedback
    """
    __tablename__ = 'demo_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    demo_class_id = db.Column(db.Integer, db.ForeignKey('demo_classes.id'), nullable=False)
    
    # Feedback from student
    student_rating = db.Column(db.Integer)  # 1-5 scale
    teaching_quality = db.Column(db.Integer)  # 1-5 scale
    communication = db.Column(db.Integer)  # 1-5 scale
    preparation = db.Column(db.Integer)  # 1-5 scale
    content_quality = db.Column(db.Integer)  # 1-5 scale
    
    # Feedback from tutor
    tutor_rating = db.Column(db.Integer)  # 1-5 scale
    student_engagement = db.Column(db.Integer)  # 1-5 scale
    student_participation = db.Column(db.Integer)  # 1-5 scale
    learning_potential = db.Column(db.Integer)  # 1-5 scale
    
    # Comments
    student_comments = db.Column(db.Text)
    tutor_comments = db.Column(db.Text)
    would_recommend = db.Column(db.Boolean)
    
    # Follow-up actions
    recommended_next_steps = db.Column(db.Text)
    suggested_course_level = db.Column(db.String(50))
    suggested_focus_areas = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DemoFeedback for DemoClass {self.demo_class_id}>'


class DemoMaterial(db.Model):
    """
    Model for demo class preparation materials
    """
    __tablename__ = 'demo_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    demo_class_id = db.Column(db.Integer, db.ForeignKey('demo_classes.id'), nullable=False)
    
    # Material details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    material_type = db.Column(db.Enum('Document', 'Video', 'Presentation', 'Link', 'Assignment', name='material_types'), 
                             nullable=False)
    file_url = db.Column(db.String(500))
    file_name = db.Column(db.String(200))
    file_size = db.Column(db.BigInteger)  # in bytes
    
    # Material settings
    is_required = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    
    # Access control
    student_accessible = db.Column(db.Boolean, default=True)
    accessible_before_demo = db.Column(db.Boolean, default=True)
    accessible_after_demo = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DemoMaterial {self.title}>'


class DemoFollowUp(db.Model):
    """
    Model for demo class follow-up activities
    """
    __tablename__ = 'demo_follow_ups'
    
    id = db.Column(db.Integer, primary_key=True)
    demo_class_id = db.Column(db.Integer, db.ForeignKey('demo_classes.id'), nullable=False)
    
    # Follow-up details
    follow_up_type = db.Column(db.Enum('Email', 'Phone', 'SMS', 'Meeting', name='follow_up_types'), 
                               nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Scheduling
    scheduled_for = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.Enum('Scheduled', 'Completed', 'Cancelled', 'Missed', name='follow_up_statuses'), 
                      nullable=False, default='Scheduled')
    
    # Results
    outcome = db.Column(db.Enum('Positive', 'Neutral', 'Negative', 'No_Response', name='follow_up_outcomes'))
    notes = db.Column(db.Text)
    next_action = db.Column(db.Text)
    next_action_date = db.Column(db.DateTime)
    
    # Assignment
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    assignee = db.relationship('User', backref='assigned_follow_ups')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DemoFollowUp {self.title} - {self.status}>'


class DemoTemplate(db.Model):
    """
    Model for demo class templates
    """
    __tablename__ = 'demo_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Template settings
    default_duration = db.Column(db.Integer, default=30)
    default_platform = db.Column(db.Enum('Zoom', 'Google Meet', 'Microsoft Teams', 'Custom', name='template_platforms'), 
                                 default='Zoom')
    
    # Content structure
    agenda = db.Column(db.Text)  # JSON structure of demo agenda
    objectives = db.Column(db.Text)  # JSON array of learning objectives
    materials_required = db.Column(db.Text)  # JSON array of required materials
    
    # Default materials
    welcome_message = db.Column(db.Text)
    introduction_script = db.Column(db.Text)
    closing_script = db.Column(db.Text)
    
    # Owner
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0)
    
    # Relationships
    creator = db.relationship('User', backref='demo_templates')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DemoTemplate {self.name}>'


class DemoAnalytics(db.Model):
    """
    Model for demo class analytics and conversion tracking
    """
    __tablename__ = 'demo_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    demo_class_id = db.Column(db.Integer, db.ForeignKey('demo_classes.id'), nullable=False)
    
    # Request analytics
    request_to_confirmation_time = db.Column(db.Integer)  # in hours
    request_source = db.Column(db.String(100))  # Where the request came from
    
    # Attendance analytics
    student_show_rate = db.Column(db.Float)  # Percentage
    tutor_show_rate = db.Column(db.Float)  # Percentage
    no_show_reason = db.Column(db.Text)
    
    # Engagement analytics
    participation_score = db.Column(db.Float)  # 1-10 scale
    engagement_level = db.Column(db.Enum('Low', 'Medium', 'High', name='engagement_levels'))
    questions_asked = db.Column(db.Integer, default=0)
    interactions_count = db.Column(db.Integer, default=0)
    
    # Conversion analytics
    conversion_probability = db.Column(db.Float)  # 0-1 scale
    conversion_time = db.Column(db.Integer)  # days from demo to conversion
    conversion_factors = db.Column(db.Text)  # JSON array of factors
    
    # Performance analytics
    tutor_performance_score = db.Column(db.Float)  # 1-10 scale
    content_effectiveness = db.Column(db.Float)  # 1-10 scale
    technical_issues = db.Column(db.Boolean, default=False)
    technical_issue_details = db.Column(db.Text)
    
    # Relationships
    demo_class = db.relationship('DemoClass', backref='analytics')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DemoAnalytics for DemoClass {self.demo_class_id}>'


class DemoRequest(db.Model):
    """
    Model for demo class requests from students
    """
    __tablename__ = 'demo_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Student information
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    
    # Request details
    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time = db.Column(db.Time, nullable=False)
    alternative_dates = db.Column(db.Text)  # JSON array of alternative dates
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    timezone = db.Column(db.String(50), default='UTC')
    
    # Request content
    learning_goals = db.Column(db.Text)
    current_level = db.Column(db.String(50))
    specific_topics = db.Column(db.Text)
    questions_for_tutor = db.Column(db.Text)
    
    # Request status
    status = db.Column(db.Enum('Pending', 'Reviewed', 'Accepted', 'Rejected', 'Scheduled', name='request_statuses'), 
                      nullable=False, default='Pending')
    
    # Processing details
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    
    # Scheduling details
    scheduled_date = db.Column(db.Date)
    scheduled_time = db.Column(db.Time)
    meeting_link = db.Column(db.String(500))
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='demo_requests')
    tutor = db.relationship('TutorProfile', foreign_keys=[tutor_id], backref='demo_requests')
    course = db.relationship('Course', foreign_keys=[course_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_student_request', 'student_id', 'status'),
        db.Index('idx_tutor_request', 'tutor_id', 'status'),
        db.Index('idx_request_date', 'preferred_date', 'status'),
    )
    
    def __repr__(self):
        return f'<DemoRequest {self.student.email} - {self.tutor.user.email}>'