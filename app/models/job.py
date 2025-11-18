from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.course import Subject


class JobPost(db.Model):
    """
    Model for job postings
    """
    __tablename__ = 'job_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    budget_range_min = db.Column(db.Numeric(10, 2))
    budget_range_max = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(10), default='USD')
    location = db.Column(db.String(100))  # Can be 'Remote' or specific location
    is_remote = db.Column(db.Boolean, default=False)
    work_type = db.Column(db.Enum('Full-time', 'Part-time', 'Contract', 'Freelance', name='work_types'), 
                         nullable=False)
    experience_level = db.Column(db.Enum('Entry', 'Mid', 'Senior', name='experience_levels'), 
                                nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.Enum('Open', 'Closed', 'Filled', name='job_statuses'), 
                      nullable=False, default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    poster = db.relationship('User', foreign_keys=[poster_id], backref='job_posts')
    subject = db.relationship('Subject', backref='job_posts')
    applications = db.relationship('JobApplication', backref='job_post', lazy=True, cascade='all, delete-orphan')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_job_status', 'status'),
        db.Index('idx_job_subject', 'subject_id'),
        db.Index('idx_job_poster', 'poster_id'),
        db.Index('idx_job_active', 'is_active'),
    )
    
    def __repr__(self):
        return f'<JobPost {self.title}>'
    
    @property
    def is_expired(self):
        """Check if job posting has expired"""
        return datetime.utcnow() > self.deadline
    
    @property
    def is_open(self):
        """Check if job is still open for applications"""
        return self.status == 'Open' and not self.is_expired
    
    def close_job(self):
        """Mark job as closed"""
        self.status = 'Closed'
        self.is_active = False
        db.session.commit()
    
    def fill_job(self):
        """Mark job as filled"""
        self.status = 'Filled'
        self.is_active = False
        db.session.commit()


class JobApplication(db.Model):
    """
    Model for applications to job postings
    """
    __tablename__ = 'job_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posts.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cover_letter = db.Column(db.Text)
    proposed_rate = db.Column(db.Numeric(10, 2))
    resume_url = db.Column(db.String(255))
    status = db.Column(db.Enum('Applied', 'Under Review', 'Interview Scheduled', 'Rejected', 'Hired', 
                               'Withdrawn', name='application_statuses'), 
                      nullable=False, default='Applied')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)  # Internal notes for recruiters
    
    # Relationships
    applicant = db.relationship('User', foreign_keys=[applicant_id], backref='job_applications')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_application_job', 'job_id'),
        db.Index('idx_application_applicant', 'applicant_id'),
        db.Index('idx_application_status', 'status'),
    )
    
    def __repr__(self):
        return f'<JobApplication {self.applicant.email} for {self.job_post.title}>'
    
    def move_to_next_stage(self):
        """Move application to next stage in the hiring process"""
        if self.status == 'Applied':
            self.status = 'Under Review'
        elif self.status == 'Under Review':
            self.status = 'Interview Scheduled'
        elif self.status == 'Interview Scheduled':
            self.status = 'Hired'
        db.session.commit()
    
    def reject_application(self):
        """Reject the application"""
        self.status = 'Rejected'
        db.session.commit()
    
    def withdraw_application(self):
        """Allow applicant to withdraw their application"""
        self.status = 'Withdrawn'
        db.session.commit()


class JobApplicationNote(db.Model):
    """
    Model for tracking notes on job applications
    """
    __tablename__ = 'job_application_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('job_applications.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', foreign_keys=[author_id])
    
    def __repr__(self):
        return f'<JobApplicationNote for Application {self.application_id}>'


class JobSaved(db.Model):
    """
    Model for users saving job postings
    """
    __tablename__ = 'job_saved'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posts.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='saved_jobs')
    job = db.relationship('JobPost', backref='saved_by_users')
    
    # Unique constraint to prevent duplicate saves
    __table_args__ = (db.UniqueConstraint('user_id', 'job_id', name='unique_user_job_save'),)
    
    def __repr__(self):
        return f'<JobSaved {self.user.email} saved {self.job.title}>'


class JobView(db.Model):
    """
    Model for tracking job views
    """
    __tablename__ = 'job_views'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posts.id'), nullable=False)
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for anonymous views
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # Store IP for anonymous views
    
    # Relationships
    job_post = db.relationship('JobPost', backref='views')
    viewer = db.relationship('User', foreign_keys=[viewer_id])
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_job_view_job', 'job_id'),
        db.Index('idx_job_view_viewer', 'viewer_id'),
    )
    
    def __repr__(self):
        viewer = self.viewer.email if self.viewer else 'Anonymous'
        return f'<JobView {viewer} viewed {self.job_post.title}>'