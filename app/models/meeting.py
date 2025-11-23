from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.course import Course
import secrets


class Meeting(db.Model):
    """
    Comprehensive meeting model for video conferencing integration
    """
    __tablename__ = 'meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Meeting scheduling
    scheduled_time = db.Column(db.DateTime, nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    timezone = db.Column(db.String(50), default='UTC')
    
    # Meeting status
    status = db.Column(db.Enum('Scheduled', 'Ongoing', 'Completed', 'Cancelled', 'No-Show', name='meeting_statuses'), 
                      nullable=False, default='Scheduled')
    
    # Host and participants
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    host_type = db.Column(db.Enum('Tutor', 'Admin', name='host_types'), nullable=False, default='Tutor')
    
    # Meeting platform details
    platform = db.Column(db.Enum('Zoom', 'Google Meet', 'Microsoft Teams', 'Custom', name='meeting_platforms'), 
                        nullable=False, default='Zoom')
    meeting_url = db.Column(db.String(500))
    meeting_id = db.Column(db.String(100))
    password = db.Column(db.String(50))
    host_key = db.Column(db.String(100))
    
    # Meeting settings
    enable_recording = db.Column(db.Boolean, default=False)
    enable_waiting_room = db.Column(db.Boolean, default=True)
    enable_participant_video = db.Column(db.Boolean, default=True)
    enable_participant_audio = db.Column(db.Boolean, default=True)
    enable_chat = db.Column(db.Boolean, default=True)
    enable_screen_share = db.Column(db.Boolean, default=True)
    
    # Security settings
    require_password = db.Column(db.Boolean, default=False)
    enable_authentication = db.Column(db.Boolean, default=True)
    one_time_link = db.Column(db.Boolean, default=False)
    link_expires_at = db.Column(db.DateTime)
    
    # Recording details
    recording_url = db.Column(db.String(500))
    recording_duration = db.Column(db.Integer)  # in minutes
    recording_size = db.Column(db.BigInteger)  # in bytes
    recording_password = db.Column(db.String(50))
    
    # Meeting analytics
    actual_start_time = db.Column(db.DateTime)
    actual_end_time = db.Column(db.DateTime)
    participant_count = db.Column(db.Integer, default=0)
    max_participants = db.Column(db.Integer, default=100)
    
    # Relationships
    host = db.relationship('User', foreign_keys=[host_id], backref='hosted_meetings')
    participants = db.relationship('MeetingParticipant', backref='meeting', cascade='all, delete-orphan')
    recordings = db.relationship('MeetingRecording', backref='meeting', cascade='all, delete-orphan')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_host_meeting', 'host_id', 'scheduled_time'),
        db.Index('idx_status_time', 'status', 'scheduled_time'),
        db.Index('idx_platform_meeting', 'platform', 'meeting_id'),
    )
    
    def __repr__(self):
        return f'<Meeting {self.title} - {self.platform}>'
    
    @property
    def end_time(self):
        """Calculate end time based on scheduled time and duration"""
        return self.scheduled_time + timedelta(minutes=self.duration_minutes)
    
    @property
    def is_expired(self):
        """Check if meeting link has expired"""
        if self.link_expires_at is None:
            return False
        return datetime.utcnow() > self.link_expires_at
    
    @property
    def is_upcoming(self):
        """Check if meeting is in future"""
        return self.scheduled_time > datetime.utcnow()
    
    @property
    def is_past(self):
        """Check if meeting is in past"""
        return self.scheduled_time <= datetime.utcnow()
    
    @property
    def is_ongoing(self):
        """Check if meeting is currently ongoing"""
        now = datetime.utcnow()
        return self.scheduled_time <= now <= self.end_time
    
    def generate_secure_password(self, length=8):
        """Generate a secure meeting password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        self.password = password
        return password
    
    def generate_host_key(self):
        """Generate a unique host key"""
        self.host_key = secrets.token_urlsafe(16)
        return self.host_key
    
    def add_participant(self, user_id, role='Participant'):
        """Add a participant to the meeting"""
        participant = MeetingParticipant(
            meeting_id=self.id,
            user_id=user_id,
            role=role
        )
        db.session.add(participant)
        return participant
    
    def start_meeting(self):
        """Mark meeting as ongoing"""
        self.status = 'Ongoing'
        self.actual_start_time = datetime.utcnow()
        db.session.commit()
    
    def end_meeting(self):
        """Mark meeting as completed"""
        self.status = 'Completed'
        self.actual_end_time = datetime.utcnow()
        if self.actual_start_time:
            duration = (self.actual_end_time - self.actual_start_time).total_seconds() / 60
            self.recording_duration = int(duration)
        db.session.commit()
 

class MeetingParticipant(db.Model):
    """
    Model for meeting participants
    """
    __tablename__ = 'meeting_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Enum('Host', 'Co-Host', 'Participant', 'Panelist', name='participant_roles'), 
                     nullable=False, default='Participant')
    
    # Participation details
    joined_at = db.Column(db.DateTime)
    left_at = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    
    # Permissions
    can_share_screen = db.Column(db.Boolean, default=False)
    can_record = db.Column(db.Boolean, default=False)
    can_mute_participants = db.Column(db.Boolean, default=False)
    
    # Status
    status = db.Column(db.Enum('Invited', 'Joined', 'Left', 'No-Show', name='participant_statuses'), 
                      nullable=False, default='Invited')
    
    # Relationships
    user = db.relationship('User', backref='meeting_participations')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_meeting_participant', 'meeting_id', 'user_id'),
        db.Index('idx_user_participation', 'user_id', 'status'),
    )
    
    def __repr__(self):
        return f'<MeetingParticipant {self.user.email} - {self.role}>'


class MeetingRecording(db.Model):
    """
    Model for meeting recordings
    """
    __tablename__ = 'meeting_recordings'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    
    # Recording details
    recording_url = db.Column(db.String(500), nullable=False)
    recording_id = db.Column(db.String(100))
    file_name = db.Column(db.String(200))
    file_size = db.Column(db.BigInteger)  # in bytes
    duration_minutes = db.Column(db.Integer)
    file_format = db.Column(db.String(20), default='MP4')
    
    # Security
    password = db.Column(db.String(50))
    download_enabled = db.Column(db.Boolean, default=True)
    share_enabled = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    
    # Processing status
    status = db.Column(db.Enum('Processing', 'Ready', 'Failed', 'Deleted', name='recording_statuses'), 
                      nullable=False, default='Processing')
    
    # Metadata
    thumbnail_url = db.Column(db.String(500))
    transcript_url = db.Column(db.String(500))
    chat_log_url = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MeetingRecording {self.file_name} - {self.status}>'


class MeetingTemplate(db.Model):
    """
    Model for meeting templates
    """
    __tablename__ = 'meeting_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Template settings
    meeting_type = db.Column(db.Enum('Regular', 'Demo', 'Consultation', 'Group', 'Webinar', name='template_meeting_types'), 
                             nullable=False, default='Regular')
    platform = db.Column(db.Enum('Zoom', 'Google Meet', 'Microsoft Teams', 'Custom', name='template_platforms'), 
                          nullable=False, default='Zoom')
    
    # Default settings
    default_duration = db.Column(db.Integer, default=60)
    enable_recording = db.Column(db.Boolean, default=False)
    enable_waiting_room = db.Column(db.Boolean, default=True)
    enable_participant_video = db.Column(db.Boolean, default=True)
    enable_participant_audio = db.Column(db.Boolean, default=True)
    enable_chat = db.Column(db.Boolean, default=True)
    enable_screen_share = db.Column(db.Boolean, default=True)
    require_password = db.Column(db.Boolean, default=False)
    enable_authentication = db.Column(db.Boolean, default=True)
    
    # Owner
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    
    # Relationships
    creator = db.relationship('User', backref='meeting_templates')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MeetingTemplate {self.name}>'


class MeetingCalendar(db.Model):
    """
    Model for calendar integration
    """
    __tablename__ = 'meeting_calendars'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    calendar_type = db.Column(db.Enum('Google', 'Outlook', 'Apple', name='calendar_types'), 
                             nullable=False, default='Google')
    calendar_id = db.Column(db.String(200), nullable=False)
    calendar_name = db.Column(db.String(200))
    
    # Integration details
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    
    # Sync settings
    sync_enabled = db.Column(db.Boolean, default=True)
    sync_direction = db.Column(db.Enum('Import', 'Export', 'Bidirectional', name='sync_directions'), 
                               default='Bidirectional')
    last_sync_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='calendars')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MeetingCalendar {self.calendar_name} - {self.calendar_type}>'


class MeetingReminder(db.Model):
    """
    Model for meeting reminders
    """
    __tablename__ = 'meeting_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Reminder settings
    reminder_type = db.Column(db.Enum('Email', 'SMS', 'Push', name='reminder_types'), 
                             nullable=False, default='Email')
    reminder_time = db.Column(db.Integer, nullable=False)  # minutes before meeting
    
    # Status
    is_sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime)
    
    # Relationships
    meeting = db.relationship('Meeting', backref='reminders')
    user = db.relationship('User', backref='meeting_reminders')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MeetingReminder {self.reminder_time}min before {self.meeting.title}>'


class MeetingAnalytics(db.Model):
    """
    Model for meeting analytics and reporting
    """
    __tablename__ = 'meeting_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    
    # Participation metrics
    total_participants = db.Column(db.Integer, default=0)
    peak_participants = db.Column(db.Integer, default=0)
    average_participation_time = db.Column(db.Integer)  # in minutes
    
    # Engagement metrics
    chat_messages_count = db.Column(db.Integer, default=0)
    screen_shares_count = db.Column(db.Integer, default=0)
    reactions_count = db.Column(db.Integer, default=0)
    hand_raises_count = db.Column(db.Integer, default=0)
    
    # Technical metrics
    connection_issues_count = db.Column(db.Integer, default=0)
    audio_issues_count = db.Column(db.Integer, default=0)
    video_issues_count = db.Column(db.Integer, default=0)
    
    # Quality metrics
    overall_rating = db.Column(db.Float)
    audio_quality_rating = db.Column(db.Float)
    video_quality_rating = db.Column(db.Float)
    
    # Relationships
    meeting = db.relationship('Meeting', backref='analytics')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MeetingAnalytics for {self.meeting.title}>'