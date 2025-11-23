"""
Student Models for TutorPro Marketplace
Enhanced student profiles with learning preferences and goals
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum as PyEnum
import json

from app import db

class LearningStyle(PyEnum):
    """Learning style preferences"""
    VISUAL = "Visual"
    AUDITORY = "Auditory"
    KINESTHETIC = "Kinesthetic"
    READING_WRITING = "Reading/Writing"
    MIXED = "Mixed"

class ExperienceLevel(PyEnum):
    """Student experience levels"""
    BEGINNER = "Beginner"
    ELEMENTARY = "Elementary"
    INTERMEDIATE = "Intermediate"
    UPPER_INTERMEDIATE = "Upper Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"

class LearningGoal(PyEnum):
    """Types of learning goals"""
    ACADEMIC_IMPROVEMENT = "Academic Improvement"
    SKILL_DEVELOPMENT = "Skill Development"
    CAREER_ADVANCEMENT = "Career Advancement"
    PERSONAL_INTEREST = "Personal Interest"
    EXAM_PREPARATION = "Exam Preparation"
    LANGUAGE_FLUENCY = "Language Fluency"
    CERTIFICATION = "Certification"
    HOBBY_DEVELOPMENT = "Hobby Development"

class LearnerProfile(db.Model):
    """Enhanced learner profile with detailed preferences"""
    __tablename__ = 'learner_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Basic Information
    bio = Column(Text)
    profile_image_url = Column(String(500))
    date_of_birth = Column(DateTime)
    timezone = Column(String(50), default='UTC')
    
    # Learning Preferences
    learning_style = Column(Enum(LearningStyle), default=LearningStyle.VISUAL)
    experience_level = Column(Enum(ExperienceLevel), default=ExperienceLevel.BEGINNER)
    preferred_languages = Column(JSON)  # List of preferred languages
    preferred_tutor_gender = Column(String(10), default='Any')  # Male, Female, Any
    
    # Learning Goals and Interests
    learning_goals = Column(JSON)  # List of learning goals
    preferred_subjects = Column(JSON)  # List of preferred subject IDs
    subject_interests = Column(JSON)  # Detailed subject interests with priorities
    learning_objectives = Column(Text)  # Free text description of objectives
    
    # Availability and Scheduling
    availability = Column(JSON)  # Preferred days and times
    preferred_session_duration = Column(Integer, default=60)  # Minutes
    preferred_session_frequency = Column(String(20), default='Weekly')  # Daily, Weekly, Bi-weekly, Monthly
    flexible_scheduling = Column(Boolean, default=True)
    
    # Budget Preferences
    budget_range_min = Column(Float)  # Minimum hourly rate
    budget_range_max = Column(Float)  # Maximum hourly rate
    preferred_payment_method = Column(String(50))  # PayPal, UPI, Credit Card, etc.
    
    # Location Preferences
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    preferred_teaching_modes = Column(JSON)  # Online, Offline, Hybrid
    max_travel_distance = Column(Integer)  # Kilometers for offline sessions
    
    # Communication Preferences
    preferred_contact_method = Column(String(20), default='email')  # email, phone, chat
    notification_preferences = Column(JSON)  # Email, SMS, Push notifications settings
    communication_frequency = Column(String(20), default='moderate')  # minimal, moderate, frequent
    
    # Privacy Settings
    profile_visibility = Column(String(20), default='public')  # public, tutors_only, private
    show_real_name = Column(Boolean, default=True)
    allow_contact_requests = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    profile_completion_percentage = Column(Float, default=0.0)
    
    # Relationships
    user = relationship('User', back_populates='learner_profile')
    learning_goals_rel = relationship('StudentLearningGoal', back_populates='learner_profile', cascade='all, delete-orphan')
    subject_preferences = relationship('StudentSubjectPreference', back_populates='learner_profile', cascade='all, delete-orphan')
    wishlist_items = relationship('StudentWishlist', back_populates='learner_profile', cascade='all, delete-orphan')
    learning_progress = relationship('LearningProgress', back_populates='learner_profile', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<LearnerProfile {self.user_id}>'
    
    def to_dict(self, include_sensitive=False):
        """Convert learner profile to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'bio': self.bio,
            'profile_image_url': self.profile_image_url,
            'timezone': self.timezone,
            'learning_style': self.learning_style.value if self.learning_style else None,
            'experience_level': self.experience_level.value if self.experience_level else None,
            'preferred_languages': self.preferred_languages or [],
            'preferred_tutor_gender': self.preferred_tutor_gender,
            'learning_goals': self.learning_goals or [],
            'preferred_subjects': self.preferred_subjects or [],
            'subject_interests': self.subject_interests or [],
            'learning_objectives': self.learning_objectives,
            'availability': self.availability or [],
            'preferred_session_duration': self.preferred_session_duration,
            'preferred_session_frequency': self.preferred_session_frequency,
            'flexible_scheduling': self.flexible_scheduling,
            'budget_range_min': self.budget_range_min,
            'budget_range_max': self.budget_range_max,
            'preferred_payment_method': self.preferred_payment_method,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'preferred_teaching_modes': self.preferred_teaching_modes or ['online'],
            'max_travel_distance': self.max_travel_distance,
            'preferred_contact_method': self.preferred_contact_method,
            'notification_preferences': self.notification_preferences or {},
            'communication_frequency': self.communication_frequency,
            'profile_visibility': self.profile_visibility,
            'show_real_name': self.show_real_name,
            'allow_contact_requests': self.allow_contact_requests,
            'profile_completion_percentage': self.profile_completion_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
        
        if include_sensitive:
            data['date_of_birth'] = self.date_of_birth.isoformat() if self.date_of_birth else None
        
        return data
    
    @hybrid_property
    def age(self):
        """Calculate age from date of birth"""
        if not self.date_of_birth:
            return None
        today = datetime.now(timezone.utc).date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def get_preferred_teaching_modes_list(self):
        """Get list of preferred teaching modes"""
        if isinstance(self.preferred_teaching_modes, str):
            try:
                return json.loads(self.preferred_teaching_modes)
            except:
                return ['online']
        return self.preferred_teaching_modes or ['online']
    
    def get_availability_days(self):
        """Get list of available days"""
        if isinstance(self.availability, str):
            try:
                availability_data = json.loads(self.availability)
                return list(availability_data.keys())
            except:
                return []
        return list(self.availability.keys()) if self.availability else []
    
    def update_profile_completion(self):
        """Update profile completion percentage"""
        fields_to_check = [
            'bio', 'learning_style', 'experience_level', 'learning_goals',
            'preferred_subjects', 'availability', 'city', 'country'
        ]
        
        completed_fields = 0
        for field in fields_to_check:
            value = getattr(self, field)
            if value:
                if isinstance(value, str) and value.strip():
                    completed_fields += 1
                elif isinstance(value, (list, dict)) and value:
                    completed_fields += 1
                elif hasattr(value, 'value'):  # Enum
                    completed_fields += 1
        
        self.profile_completion_percentage = (completed_fields / len(fields_to_check)) * 100
        db.session.commit()

class StudentLearningGoal(db.Model):
    """Detailed learning goals for students"""
    __tablename__ = 'student_learning_goals'
    
    id = Column(Integer, primary_key=True)
    learner_profile_id = Column(Integer, ForeignKey('learner_profiles.id'), nullable=False)
    goal_type = Column(Enum(LearningGoal), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    target_date = Column(DateTime)
    priority = Column(String(10), default='medium')  # high, medium, low
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    learner_profile = relationship('LearnerProfile', back_populates='learning_goals_rel')
    subject = relationship('Subject')
    milestones = relationship('LearningMilestone', back_populates='learning_goal', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StudentLearningGoal {self.title}>'
    
    def to_dict(self):
        """Convert learning goal to dictionary"""
        return {
            'id': self.id,
            'learner_profile_id': self.learner_profile_id,
            'goal_type': self.goal_type.value if self.goal_type else None,
            'subject_id': self.subject_id,
            'title': self.title,
            'description': self.description,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'priority': self.priority,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'subject': self.subject.to_dict() if self.subject else None,
            'milestones': [milestone.to_dict() for milestone in self.milestones]
        }

class StudentSubjectPreference(db.Model):
    """Detailed subject preferences for students"""
    __tablename__ = 'student_subject_preferences'
    
    id = Column(Integer, primary_key=True)
    learner_profile_id = Column(Integer, ForeignKey('learner_profiles.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    priority_level = Column(Integer, default=1)  # 1-5, 5 being highest
    skill_level_current = Column(Enum(ExperienceLevel), default=ExperienceLevel.BEGINNER)
    skill_level_target = Column(Enum(ExperienceLevel))
    learning_intensity = Column(String(20), default='moderate')  # casual, moderate, intensive
    preferred_duration_weeks = Column(Integer)  # Estimated learning duration
    budget_allocation = Column(Float)  # Budget specifically for this subject
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    learner_profile = relationship('LearnerProfile', back_populates='subject_preferences')
    subject = relationship('Subject')
    
    def __repr__(self):
        return f'<StudentSubjectPreference {self.learner_profile_id}:{self.subject_id}>'
    
    def to_dict(self):
        """Convert subject preference to dictionary"""
        return {
            'id': self.id,
            'learner_profile_id': self.learner_profile_id,
            'subject_id': self.subject_id,
            'priority_level': self.priority_level,
            'skill_level_current': self.skill_level_current.value if self.skill_level_current else None,
            'skill_level_target': self.skill_level_target.value if self.skill_level_target else None,
            'learning_intensity': self.learning_intensity,
            'preferred_duration_weeks': self.preferred_duration_weeks,
            'budget_allocation': self.budget_allocation,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'subject': self.subject.to_dict() if self.subject else None
        }

class StudentWishlist(db.Model):
    """Student wishlist for favorite tutors"""
    __tablename__ = 'student_wishlists'
    
    id = Column(Integer, primary_key=True)
    learner_profile_id = Column(Integer, ForeignKey('learner_profiles.id'), nullable=False)
    tutor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    notes = Column(Text)  # Student's notes about why they like this tutor
    priority = Column(String(10), default='medium')  # high, medium, low
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_viewed = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    learner_profile = relationship('LearnerProfile', back_populates='wishlist_items')
    tutor = relationship('User')
    
    def __repr__(self):
        return f'<StudentWishlist {self.learner_profile_id}:{self.tutor_id}>'
    
    def to_dict(self):
        """Convert wishlist item to dictionary"""
        return {
            'id': self.id,
            'learner_profile_id': self.learner_profile_id,
            'tutor_id': self.tutor_id,
            'notes': self.notes,
            'priority': self.priority,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'last_viewed': self.last_viewed.isoformat() if self.last_viewed else None,
            'is_active': self.is_active,
            'tutor': self.tutor.to_dict() if self.tutor else None
        }

class LearningProgress(db.Model):
    """Track student learning progress"""
    __tablename__ = 'learning_progress'
    
    id = Column(Integer, primary_key=True)
    learner_profile_id = Column(Integer, ForeignKey('learner_profiles.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    tutor_id = Column(Integer, ForeignKey('users.id'))
    learning_goal_id = Column(Integer, ForeignKey('student_learning_goals.id'))
    
    # Progress Metrics
    current_level = Column(Enum(ExperienceLevel))
    sessions_completed = Column(Integer, default=0)
    total_hours = Column(Float, default=0.0)
    progress_percentage = Column(Float, default=0.0)
    
    # Assessment Data
    last_assessment_date = Column(DateTime)
    assessment_score = Column(Float)
    improvement_rate = Column(Float)  # Percentage improvement over time
    
    # Feedback and Notes
    tutor_feedback = Column(Text)
    student_notes = Column(Text)
    achievements = Column(JSON)  # List of achievements/milestones
    
    # Metadata
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    learner_profile = relationship('LearnerProfile', back_populates='learning_progress')
    subject = relationship('Subject')
    tutor = relationship('User')
    learning_goal = relationship('StudentLearningGoal')
    progress_entries = relationship('ProgressEntry', back_populates='learning_progress', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<LearningProgress {self.learner_profile_id}:{self.subject_id}>'
    
    def to_dict(self):
        """Convert learning progress to dictionary"""
        return {
            'id': self.id,
            'learner_profile_id': self.learner_profile_id,
            'subject_id': self.subject_id,
            'tutor_id': self.tutor_id,
            'learning_goal_id': self.learning_goal_id,
            'current_level': self.current_level.value if self.current_level else None,
            'sessions_completed': self.sessions_completed,
            'total_hours': self.total_hours,
            'progress_percentage': self.progress_percentage,
            'last_assessment_date': self.last_assessment_date.isoformat() if self.last_assessment_date else None,
            'assessment_score': self.assessment_score,
            'improvement_rate': self.improvement_rate,
            'tutor_feedback': self.tutor_feedback,
            'student_notes': self.student_notes,
            'achievements': self.achievements or [],
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'is_active': self.is_active,
            'subject': self.subject.to_dict() if self.subject else None,
            'tutor': self.tutor.to_dict() if self.tutor else None,
            'learning_goal': self.learning_goal.to_dict() if self.learning_goal else None
        }

class ProgressEntry(db.Model):
    """Individual progress entries for detailed tracking"""
    __tablename__ = 'progress_entries'
    
    id = Column(Integer, primary_key=True)
    learning_progress_id = Column(Integer, ForeignKey('learning_progress.id'), nullable=False)
    
    # Entry Details
    entry_type = Column(String(20), default='session')  # session, assessment, milestone, note
    title = Column(String(200))
    description = Column(Text)
    
    # Progress Data
    progress_value = Column(Float)  # Progress value for this entry
    hours_spent = Column(Float)
    topics_covered = Column(JSON)  # List of topics covered in this entry
    
    # Assessment Data (if applicable)
    score = Column(Float)
    max_score = Column(Float)
    feedback = Column(Text)
    
    # Metadata
    entry_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey('users.id'))  # Student or tutor who created entry
    
    # Relationships
    learning_progress = relationship('LearningProgress', back_populates='progress_entries')
    creator = relationship('User')
    
    def __repr__(self):
        return f'<ProgressEntry {self.id}:{self.entry_type}>'
    
    def to_dict(self):
        """Convert progress entry to dictionary"""
        return {
            'id': self.id,
            'learning_progress_id': self.learning_progress_id,
            'entry_type': self.entry_type,
            'title': self.title,
            'description': self.description,
            'progress_value': self.progress_value,
            'hours_spent': self.hours_spent,
            'topics_covered': self.topics_covered or [],
            'score': self.score,
            'max_score': self.max_score,
            'feedback': self.feedback,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'created_by': self.created_by,
            'creator': self.creator.to_dict() if self.creator else None
        }

class LearningMilestone(db.Model):
    """Milestones for learning goals"""
    __tablename__ = 'learning_milestones'
    
    id = Column(Integer, primary_key=True)
    learning_goal_id = Column(Integer, ForeignKey('student_learning_goals.id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    target_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    completion_notes = Column(Text)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    learning_goal = relationship('StudentLearningGoal', back_populates='milestones')
    
    def __repr__(self):
        return f'<LearningMilestone {self.title}>'
    
    def to_dict(self):
        """Convert milestone to dictionary"""
        return {
            'id': self.id,
            'learning_goal_id': self.learning_goal_id,
            'title': self.title,
            'description': self.description,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completion_notes': self.completion_notes,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StudentComparison(db.Model):
    """Student tutor comparisons for decision making"""
    __tablename__ = 'student_comparisons'
    
    id = Column(Integer, primary_key=True)
    learner_profile_id = Column(Integer, ForeignKey('learner_profiles.id'), nullable=False)
    comparison_name = Column(String(200), nullable=False)
    tutor_ids = Column(JSON, nullable=False)  # List of tutor IDs being compared
    comparison_criteria = Column(JSON)  # Criteria used for comparison
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    learner_profile = relationship('LearnerProfile')
    
    def __repr__(self):
        return f'<StudentComparison {self.comparison_name}>'
    
    def to_dict(self):
        """Convert comparison to dictionary"""
        return {
            'id': self.id,
            'learner_profile_id': self.learner_profile_id,
            'comparison_name': self.comparison_name,
            'tutor_ids': self.tutor_ids or [],
            'comparison_criteria': self.comparison_criteria or {},
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }