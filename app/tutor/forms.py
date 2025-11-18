from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, IntegerField, BooleanField, SubmitField, FileField, TimeField, DateField, DateTimeField, MultipleFileField
from wtforms.validators import DataRequired, Length, Email, URL, NumberRange, Optional, ValidationError
from wtforms.widgets import TextArea
import re
from datetime import datetime

class CKEditorWidget(TextArea):
    """Widget for CKEditor text area"""
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class', 'ckeditor')
        return super(CKEditorWidget, self).__call__(field, **kwargs)

class CKEditorField(TextAreaField):
    """Field for CKEditor"""
    widget = CKEditorWidget()

class ProfileForm(FlaskForm):
    """Form for tutor profile management"""
    # Basic Information
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required'),
        Length(min=2, max=50, message='First name must be between 2 and 50 characters')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required'),
        Length(min=2, max=50, message='Last name must be between 2 and 50 characters')
    ])
    phone = StringField('Phone Number', validators=[
        Optional(),
        Length(min=10, max=20, message='Phone number must be between 10 and 20 characters')
    ])
    
    # Professional Information
    title = StringField('Professional Title', validators=[
        DataRequired(message='Professional title is required'),
        Length(min=2, max=100, message='Title must be between 2 and 100 characters')
    ])
    bio = CKEditorField('Professional Bio', validators=[
        DataRequired(message='Professional bio is required'),
        Length(min=50, max=2000, message='Bio must be between 50 and 2000 characters')
    ])
    expertise = TextAreaField('Areas of Expertise', validators=[
        DataRequired(message='Areas of expertise are required'),
        Length(min=10, max=1000, message='Expertise description must be between 10 and 1000 characters')
    ])
    education = TextAreaField('Education', validators=[
        Optional(),
        Length(max=1000, message='Education details must be less than 1000 characters')
    ])
    experience = TextAreaField('Teaching Experience', validators=[
        Optional(),
        Length(max=1000, message='Experience details must be less than 1000 characters')
    ])
    
    # Profile Picture
    profile_picture = FileField('Profile Picture', validators=[
        Optional()
    ])
    
    # Video Introduction
    video_intro_url = StringField('Video Introduction URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL')
    ])
    
    # Pricing Information
    hourly_rate = DecimalField('Hourly Rate (USD)', validators=[
        DataRequired(message='Hourly rate is required'),
        NumberRange(min=1, max=1000, message='Hourly rate must be between $1 and $1000')
    ])
    currency = SelectField('Currency', choices=[
        ('USD', 'US Dollar (USD)'),
        ('EUR', 'Euro (EUR)'),
        ('GBP', 'British Pound (GBP)'),
        ('INR', 'Indian Rupee (INR)'),
        ('JPY', 'Japanese Yen (JPY)')
    ], default='USD')
    
    # Payment Information
    upi_id = StringField('UPI ID', validators=[
        Optional(),
        Length(max=50, message='UPI ID must be less than 50 characters')
    ])
    preferred_payment_method = SelectField('Preferred Payment Method', choices=[
        ('upi', 'UPI'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('other', 'Other')
    ], default='upi')
    bank_account_name = StringField('Bank Account Name', validators=[
        Optional(),
        Length(max=100, message='Account name must be less than 100 characters')
    ])
    bank_account_number = StringField('Bank Account Number', validators=[
        Optional(),
        Length(max=20, message='Account number must be less than 20 characters')
    ])
    bank_ifsc_code = StringField('Bank IFSC Code', validators=[
        Optional(),
        Length(max=11, message='IFSC code must be less than 11 characters')
    ])
    
    # Subjects
    subjects = SelectField('Subjects You Teach', coerce=int, validators=[
        DataRequired(message='Please select at least one subject')
    ])
    proficiency_level = SelectField('Proficiency Level', choices=[
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert')
    ], default='Intermediate')
    
    # Availability Preferences
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
    
    # Additional Information
    languages = StringField('Languages Spoken', validators=[
        Optional(),
        Length(max=200, message='Languages must be less than 200 characters')
    ])
    teaching_style = TextAreaField('Teaching Style', validators=[
        Optional(),
        Length(max=1000, message='Teaching style must be less than 1000 characters')
    ])
    
    submit = SubmitField('Update Profile')
    
    def validate_phone(self, phone):
        """Custom validator for phone number"""
        if phone.data and not re.match(r'^[\d\s\-\+\(\)]+$', phone.data):
            raise ValidationError('Phone number contains invalid characters')
    
    def validate_upi_id(self, upi_id):
        """Custom validator for UPI ID"""
        if upi_id.data and not re.match(r'^[a-zA-Z0-9\.\_\-]+@[a-zA-Z0-9]+$', upi_id.data):
            raise ValidationError('UPI ID format is invalid')


class AvailabilityForm(FlaskForm):
    """Form for managing tutor availability"""
    day_of_week = SelectField('Day of Week', choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
    ], validators=[DataRequired(message='Please select a day')])
    
    start_time = TimeField('Start Time', validators=[
        DataRequired(message='Start time is required')
    ])
    
    end_time = TimeField('End Time', validators=[
        DataRequired(message='End time is required')
    ])
    
    is_available = BooleanField('Available', default=True)
    
    submit = SubmitField('Save Availability')


class BulkAvailabilityForm(FlaskForm):
    """Form for bulk availability management"""
    csv_file = FileField('CSV File', validators=[
        DataRequired(message='Please select a CSV file')
    ])
    
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
    
    submit = SubmitField('Import Availability')
    export = SubmitField('Export Availability')


class BookingForm(FlaskForm):
    """Form for managing bookings"""
    student_id = SelectField('Student', coerce=int, validators=[
        DataRequired(message='Please select a student')
    ])
    
    course_id = SelectField('Course', coerce=int, validators=[
        DataRequired(message='Please select a course')
    ])
    
    scheduled_time = DateTimeField('Scheduled Time', validators=[
        DataRequired(message='Scheduled time is required')
    ])
    
    duration_minutes = IntegerField('Duration (minutes)', validators=[
        DataRequired(message='Duration is required'),
        NumberRange(min=15, max=240, message='Duration must be between 15 and 240 minutes')
    ])
    
    notes = TextAreaField('Notes', validators=[
        Optional(),
        Length(max=500, message='Notes must be less than 500 characters')
    ])
    
    submit = SubmitField('Update Booking')


class RescheduleForm(FlaskForm):
    """Form for rescheduling bookings"""
    new_scheduled_time = DateTimeField('New Scheduled Time', validators=[
        DataRequired(message='New scheduled time is required')
    ])
    
    new_duration_minutes = IntegerField('New Duration (minutes)', validators=[
        DataRequired(message='Duration is required'),
        NumberRange(min=15, max=240, message='Duration must be between 15 and 240 minutes')
    ])
    
    notes = TextAreaField('Rescheduling Notes', validators=[
        Optional(),
        Length(max=500, message='Notes must be less than 500 characters')
    ])
    
    submit = SubmitField('Reschedule')


class DemoRequestForm(FlaskForm):
    """Form for managing demo requests"""
    preferred_date = DateField('Preferred Date', validators=[
        DataRequired(message='Preferred date is required')
    ])
    
    preferred_time = TimeField('Preferred Time', validators=[
        DataRequired(message='Preferred time is required')
    ])
    
    duration_minutes = IntegerField('Duration (minutes)', validators=[
        DataRequired(message='Duration is required'),
        NumberRange(min=15, max=120, message='Duration must be between 15 and 120 minutes')
    ], default=30)
    
    notes = TextAreaField('Notes', validators=[
        Optional(),
        Length(max=500, message='Notes must be less than 500 characters')
    ])
    
    submit = SubmitField('Schedule Demo')


class FeedbackForm(FlaskForm):
    """Form for collecting demo feedback"""
    rating = SelectField('Rating', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please select a rating')])
    
    teaching_quality = SelectField('Teaching Quality', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate teaching quality')])
    
    communication = SelectField('Communication', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate communication')])
    
    preparation = SelectField('Preparation', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate preparation')])
    
    value_for_money = SelectField('Value for Money', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate value for money')])
    
    comments = TextAreaField('Comments', validators=[
        Optional(),
        Length(max=1000, message='Comments must be less than 1000 characters')
    ])
    
    would_recommend = BooleanField('I would recommend this tutor to others')
    
    submit = SubmitField('Submit Feedback')


class MeetingLinkForm(FlaskForm):
    """Form for generating meeting links"""
    platform = SelectField('Platform', choices=[
        ('Zoom', 'Zoom'),
        ('Google Meet', 'Google Meet'),
        ('Microsoft Teams', 'Microsoft Teams'),
        ('Other', 'Other')
    ], validators=[DataRequired(message='Please select a platform')])
    
    meeting_url = StringField('Meeting URL', validators=[
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
    ])
    
    submit = SubmitField('Generate Meeting Link')


class RescheduleDemoForm(FlaskForm):
    """Form for rescheduling demo classes"""
    scheduled_date = DateField('Scheduled Date', validators=[
        DataRequired(message='Scheduled date is required')
    ])
    
    scheduled_time = TimeField('Scheduled Time', validators=[
        DataRequired(message='Scheduled time is required')
    ])
    
    duration_minutes = IntegerField('Duration (minutes)', validators=[
        DataRequired(message='Duration is required'),
        NumberRange(min=15, max=120, message='Duration must be between 15 and 120 minutes')
    ])
    
    meeting_link = StringField('Meeting Link (optional)', validators=[
        Optional(),
        URL(message='Please enter a valid URL')
    ])
    
    notes = TextAreaField('Notes', validators=[
        Optional(),
        Length(max=500, message='Notes must be less than 500 characters')
    ])
    
    submit = SubmitField('Reschedule Demo')