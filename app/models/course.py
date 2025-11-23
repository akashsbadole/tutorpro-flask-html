from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db


class Course(db.Model):
    """
    Course model with syllabus, description, and pricing
    """
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    level = db.Column(db.Enum('Beginner', 'Intermediate', 'Advanced', name='course_levels'), 
                     nullable=False, default='Beginner')
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_hours = db.Column(db.Integer, nullable=False)
    thumbnail_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    syllabus = db.relationship('CourseSyllabus', backref='course', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.title}>'


class CourseSyllabus(db.Model):
    """
    CourseSyllabus model for tracking course content
    """
    __tablename__ = 'course_syllabus'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    order_index = db.Column(db.Integer, nullable=False)
    is_milestone = db.Column(db.Boolean, default=False)
    estimated_hours = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseSyllabus {self.title}>'


class CourseTopic(db.Model):
    """
    CourseTopic model for organizing course content
    """
    __tablename__ = 'course_topics'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    order_index = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseTopic {self.title}>'


class CourseMaterial(db.Model):
    """
    CourseMaterial model for course resources
    """
    __tablename__ = 'course_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    material_type = db.Column(db.Enum('Document', 'Video', 'Audio', 'Link', 'Other', name='material_types'), 
                             nullable=False)
    file_url = db.Column(db.String(500))
    external_url = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseMaterial {self.title}>'


class CourseAssignment(db.Model):
    """
    CourseAssignment model for course assignments
    """
    __tablename__ = 'course_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    max_score = db.Column(db.Float, default=100.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseAssignment {self.title}>'


class CourseQuiz(db.Model):
    """
    CourseQuiz model for course quizzes
    """
    __tablename__ = 'course_quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    time_limit_minutes = db.Column(db.Integer)
    max_attempts = db.Column(db.Integer, default=3)
    passing_score = db.Column(db.Float, default=70.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseQuiz {self.title}>'


class CourseDiscussion(db.Model):
    """
    CourseDiscussion model for course discussions
    """
    __tablename__ = 'course_discussions'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseDiscussion {self.title}>'


class CourseEnrollment(db.Model):
    """
    CourseEnrollment model for student course enrollments
    """
    __tablename__ = 'course_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    progress_percentage = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<CourseEnrollment {self.course_id}-{self.student_id}>'


class CourseProgress(db.Model):
    """
    CourseProgress model for tracking student progress
    """
    __tablename__ = 'course_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('course_enrollments.id'), nullable=False)
    content_type = db.Column(db.Enum('Topic', 'Material', 'Assignment', 'Quiz', name='content_types'), 
                            nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime)
    score = db.Column(db.Float)
    time_spent_minutes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseProgress {self.content_type}-{self.content_id}>'


class CourseAnnouncement(db.Model):
    """
    CourseAnnouncement model for course announcements
    """
    __tablename__ = 'course_announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseAnnouncement {self.title}>'


class CourseAchievement(db.Model):
    """
    CourseAchievement model for course achievements
    """
    __tablename__ = 'course_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    badge_url = db.Column(db.String(500))
    points = db.Column(db.Integer, default=0)
    condition_type = db.Column(db.Enum('Completion', 'Score', 'Time', 'Participation', name='achievement_conditions'), 
                              nullable=False)
    condition_value = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseAchievement {self.title}>'


class StudentAchievement(db.Model):
    """
    StudentAchievement model for tracking earned achievements
    """
    __tablename__ = 'student_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey('course_achievements.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    earned_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudentAchievement {self.achievement_id}-{self.student_id}>'