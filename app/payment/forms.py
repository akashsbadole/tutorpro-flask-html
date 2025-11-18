from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, TextAreaField, HiddenField, BooleanField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Length, Regexp, Optional, Email
from wtforms.widgets import TextArea
import re

class PaymentMethodForm(FlaskForm):
    """Form for adding/editing payment methods"""
    payment_type = SelectField('Payment Method', 
                               choices=[('UPI', 'UPI'), ('PayPal', 'PayPal'), 
                                       ('Credit Card', 'Credit Card'), ('Debit Card', 'Debit Card')],
                               validators=[DataRequired()])
    method_details = StringField('Payment Details', validators=[
        DataRequired(),
        Length(min=5, max=255, message='Payment details must be between 5 and 255 characters')
    ])
    is_default = BooleanField('Set as Default Payment Method')

class UPIPaymentForm(FlaskForm):
    """Form for UPI payments"""
    upi_id = StringField('UPI ID', validators=[
        DataRequired(),
        Regexp(r'^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$', 
               message='Invalid UPI ID format (e.g., username@upi)')
    ])
    amount = DecimalField('Amount', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Amount must be greater than 0')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    
    def validate_upi_id(self, field):
        """Custom UPI ID validation"""
        upi_id = field.data
        if not re.match(r'^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$', upi_id):
            raise ValueError('Invalid UPI ID format')

class PayPalPaymentForm(FlaskForm):
    """Form for PayPal payments"""
    paypal_email = StringField('PayPal Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    amount = DecimalField('Amount', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Amount must be greater than 0')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    is_subscription = BooleanField('Make this a recurring payment')
    subscription_interval = SelectField('Subscription Interval', 
                                       choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')],
                                       validators=[Optional()])

class PaymentForm(FlaskForm):
    """General payment form for processing payments"""
    booking_id = HiddenField('Booking ID', validators=[DataRequired()])
    payment_method_id = SelectField('Payment Method', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Amount must be greater than 0')
    ])
    currency = SelectField('Currency', choices=[('USD', 'USD'), ('INR', 'INR')], default='USD')
    description = TextAreaField('Description', validators=[Optional()])

class RefundForm(FlaskForm):
    """Form for processing refunds"""
    payment_id = HiddenField('Payment ID', validators=[DataRequired()])
    refund_amount = DecimalField('Refund Amount', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Refund amount must be greater than 0')
    ])
    refund_reason = TextAreaField('Refund Reason', validators=[
        DataRequired(),
        Length(min=10, max=500, message='Refund reason must be between 10 and 500 characters')
    ])

class PayoutRequestForm(FlaskForm):
    """Form for tutor payout requests"""
    amount = DecimalField('Payout Amount', validators=[
        DataRequired(),
        NumberRange(min=1.00, message='Minimum payout amount is $1.00')
    ])
    payout_method = SelectField('Payout Method', 
                               choices=[('Bank Transfer', 'Bank Transfer'), 
                                       ('UPI', 'UPI'), 
                                       ('PayPal', 'PayPal')],
                               validators=[DataRequired()])
    payout_details = StringField('Payout Details', validators=[
        DataRequired(),
        Length(min=5, max=255, message='Payout details must be between 5 and 255 characters')
    ])
    notes = TextAreaField('Notes', validators=[Optional()])

class PayoutMethodForm(FlaskForm):
    """Form for adding/editing payout methods"""
    method_type = SelectField('Method Type', 
                             choices=[('Bank Transfer', 'Bank Transfer'), 
                                     ('UPI', 'UPI'), 
                                     ('PayPal', 'PayPal')],
                             validators=[DataRequired()])
    account_holder_name = StringField('Account Holder Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Account holder name must be between 2 and 100 characters')
    ])
    account_details = StringField('Account Details', validators=[
        DataRequired(),
        Length(min=5, max=255, message='Account details must be between 5 and 255 characters')
    ])
    bank_name = StringField('Bank Name', validators=[Optional()])
    ifsc_code = StringField('IFSC Code', validators=[
        Optional(),
        Regexp(r'^[A-Z]{4}0[A-Z0-9]{6}$', message='Invalid IFSC code format')
    ])
    is_default = BooleanField('Set as Default Payout Method')

class PaymentSearchForm(FlaskForm):
    """Form for searching payment history"""
    search_query = StringField('Search', validators=[Optional()])
    status = SelectField('Status', 
                         choices=[('', 'All'), ('Pending', 'Pending'), 
                                 ('Completed', 'Completed'), ('Failed', 'Failed'), 
                                 ('Refunded', 'Refunded')],
                         validators=[Optional()])
    payment_method = SelectField('Payment Method', 
                                choices=[('', 'All'), ('UPI', 'UPI'), 
                                        ('PayPal', 'PayPal'), 
                                        ('Credit Card', 'Credit Card'), 
                                        ('Debit Card', 'Debit Card')],
                                validators=[Optional()])
    date_from = StringField('From Date', validators=[Optional()])
    date_to = StringField('To Date', validators=[Optional()])
    amount_min = DecimalField('Min Amount', validators=[Optional()])
    amount_max = DecimalField('Max Amount', validators=[Optional()])

class AnalyticsFilterForm(FlaskForm):
    """Form for filtering payment analytics"""
    period = SelectField('Period', 
                         choices=[('7', 'Last 7 Days'), ('30', 'Last 30 Days'), 
                                 ('90', 'Last 90 Days'), ('365', 'Last Year')],
                         default='30')
    payment_method = SelectField('Payment Method', 
                                choices=[('', 'All Methods'), ('UPI', 'UPI'), 
                                        ('PayPal', 'PayPal'), 
                                        ('Credit Card', 'Credit Card'), 
                                        ('Debit Card', 'Debit Card')],
                                validators=[Optional()])
    currency = SelectField('Currency', 
                          choices=[('', 'All Currencies'), ('USD', 'USD'), ('INR', 'INR')],
                          validators=[Optional()])