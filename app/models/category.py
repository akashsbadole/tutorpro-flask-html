from datetime import datetime
from app import db

class SubjectCategory(db.Model):
    """
    Subject categories for organizing tutor specialties
    Supports hierarchical structure with parent-child relationships
    """
    __tablename__ = 'subject_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    slug = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('subject_categories.id'), nullable=True)
    icon_url = db.Column(db.String(255))
    banner_url = db.Column(db.String(255))
    color = db.Column(db.String(7), default='#007bff')  # Hex color code
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_featured = db.Column(db.Boolean, default=False)
    meta_title = db.Column(db.String(100))
    meta_description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('SubjectCategory', remote_side=[id], backref='children')
    subjects = db.relationship('Subject', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SubjectCategory {self.name}>'
    
    @property
    def full_path(self):
        """Get the full hierarchical path of the category"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name
    
    def get_all_children(self):
        """Get all child categories recursively"""
        children = list(self.children)
        for child in self.children:
            children.extend(child.get_all_children())
        return children
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'parent_id': self.parent_id,
            'icon_url': self.icon_url,
            'banner_url': self.banner_url,
            'color': self.color,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'subject_count': self.subjects.count(),
            'full_path': self.full_path
        }


class Subject(db.Model):
    """
    Individual subjects within categories
    """
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('subject_categories.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    slug = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)
    icon_url = db.Column(db.String(255))
    difficulty_level = db.Column(db.Enum('Beginner', 'Intermediate', 'Advanced', 'All Levels', name='subject_difficulty_levels'), default='All Levels')
    typical_duration_hours = db.Column(db.Integer)  # Typical course duration in hours
    typical_price_range_min = db.Column(db.Numeric(10, 2))
    typical_price_range_max = db.Column(db.Numeric(10, 2))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_popular = db.Column(db.Boolean, default=False)
    meta_title = db.Column(db.String(100))
    meta_description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tutor_subjects = db.relationship('TutorSubject', backref='subject_category', lazy='dynamic', cascade='all, delete-orphan')
    learning_objectives = db.relationship('LearningObjective', backref='subject_category', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Subject {self.name}>'
    
    def get_tutor_count(self):
        """Get the number of tutors teaching this subject"""
        return self.tutor_subjects.filter_by(is_active=True).count()
    
    def get_average_price(self):
        """Get the average hourly rate for this subject"""
        from sqlalchemy import func
        from app.models.tutor import TutorSubject
        avg_price = db.session.query(func.avg(TutorSubject.hourly_rate)).filter_by(
            subject_id=self.id, is_active=True
        ).scalar()
        return float(avg_price) if avg_price else 0
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'icon_url': self.icon_url,
            'difficulty_level': self.difficulty_level,
            'typical_duration_hours': self.typical_duration_hours,
            'typical_price_range_min': float(self.typical_price_range_min) if self.typical_price_range_min else None,
            'typical_price_range_max': float(self.typical_price_range_max) if self.typical_price_range_max else None,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'is_popular': self.is_popular,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'tutor_count': self.get_tutor_count(),
            'average_price': self.get_average_price()
        }


class LearningObjective(db.Model):
    """
    Learning objectives for subjects
    """
    __tablename__ = 'learning_objectives'
    
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LearningObjective {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'title': self.title,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active
        }


class SubjectLevel(db.Model):
    """
    Subject proficiency levels
    """
    __tablename__ = 'subject_levels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubjectLevel {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order
        }