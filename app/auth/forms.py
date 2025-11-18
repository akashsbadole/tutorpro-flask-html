from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    """
    Form for user login
    """
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """
    Form for user registration
    """
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address'),
        Length(min=6, max=120, message='Email must be between 6 and 120 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('I am a', choices=[
        ('Learner', 'Learner - Looking for a tutor'),
        ('Tutor', 'Tutor - Looking to teach')
    ], validators=[DataRequired(message='Please select a role')])
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required'),
        Length(min=2, max=50, message='First name must be between 2 and 50 characters')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required'),
        Length(min=2, max=50, message='Last name must be between 2 and 50 characters')
    ])
    submit = SubmitField('Create Account')

    def validate_email(self, email):
        """
        Custom validator to check if email already exists
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered. Please use a different email or log in.')


class ChangePasswordForm(FlaskForm):
    """
    Form for changing user password
    """
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')

    def __init__(self, user, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_current_password(self, current_password):
        """
        Custom validator to check if current password is correct
        """
        if not self.user.check_password(current_password.data):
            raise ValidationError('Current password is incorrect. Please try again.')


class ForgotPasswordForm(FlaskForm):
    """
    Form for password reset request
    """
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    """
    Form for password reset
    """
    password = PasswordField('New Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')