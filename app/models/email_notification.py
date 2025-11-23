from datetime import datetime, timedelta
from app import db

class EmailNotification(db.Model):
    """
    Email notification system for various user actions
    """
    __tablename__ = 'email_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Notification details
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    notification_type = db.Column(db.Enum(
        'Booking Confirmation',
        'Booking Reminder',
        'Payment Confirmation',
        'Payment Reminder',
        'Course Enrollment',
        'Assignment Due',
        'Session Reminder',
        'Review Request',
        'Profile Update',
        'Marketing',
        'System Update',
        'Security Alert',
        name='notification_types'
    ), nullable=False, index=True)
    
    # Content
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    html_content = db.Column(db.Text)  # HTML email content
    
    # Status and tracking
    status = db.Column(db.Enum(
        'Pending',
        'Sent',
        'Delivered',
        'Failed',
        'Bounced',
        'Opened',
        'Clicked',
        name='notification_statuses'
    ), nullable=False, default='Pending', index=True)
    
    # Scheduling
    scheduled_at = db.Column(db.DateTime)  # When to send
    sent_at = db.Column(db.DateTime)  # When actually sent
    delivered_at = db.Column(db.DateTime)  # When delivered
    opened_at = db.Column(db.DateTime)  # When opened
    clicked_at = db.Column(db.DateTime)  # When clicked
    
    # Delivery tracking
    delivery_attempts = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text)  # Last delivery error
    
    # Engagement tracking
    open_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    
    # Email details
    from_email = db.Column(db.String(255))  # Sender email
    from_name = db.Column(db.String(200))  # Sender name
    reply_to = db.Column(db.String(255))  # Reply-to email for threads
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='email_notifications')
    template = db.relationship('EmailTemplate', backref='notifications')
    
    def __repr__(self):
        return f'<EmailNotification {self.id}: {self.notification_type}>'
    
    def is_delivered(self):
        """Check if notification was delivered successfully"""
        return self.status == 'Delivered'
    
    def is_pending(self):
        """Check if notification is still pending"""
        return self.status == 'Pending'
    
    def is_failed(self):
        """Check if notification failed"""
        return self.status == 'Failed'
    
    def can_retry(self):
        """Check if notification can be retried"""
        if self.is_delivered() or self.is_failed():
            return False
        return self.delivery_attempts < 3 and self.last_error != 'Permanent failure'
    
    def get_time_until_send(self):
        """Get time until scheduled send"""
        if self.scheduled_at and self.scheduled_at > datetime.utcnow():
            return self.scheduled_at - datetime.utcnow()
        return timedelta(0)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'delivery_attempts': self.delivery_attempts,
            'last_error': self.last_error,
            'open_count': self.open_count,
            'click_count': self.click_count,
            'from_email': self.from_email,
            'from_name': self.from_name,
            'reply_to': self.reply_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_delivered': self.is_delivered(),
            'is_pending': self.is_pending(),
            'is_failed': self.is_failed(),
            'can_retry': self.can_retry(),
            'time_until_send': self.get_time_until_send().total_seconds() if self.get_time_until_send() else None
        }


class EmailTemplate(db.Model):
    """
    Email templates for different notification types
    """
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template details
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    template_type = db.Column(db.Enum(
        'Booking Confirmation',
        'Booking Reminder',
        'Payment Confirmation',
        'Payment Reminder',
        'Course Enrollment',
        'Assignment Due',
        'Session Reminder',
        'Review Request',
        'Profile Update',
        'Marketing',
        'System Update',
        'Security Alert',
        name='template_types'
    ), nullable=False, unique=True)
    
    # Template content
    subject_template = db.Column(db.String(200))  # Subject template with placeholders
    body_template = db.Column(db.Text, nullable=False)  # HTML body template
    text_template = db.Column(db.Text)  # Plain text template
    
    # Template variables
    variables = db.Column(db.Text)  # JSON object of available variables
    
    # Design settings
    header_style = db.Column(db.Enum(
        'Professional',
        'Friendly',
        'Modern',
        'Minimal',
        name='header_styles'
    ), nullable=False, default='Professional')
    
    footer_style = db.Column(db.Enum(
        'Professional',
        'Friendly',
        'Modern',
        'Minimal',
        name='footer_styles'
    ), nullable=False, default='Professional')
    
    # Default settings
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailTemplate {self.id}: {self.name}>'
    
    def render_template(self, variables=None):
        """Render template with provided variables"""
        import re
        from jinja2 import Template
        
        if not variables:
            variables = {}
        
        # Choose appropriate template
        if self.text_template and not self.body_template:
            template_content = self.text_template
        else:
            template_content = self.body_template
        
        template = Template(template_content)
        return template.render(**variables)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_type': self.template_type,
            'subject_template': self.subject_template,
            'body_template': self.body_template,
            'text_template': self.text_template,
            'variables': self.variables,
            'header_style': self.header_style,
            'footer_style': self.footer_style,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class EmailNotificationPreference(db.Model):
    """
    User notification preferences for email notifications
    """
    __tablename__ = 'email_notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User and preferences
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Email preferences
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=False)
    push_enabled = db.Column(db.Boolean, default=True)
    
    # Notification type preferences
    booking_notifications = db.Column(db.Boolean, default=True)
    payment_notifications = db.Column(db.Boolean, default=True)
    course_notifications = db.Column(db.Boolean, default=True)
    review_notifications = db.Column(db.Boolean, default=True)
    marketing_notifications = db.Column(db.Boolean, default=False)
    system_notifications = db.Column(db.Boolean, default=True)
    
    # Frequency settings
    email_frequency = db.Column(db.Enum(
        'Immediate',
        'Hourly',
        'Daily',
        'Weekly',
        'Monthly',
        name='notification_frequencies'
    ), nullable=False, default='Immediate')
    
    # Quiet hours
    quiet_hours_start = db.Column(db.Integer, default=22)  # 10 PM
    quiet_hours_end = db.Column(db.Integer, default=8)  # 8 AM
    
    # Time preferences
    timezone = db.Column(db.String(50), default='UTC')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # user = db.relationship('User', backref='email_notification_preferences_list')
    
    def __repr__(self):
        return f'<NotificationPreference {self.id}: {self.user_id}>'
    
    def is_quiet_hours(self, hour=None):
        """Check if current hour is within quiet hours"""
        if hour is None:
            hour = datetime.utcnow().hour
        
        if self.quiet_hours_start <= self.quiet_hours_end:
            return False
        elif self.quiet_hours_start > self.quiet_hours_end:
            return False
        else:
            return self.quiet_hours_start <= hour < self.quiet_hours_end
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_enabled': self.email_enabled,
            'sms_enabled': self.sms_enabled,
            'push_enabled': self.push_enabled,
            'booking_notifications': self.booking_notifications,
            'payment_notifications': self.payment_notifications,
            'course_notifications': self.course_notifications,
            'review_notifications': self.review_notifications,
            'marketing_notifications': self.marketing_notifications,
            'system_notifications': self.system_notifications,
            'email_frequency': self.email_frequency,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_quiet_hours': self.is_quiet_hours()
        }