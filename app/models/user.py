from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    """
    User model for authentication and role-based access control
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('Learner', 'Tutor', 'Admin', name='user_roles'), nullable=False, default='Learner')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    user_profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    learner_profile = db.relationship('LearnerProfile', backref='learner_user', uselist=False, cascade='all, delete-orphan')
    email_notification_preferences = db.relationship('EmailNotificationPreference', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def __init__(self, email, password, role='Learner'):
        self.email = email
        self.set_password(password)
        self.role = role
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'Admin'
    
    def is_tutor(self):
        """Check if user is a tutor"""
        return self.role == 'Tutor'
    
    def is_learner(self):
        """Check if user is a learner"""
        return self.role == 'Learner'
    
    def __repr__(self):
        return f'<User {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


class UserProfile(db.Model):
    """
    Extended user profile information
    """
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    timezone = db.Column(db.String(50), default='UTC')
    avatar_url = db.Column(db.String(255))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def full_name(self):
        """Return the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.user.email.split('@')[0]
    
    def __repr__(self):
        return f'<UserProfile {self.full_name}>'


# LearnerProfile is now defined in app/models/student.py