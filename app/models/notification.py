from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models.user import User


class Notification(db.Model):
    """
    Model for system notifications
    """
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.Enum('Booking', 'Payment', 'Review', 'Message', 'System', 'Job', 
                            'Assignment', name='notification_types'), 
                    nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_priority = db.Column(db.Boolean, default=False)
    metadata_json = db.Column(db.JSON)  # Additional data related to the notification
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_notification_user', 'user_id'),
        db.Index('idx_notification_type', 'type'),
        db.Index('idx_notification_read', 'is_read'),
        db.Index('idx_notification_priority', 'is_priority'),
    )
    
    def __repr__(self):
        return f'<Notification {self.type} for {self.user.email}>'
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_unread(self):
        """Mark notification as unread"""
        self.is_read = False
        self.read_at = None
        db.session.commit()


class EmailLog(db.Model):
    """
    Model for email tracking
    """
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email_type = db.Column(db.Enum('Welcome', 'Password Reset', 'Booking Confirmation', 
                                   'Booking Reminder', 'Payment Receipt', 'Review Request',
                                   'Newsletter', 'Job Alert', name='email_types'), 
                          nullable=False)
    recipient_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    template = db.Column(db.String(100), nullable=False)  # Template used
    status = db.Column(db.Enum('Pending', 'Sent', 'Failed', name='email_statuses'), 
                      nullable=False, default='Pending')
    error_message = db.Column(db.Text)  # Error message if email failed
    sent_at = db.Column(db.DateTime)
    opened_at = db.Column(db.DateTime)  # Track when email was opened
    clicked_at = db.Column(db.DateTime)  # Track when link was clicked
    metadata_json = db.Column(db.JSON)  # Additional data related to the email
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='email_logs')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_email_log_user', 'user_id'),
        db.Index('idx_email_log_type', 'email_type'),
        db.Index('idx_email_log_status', 'status'),
    )
    
    def __repr__(self):
        return f'<EmailLog {self.email_type} to {self.recipient_email}>'
    
    def mark_as_sent(self):
        """Mark email as sent"""
        self.status = 'Sent'
        self.sent_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_failed(self, error_message):
        """Mark email as failed"""
        self.status = 'Failed'
        self.error_message = error_message
        db.session.commit()
    
    def mark_as_opened(self):
        """Mark email as opened"""
        self.opened_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_clicked(self):
        """Mark email as clicked"""
        self.clicked_at = datetime.utcnow()
        db.session.commit()


class NotificationPreference(db.Model):
    """
    Model for user notification preferences
    """
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Email notifications
    email_booking = db.Column(db.Boolean, default=True)
    email_payment = db.Column(db.Boolean, default=True)
    email_review = db.Column(db.Boolean, default=True)
    email_message = db.Column(db.Boolean, default=True)
    email_system = db.Column(db.Boolean, default=True)
    email_job = db.Column(db.Boolean, default=True)
    email_assignment = db.Column(db.Boolean, default=True)
    
    # In-app notifications
    in_app_booking = db.Column(db.Boolean, default=True)
    in_app_payment = db.Column(db.Boolean, default=True)
    in_app_review = db.Column(db.Boolean, default=True)
    in_app_message = db.Column(db.Boolean, default=True)
    in_app_system = db.Column(db.Boolean, default=True)
    in_app_job = db.Column(db.Boolean, default=True)
    in_app_assignment = db.Column(db.Boolean, default=True)
    
    # Push notifications
    push_booking = db.Column(db.Boolean, default=True)
    push_payment = db.Column(db.Boolean, default=True)
    push_review = db.Column(db.Boolean, default=True)
    push_message = db.Column(db.Boolean, default=True)
    push_system = db.Column(db.Boolean, default=False)  # Usually disabled by default
    push_job = db.Column(db.Boolean, default=True)
    push_assignment = db.Column(db.Boolean, default=True)
    
    # Marketing communications
    marketing_email = db.Column(db.Boolean, default=False)
    marketing_push = db.Column(db.Boolean, default=False)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='notification_preferences')
    
    def __repr__(self):
        return f'<NotificationPreference for {self.user.email}>'
    
    def update_preferences(self, **kwargs):
        """Update notification preferences"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_email_preferences(self):
        """Get all email notification preferences"""
        return {
            'booking': self.email_booking,
            'payment': self.email_payment,
            'review': self.email_review,
            'message': self.email_message,
            'system': self.email_system,
            'job': self.email_job,
            'assignment': self.email_assignment,
        }
    
    def get_in_app_preferences(self):
        """Get all in-app notification preferences"""
        return {
            'booking': self.in_app_booking,
            'payment': self.in_app_payment,
            'review': self.in_app_review,
            'message': self.in_app_message,
            'system': self.in_app_system,
            'job': self.in_app_job,
            'assignment': self.in_app_assignment,
        }
    
    def get_push_preferences(self):
        """Get all push notification preferences"""
        return {
            'booking': self.push_booking,
            'payment': self.push_payment,
            'review': self.push_review,
            'message': self.push_message,
            'system': self.push_system,
            'job': self.push_job,
            'assignment': self.push_assignment,
        }


class NotificationTemplate(db.Model):
    """
    Model for notification templates
    """
    __tablename__ = 'notification_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.Enum('Booking', 'Payment', 'Review', 'Message', 'System', 'Job', 
                            'Assignment', name='template_types'), 
                    nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    text_content = db.Column(db.Text, nullable=False)
    variables = db.Column(db.JSON)  # List of variables that can be used in the template
    metadata_json = db.Column(db.JSON)  # Additional metadata for the template
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NotificationTemplate {self.name}>'
    
    def render_template(self, context):
        """Render template with provided context"""
        # This is a simplified version - in production you'd use a proper template engine
        rendered_html = self.html_content
        rendered_text = self.text_content
        
        # Replace variables with actual values
        if self.variables:
            for var in self.variables:
                placeholder = f'{{{{{var}}}}}'
                if var in context:
                    rendered_html = rendered_html.replace(placeholder, str(context[var]))
                    rendered_text = rendered_text.replace(placeholder, str(context[var]))
        
        return {
            'subject': self.subject,
            'html_content': rendered_html,
            'text_content': rendered_text
        }