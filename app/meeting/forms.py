from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, SubmitField, DateTimeField, DateField, TimeField, MultipleFileField, URLField
from wtforms.validators import DataRequired, Length, URL, NumberRange, Optional, ValidationError
from wtforms.widgets import TextArea
from datetime import datetime, timedelta
import re


class CKEditorWidget(TextArea):
    """Widget for CKEditor text area"""
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class', 'ckeditor')
        return super(CKEditorWidget, self).__call__(field, **kwargs)


class CKEditorField(TextAreaField):
    """Field for CKEditor"""
    widget = CKEditorWidget()


class MeetingForm(FlaskForm):
    """Form for creating and editing meetings"""
    title = StringField('Meeting Title', validators=[
        DataRequired(message='Meeting title is required'),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters')
    ])
    
    description = CKEditorField('Description', validators=[
        Optional(),
        Length(max=2000, message='Description must be less than 2000 characters')
    ])
    
    meeting_type = SelectField('Meeting Type', choices=[
        ('Regular', 'Regular Meeting'),
        ('Demo', 'Demo Class'),
        ('Consultation', 'Consultation'),
        ('Group', 'Group Meeting'),
        ('Webinar', 'Webinar')
    ], validators=[DataRequired(message='Please select a meeting type')])
    
    scheduled_time = DateTimeField('Scheduled Time', validators=[
        DataRequired(message='Scheduled time is required')
    ], format='%Y-%m-%d %H:%M')
    
    duration_minutes = IntegerField('Duration (minutes)', validators=[
        DataRequired(message='Duration is required'),
        NumberRange(min=15, max=480, message='Duration must be between 15 and 480 minutes')
    ], default=60)
    
    timezone = SelectField('Time Zone', choices=[
        ('UTC', 'UTC'),
        ('US/Eastern', 'US Eastern'),
        ('US/Central', 'US Central'),
        ('US/Mountain', 'US Mountain'),
        ('US/Pacific', 'US Pacific'),
        ('Europe/London', 'Europe London'),
        ('Europe/Paris', 'Europe Paris'),
        ('Asia/Calcutta', 'Asia Calcutta'),
        ('Asia/Shanghai', 'Asia Shanghai'),
        ('Asia/Tokyo', 'Asia Tokyo'),
        ('Australia/Sydney', 'Australia Sydney')
    ], default='UTC')
    
    platform = SelectField('Meeting Platform', choices=[
        ('Zoom', 'Zoom'),
        ('Google Meet', 'Google Meet'),
        ('Microsoft Teams', 'Microsoft Teams'),
        ('Custom', 'Custom Platform')
    ], validators=[DataRequired(message='Please select a platform')])
    
    meeting_url = URLField('Meeting URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL')
    ])
    
    meeting_id = StringField('Meeting ID', validators=[
        Optional(),
        Length(max=100, message='Meeting ID must be less than 100 characters')
    ])
    
    password = StringField('Meeting Password', validators=[
        Optional(),
        Length(max=50, message='Password must be less than 50 characters')
    ])
    
    max_participants = IntegerField('Maximum Participants', validators=[
        DataRequired(message='Maximum participants is required'),
        NumberRange(min=1, max=1000, message='Participants must be between 1 and 1000')
    ], default=100)
    
    # Meeting settings
    enable_recording = BooleanField('Enable Recording')
    enable_waiting_room = BooleanField('Enable Waiting Room', default=True)
    enable_participant_video = BooleanField('Enable Participant Video', default=True)
    enable_participant_audio = BooleanField('Enable Participant Audio', default=True)
    enable_chat = BooleanField('Enable Chat', default=True)
    enable_screen_share = BooleanField('Enable Screen Sharing', default=True)
    
    # Security settings
    require_password = BooleanField('Require Password')
    enable_authentication = BooleanField('Enable Authentication', default=True)
    one_time_link = BooleanField('One-Time Link')
    link_expires_at = DateTimeField('Link Expires At', validators=[
        Optional()
    ], format='%Y-%m-%d %H:%M')
    
    submit = SubmitField('Save Meeting')
    
    def validate_scheduled_time(self, scheduled_time):
        """Validate that scheduled time is in the future"""
        if scheduled_time.data and scheduled_time.data <= datetime.utcnow():
            raise ValidationError('Meeting must be scheduled for a future time')
    
    def validate_link_expires_at(self, link_expires_at):
        """Validate that link expiration is after scheduled time"""
        if link_expires_at.data and self.scheduled_time.data:
            if link_expires_at.data <= self.scheduled_time.data:
                raise ValidationError('Link expiration must be after scheduled meeting time')


class MeetingTemplateForm(FlaskForm):
    """Form for creating and editing meeting templates"""
    name = StringField('Template Name', validators=[
        DataRequired(message='Template name is required'),
        Length(min=3, max=100, message='Name must be between 3 and 100 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500, message='Description must be less than 500 characters')
    ])
    
    meeting_type = SelectField('Meeting Type', choices=[
        ('Regular', 'Regular Meeting'),
        ('Demo', 'Demo Class'),
        ('Consultation', 'Consultation'),
        ('Group', 'Group Meeting'),
        ('Webinar', 'Webinar')
    ], validators=[DataRequired(message='Please select a meeting type')])
    
    platform = SelectField('Default Platform', choices=[
        ('Zoom', 'Zoom'),
        ('Google Meet', 'Google Meet'),
        ('Microsoft Teams', 'Microsoft Teams'),
        ('Custom', 'Custom Platform')
    ], validators=[DataRequired(message='Please select a platform')])
    
    default_duration = IntegerField('Default Duration (minutes)', validators=[
        DataRequired(message='Default duration is required'),
        NumberRange(min=15, max=480, message='Duration must be between 15 and 480 minutes')
    ], default=60)
    
    # Default settings
    enable_recording = BooleanField('Enable Recording by Default')
    enable_waiting_room = BooleanField('Enable Waiting Room by Default', default=True)
    enable_participant_video = BooleanField('Enable Participant Video by Default', default=True)
    enable_participant_audio = BooleanField('Enable Participant Audio by Default', default=True)
    enable_chat = BooleanField('Enable Chat by Default', default=True)
    enable_screen_share = BooleanField('Enable Screen Sharing by Default', default=True)
    require_password = BooleanField('Require Password by Default')
    enable_authentication = BooleanField('Enable Authentication by Default', default=True)
    is_public = BooleanField('Make Template Public')
    
    submit = SubmitField('Save Template')


class MeetingParticipantForm(FlaskForm):
    """Form for adding meeting participants"""
    user_id = SelectField('Participant', coerce=int, validators=[
        DataRequired(message='Please select a participant')
    ])
    
    role = SelectField('Role', choices=[
        ('Host', 'Host'),
        ('Co-Host', 'Co-Host'),
        ('Participant', 'Participant'),
        ('Panelist', 'Panelist')
    ], validators=[DataRequired(message='Please select a role')])
    
    can_share_screen = BooleanField('Can Share Screen')
    can_record = BooleanField('Can Record')
    can_mute_participants = BooleanField('Can Mute Participants')
    
    submit = SubmitField('Add Participant')


class MeetingReminderForm(FlaskForm):
    """Form for setting meeting reminders"""
    reminder_type = SelectField('Reminder Type', choices=[
        ('Email', 'Email'),
        ('SMS', 'SMS'),
        ('Push', 'Push Notification')
    ], validators=[DataRequired(message='Please select a reminder type')])
    
    reminder_time = IntegerField('Reminder Time (minutes before meeting)', validators=[
        DataRequired(message='Reminder time is required'),
        NumberRange(min=5, max=1440, message='Reminder time must be between 5 and 1440 minutes')
    ], default=15)
    
    submit = SubmitField('Set Reminder')


class MeetingCalendarForm(FlaskForm):
    """Form for calendar integration"""
    calendar_type = SelectField('Calendar Type', choices=[
        ('Google', 'Google Calendar'),
        ('Outlook', 'Outlook Calendar'),
        ('Apple', 'Apple Calendar')
    ], validators=[DataRequired(message='Please select a calendar type')])
    
    calendar_name = StringField('Calendar Name', validators=[
        DataRequired(message='Calendar name is required'),
        Length(max=200, message='Calendar name must be less than 200 characters')
    ])
    
    sync_enabled = BooleanField('Enable Sync', default=True)
    sync_direction = SelectField('Sync Direction', choices=[
        ('Import', 'Import Only'),
        ('Export', 'Export Only'),
        ('Bidirectional', 'Bidirectional')
    ], default='Bidirectional')
    
    submit = SubmitField('Connect Calendar')


class MeetingRecordingForm(FlaskForm):
    """Form for managing meeting recordings"""
    file_name = StringField('Recording Name', validators=[
        DataRequired(message='Recording name is required'),
        Length(max=200, message='Recording name must be less than 200 characters')
    ])
    
    file_format = SelectField('File Format', choices=[
        ('MP4', 'MP4'),
        ('M4A', 'M4A'),
        ('MP3', 'MP3'),
        ('TXT', 'TXT (Transcript)')
    ], validators=[DataRequired(message='Please select a file format')])
    
    password = StringField('Recording Password', validators=[
        Optional(),
        Length(max=50, message='Password must be less than 50 characters')
    ])
    
    download_enabled = BooleanField('Allow Download', default=True)
    share_enabled = BooleanField('Allow Sharing', default=True)
    expires_at = DateTimeField('Expires At', validators=[
        Optional()
    ], format='%Y-%m-%d %H:%M')
    
    submit = SubmitField('Save Recording Settings')


class MeetingLinkForm(FlaskForm):
    """Form for generating meeting links"""
    platform = SelectField('Platform', choices=[
        ('Zoom', 'Zoom'),
        ('Google Meet', 'Google Meet'),
        ('Microsoft Teams', 'Microsoft Teams'),
        ('Custom', 'Custom')
    ], validators=[DataRequired(message='Please select a platform')])
    
    meeting_url = URLField('Meeting URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL')
    ])
    
    meeting_id = StringField('Meeting ID', validators=[
        Optional(),
        Length(max=100, message='Meeting ID must be less than 100 characters')
    ])
    
    password = StringField('Password', validators=[
        Optional(),
        Length(max=50, message='Password must be less than 50 characters')
    ])
    
    expires_at = DateTimeField('Expires At', validators=[
        Optional()
    ], format='%Y-%m-%d %H:%M')
    
    submit = SubmitField('Generate Meeting Link')


class MeetingSearchForm(FlaskForm):
    """Form for searching meetings"""
    query = StringField('Search', validators=[
        Optional(),
        Length(max=100, message='Search query must be less than 100 characters')
    ])
    
    status = SelectField('Status', choices=[
        ('', 'All Status'),
        ('Scheduled', 'Scheduled'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('No-Show', 'No-Show')
    ], default='')
    
    meeting_type = SelectField('Meeting Type', choices=[
        ('', 'All Types'),
        ('Regular', 'Regular'),
        ('Demo', 'Demo'),
        ('Consultation', 'Consultation'),
        ('Group', 'Group'),
        ('Webinar', 'Webinar')
    ], default='')
    
    platform = SelectField('Platform', choices=[
        ('', 'All Platforms'),
        ('Zoom', 'Zoom'),
        ('Google Meet', 'Google Meet'),
        ('Microsoft Teams', 'Microsoft Teams'),
        ('Custom', 'Custom')
    ], default='')
    
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    
    submit = SubmitField('Search')


class MeetingFeedbackForm(FlaskForm):
    """Form for collecting meeting feedback"""
    overall_rating = SelectField('Overall Rating', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please provide an overall rating')])
    
    audio_quality = SelectField('Audio Quality', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate audio quality')])
    
    video_quality = SelectField('Video Quality', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate video quality')])
    
    content_quality = SelectField('Content Quality', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate content quality')])
    
    comments = TextAreaField('Comments', validators=[
        Optional(),
        Length(max=1000, message='Comments must be less than 1000 characters')
    ])
    
    would_recommend = BooleanField('I would recommend this meeting to others')
    
    submit = SubmitField('Submit Feedback')


class MeetingRescheduleForm(FlaskForm):
    """Form for rescheduling meetings"""
    new_scheduled_time = DateTimeField('New Scheduled Time', validators=[
        DataRequired(message='New scheduled time is required')
    ], format='%Y-%m-%d %H:%M')
    
    new_duration_minutes = IntegerField('New Duration (minutes)', validators=[
        DataRequired(message='Duration is required'),
        NumberRange(min=15, max=480, message='Duration must be between 15 and 480 minutes')
    ])
    
    reason = TextAreaField('Rescheduling Reason', validators=[
        DataRequired(message='Please provide a reason for rescheduling'),
        Length(max=500, message='Reason must be less than 500 characters')
    ])
    
    notify_participants = BooleanField('Notify Participants', default=True)
    
    submit = SubmitField('Reschedule Meeting')
    
    def validate_new_scheduled_time(self, new_scheduled_time):
        """Validate that new scheduled time is in the future"""
        if new_scheduled_time.data and new_scheduled_time.data <= datetime.utcnow():
            raise ValidationError('Meeting must be rescheduled for a future time')