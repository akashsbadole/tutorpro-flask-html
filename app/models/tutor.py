from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models.user import User

class TutorProfile(db.Model):
    """
    Tutor-specific profile information
    """
    __tablename__ = 'tutor_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    hourly_rate = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(10), default='USD')
    video_intro_url = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    total_students = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship back to User
    user = db.relationship('User', backref=db.backref('tutor_profile', uselist=False))
    
    def __repr__(self):
        return f'<TutorProfile {self.user.email}>'