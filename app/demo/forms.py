from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, SubmitField, DateTimeField, DateField, TimeField, MultipleFileField, URLField, FloatField
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


class DemoRequestForm(FlaskForm):
    """Form for requesting demo classes"""
    tutor_id = SelectField('Select Tutor', coerce=int, validators=[
        DataRequired(message='Please select a tutor')
    ])
    
    course_id = SelectField('Select Course', coerce=int, validators=[
        DataRequired(message='Please select a course')
    ])
    
    preferred_date = DateField('Preferred Date', validators=[
        DataRequired(message='Preferred date is required')
    ])
    
    preferred_time = TimeField('Preferred Time', validators=[
        DataRequired(message='Preferred time is required')
    ])
    
    alternative_dates = TextAreaField('Alternative Dates', validators=[
        Optional(),
        Length(max=500, message='Alternative dates must be less than 500 characters')
    ])
    
    duration_minutes = IntegerField('Duration (minutes)', validators=[
        DataRequired(message='Duration is required'),
        NumberRange(min=15, max=120, message='Duration must be between 15 and 120 minutes')
    ], default=30)
    
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
    
    learning_goals = TextAreaField('Learning Goals', validators=[
        Optional(),
        Length(max=1000, message='Learning goals must be less than 1000 characters')
    ])
    
    current_level = SelectField('Current Level', choices=[
        ('', 'Select your level'),
        ('Beginner', 'Beginner'),
        ('Elementary', 'Elementary'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert')
    ])
    
    specific_topics = TextAreaField('Specific Topics', validators=[
        Optional(),
        Length(max=1000, message='Specific topics must be less than 1000 characters')
    ])
    
    questions_for_tutor = TextAreaField('Questions for Tutor', validators=[
        Optional(),
        Length(max=1000, message='Questions must be less than 1000 characters')
    ])
    
    submit = SubmitField('Request Demo Class')
    
    def validate_preferred_date(self, preferred_date):
        """Validate that preferred date is in the future"""
        if preferred_date.data and preferred_date.data <= datetime.utcnow().date():
            raise ValidationError('Demo class must be scheduled for a future date')


class DemoClassForm(FlaskForm):
    """Form for creating and editing demo classes"""
    title = StringField('Demo Title', validators=[
        DataRequired(message='Demo title is required'),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters')
    ])
    
    description = CKEditorField('Description', validators=[
        Optional(),
        Length(max=2000, message='Description must be less than 2000 characters')
    ])
    
    student_id = SelectField('Student', coerce=int, validators=[
        DataRequired(message='Please select a student')
    ])
    
    tutor_id = SelectField('Tutor', coerce=int, validators=[
        DataRequired(message='Please select a tutor')
    ])
    
    course_id = SelectField('Course', coerce=int, validators=[
        Optional()
    ])
    
    scheduled_time = DateTimeField('Scheduled Time', validators=[
        DataRequired(message='Scheduled time is required')
    ], format='%Y-%m-%d %H:%M')
    
    duration_minutes = IntegerField('Duration (minutes)', validators=[
        DataRequired(message='Duration is required'),
        NumberRange(min=15, max=180, message='Duration must be between 15 and 180 minutes')
    ], default=30)
    
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
    
    meeting_platform = SelectField('Meeting Platform', choices=[
        ('Zoom', 'Zoom'),
        ('Google Meet', 'Google Meet'),
        ('Microsoft Teams', 'Microsoft Teams'),
        ('Custom', 'Custom')
    ], default='Zoom')
    
    meeting_url = URLField('Meeting URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL')
    ])
    
    meeting_password = StringField('Meeting Password', validators=[
        Optional(),
        Length(max=50, message='Password must be less than 50 characters')
    ])
    
    max_participants = IntegerField('Maximum Participants', validators=[
        DataRequired(message='Maximum participants is required'),
        NumberRange(min=1, max=50, message='Participants must be between 1 and 50')
    ], default=1)
    
    is_group_demo = BooleanField('Group Demo Class')
    
    preparation_materials = TextAreaField('Preparation Materials', validators=[
        Optional(),
        Length(max=1000, message='Preparation materials must be less than 1000 characters')
    ])
    
    submit = SubmitField('Save Demo Class')
    
    def validate_scheduled_time(self, scheduled_time):
        """Validate that scheduled time is in the future"""
        if scheduled_time.data and scheduled_time.data <= datetime.utcnow():
            raise ValidationError('Demo class must be scheduled for a future time')


class DemoFeedbackForm(FlaskForm):
    """Form for collecting demo feedback"""
    # Student feedback
    student_rating = SelectField('Overall Rating', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please provide an overall rating')])
    
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
    
    content_quality = SelectField('Content Quality', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate content quality')])
    
    student_comments = TextAreaField('Your Comments', validators=[
        Optional(),
        Length(max=1000, message='Comments must be less than 1000 characters')
    ])
    
    would_recommend = BooleanField('I would recommend this tutor to others')
    
    # Tutor feedback
    tutor_rating = SelectField('Student Performance', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate student performance')])
    
    student_engagement = SelectField('Student Engagement', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate student engagement')])
    
    student_participation = SelectField('Student Participation', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate student participation')])
    
    learning_potential = SelectField('Learning Potential', choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ], validators=[DataRequired(message='Please rate learning potential')])
    
    tutor_comments = TextAreaField('Tutor Comments', validators=[
        Optional(),
        Length(max=1000, message='Comments must be less than 1000 characters')
    ])
    
    # Follow-up actions
    recommended_next_steps = TextAreaField('Recommended Next Steps', validators=[
        Optional(),
        Length(max=1000, message='Next steps must be less than 1000 characters')
    ])
    
    suggested_course_level = SelectField('Suggested Course Level', choices=[
        ('', 'Select level'),
        ('Beginner', 'Beginner'),
        ('Elementary', 'Elementary'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert')
    ])
    
    suggested_focus_areas = TextAreaField('Suggested Focus Areas', validators=[
        Optional(),
        Length(max=1000, message='Focus areas must be less than 1000 characters')
    ])
    
    submit = SubmitField('Submit Feedback')


class DemoMaterialForm(FlaskForm):
    """Form for adding demo materials"""
    title = StringField('Material Title', validators=[
        DataRequired(message='Material title is required'),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500, message='Description must be less than 500 characters')
    ])
    
    material_type = SelectField('Material Type', choices=[
        ('Document', 'Document'),
        ('Video', 'Video'),
        ('Presentation', 'Presentation'),
        ('Link', 'Link'),
        ('Assignment', 'Assignment')
    ], validators=[DataRequired(message='Please select a material type')])
    
    file_url = URLField('File URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL')
    ])
    
    file_name = StringField('File Name', validators=[
        Optional(),
        Length(max=200, message='File name must be less than 200 characters')
    ])
    
    is_required = BooleanField('Required Material')
    order = IntegerField('Display Order', validators=[
        DataRequired(message='Display order is required'),
        NumberRange(min=0, max=100, message='Order must be between 0 and 100')
    ], default=0)
    
    student_accessible = BooleanField('Student Can Access', default=True)
    accessible_before_demo = BooleanField('Accessible Before Demo', default=True)
    accessible_after_demo = BooleanField('Accessible After Demo', default=True)
    
    submit = SubmitField('Add Material')


class DemoFollowUpForm(FlaskForm):
    """Form for demo follow-up activities"""
    follow_up_type = SelectField('Follow-up Type', choices=[
        ('Email', 'Email'),
        ('Phone', 'Phone'),
        ('SMS', 'SMS'),
        ('Meeting', 'Meeting')
    ], validators=[DataRequired(message='Please select a follow-up type')])
    
    title = StringField('Follow-up Title', validators=[
        DataRequired(message='Follow-up title is required'),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=1000, message='Description must be less than 1000 characters')
    ])
    
    scheduled_for = DateTimeField('Scheduled For', validators=[
        DataRequired(message='Schedule date and time is required')
    ], format='%Y-%m-%d %H:%M')
    
    assigned_to = SelectField('Assigned To', coerce=int, validators=[
        Optional()
    ])
    
    submit = SubmitField('Schedule Follow-up')
    
    def validate_scheduled_for(self, scheduled_for):
        """Validate that follow-up is scheduled for the future"""
        if scheduled_for.data and scheduled_for.data <= datetime.utcnow():
            raise ValidationError('Follow-up must be scheduled for a future time')


class DemoTemplateForm(FlaskForm):
    """Form for creating demo templates"""
    name = StringField('Template Name', validators=[
        DataRequired(message='Template name is required'),
        Length(min=3, max=100, message='Name must be between 3 and 100 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500, message='Description must be less than 500 characters')
    ])
    
    default_duration = IntegerField('Default Duration (minutes)', validators=[
        DataRequired(message='Default duration is required'),
        NumberRange(min=15, max=180, message='Duration must be between 15 and 180 minutes')
    ], default=30)
    
    default_platform = SelectField('Default Platform', choices=[
        ('Zoom', 'Zoom'),
        ('Google Meet', 'Google Meet'),
        ('Microsoft Teams', 'Microsoft Teams'),
        ('Custom', 'Custom')
    ], validators=[DataRequired(message='Please select a platform')])
    
    agenda = CKEditorField('Demo Agenda', validators=[
        Optional(),
        Length(max=2000, message='Agenda must be less than 2000 characters')
    ])
    
    objectives = TextAreaField('Learning Objectives', validators=[
        Optional(),
        Length(max=1000, message='Objectives must be less than 1000 characters')
    ])
    
    materials_required = TextAreaField('Required Materials', validators=[
        Optional(),
        Length(max=1000, message='Materials must be less than 1000 characters')
    ])
    
    welcome_message = TextAreaField('Welcome Message', validators=[
        Optional(),
        Length(max=1000, message='Welcome message must be less than 1000 characters')
    ])
    
    introduction_script = CKEditorField('Introduction Script', validators=[
        Optional(),
        Length(max=2000, message='Introduction script must be less than 2000 characters')
    ])
    
    closing_script = CKEditorField('Closing Script', validators=[
        Optional(),
        Length(max=2000, message='Closing script must be less than 2000 characters')
    ])
    
    is_public = BooleanField('Make Template Public')
    
    submit = SubmitField('Save Template')


class DemoSearchForm(FlaskForm):
    """Form for searching demo classes"""
    query = StringField('Search', validators=[
        Optional(),
        Length(max=100, message='Search query must be less than 100 characters')
    ])
    
    status = SelectField('Status', choices=[
        ('', 'All Status'),
        ('Requested', 'Requested'),
        ('Confirmed', 'Confirmed'),
        ('Scheduled', 'Scheduled'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('No-Show', 'No-Show')
    ], default='')
    
    conversion_status = SelectField('Conversion Status', choices=[
        ('', 'All Conversion Status'),
        ('Not_Converted', 'Not Converted'),
        ('Interested', 'Interested'),
        ('Enrolled', 'Enrolled'),
        ('Not_Interested', 'Not Interested')
    ], default='')
    
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    
    submit = SubmitField('Search')


class DemoRescheduleForm(FlaskForm):
    """Form for rescheduling demo classes"""
    new_scheduled_time = DateTimeField('New Scheduled Time', validators=[
        DataRequired(message='New scheduled time is required')
    ], format='%Y-%m-%d %H:%M')
    
    new_duration_minutes = IntegerField('New Duration (minutes)', validators=[
        DataRequired(message='Duration is required'),
        NumberRange(min=15, max=180, message='Duration must be between 15 and 180 minutes')
    ])
    
    reason = TextAreaField('Rescheduling Reason', validators=[
        DataRequired(message='Please provide a reason for rescheduling'),
        Length(max=500, message='Reason must be less than 500 characters')
    ])
    
    notify_student = BooleanField('Notify Student', default=True)
    
    submit = SubmitField('Reschedule Demo')
    
    def validate_new_scheduled_time(self, new_scheduled_time):
        """Validate that new scheduled time is in the future"""
        if new_scheduled_time.data and new_scheduled_time.data <= datetime.utcnow():
            raise ValidationError('Demo class must be rescheduled for a future time')


class DemoConversionForm(FlaskForm):
    """Form for tracking demo conversions"""
    conversion_status = SelectField('Conversion Status', choices=[
        ('Not_Converted', 'Not Converted'),
        ('Interested', 'Interested'),
        ('Enrolled', 'Enrolled'),
        ('Not_Interested', 'Not Interested')
    ], validators=[DataRequired(message='Please select conversion status')])
    
    conversion_notes = TextAreaField('Conversion Notes', validators=[
        Optional(),
        Length(max=1000, message='Conversion notes must be less than 1000 characters')
    ])
    
    follow_up_required = BooleanField('Follow-up Required', default=True)
    follow_up_date = DateField('Follow-up Date', validators=[
        Optional()
    ])
    
    submit = SubmitField('Update Conversion Status')
    
    def validate_follow_up_date(self, follow_up_date):
        """Validate that follow-up date is in the future if required"""
        if follow_up_date.data and self.follow_up_required.data:
            if follow_up_date.data <= datetime.utcnow().date():
                raise ValidationError('Follow-up date must be in the future')