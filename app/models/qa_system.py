from datetime import datetime
from app import db

class Question(db.Model):
    """
    Question model for student-tutor Q&A system
    """
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Question details
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Question metadata
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True, index=True)
    
    # Question categorization
    question_type = db.Column(db.Enum(
        'Concept Clarification',
        'Homework Help',
        'Exam Preparation',
        'Career Guidance',
        'General Inquiry',
        name='question_types'
    ), nullable=False, default='General Inquiry')
    
    difficulty_level = db.Column(db.Enum(
        'Beginner',
        'Intermediate',
        'Advanced',
        name='question_difficulty_levels'
    ), nullable=False, default='Beginner')
    
    # Question status
    status = db.Column(db.Enum(
        'Open',
        'Answered',
        'Closed',
        'Under Review',
        name='question_statuses'
    ), nullable=False, default='Open', index=True)
    
    # Priority and urgency
    priority = db.Column(db.Enum(
        'Low',
        'Medium',
        'High',
        'Urgent',
        name='question_priorities'
    ), nullable=False, default='Medium')
    
    # Question visibility
    is_public = db.Column(db.Boolean, default=True)
    is_anonymous = db.Column(db.Boolean, default=False)
    
    # Question engagement
    view_count = db.Column(db.Integer, default=0)
    upvote_count = db.Column(db.Integer, default=0)
    downvote_count = db.Column(db.Integer, default=0)
    
    # Question resolution
    accepted_answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'), nullable=True)
    resolved_at = db.Column(db.DateTime)
    
    # Question moderation
    is_flagged = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.String(500))
    moderated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='asked_questions')
    subject = db.relationship('Subject', backref='questions')
    course = db.relationship('Course', backref='questions')
    accepted_answer = db.relationship('Answer', foreign_keys=[accepted_answer_id])
    moderator = db.relationship('User', foreign_keys=[moderated_by])
    answers = db.relationship('Answer', backref='question', lazy='dynamic', cascade='all, delete-orphan',
                             foreign_keys='Answer.question_id')
    tags = db.relationship('QuestionTag', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    upvotes = db.relationship('QuestionVote', foreign_keys='QuestionVote.question_id', backref='question', lazy='dynamic')
    
    def __repr__(self):
        return f'<Question {self.id}: {self.title}>'
    
    def get_vote_score(self):
        """Calculate vote score"""
        return self.upvote_count - self.downvote_count
    
    def is_answered(self):
        """Check if question has been answered"""
        return self.status == 'Answered' or self.answers.count() > 0
    
    def is_resolved(self):
        """Check if question has been resolved"""
        return self.accepted_answer_id is not None
    
    def get_answer_count(self):
        """Get total number of answers"""
        return self.answers.count()
    
    def get_time_since_creation(self):
        """Get time since question was created"""
        from datetime import datetime
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'course_id': self.course_id,
            'question_type': self.question_type,
            'difficulty_level': self.difficulty_level,
            'status': self.status,
            'priority': self.priority,
            'is_public': self.is_public,
            'is_anonymous': self.is_anonymous,
            'view_count': self.view_count,
            'upvote_count': self.upvote_count,
            'downvote_count': self.downvote_count,
            'vote_score': self.get_vote_score(),
            'accepted_answer_id': self.accepted_answer_id,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'is_flagged': self.is_flagged,
            'flag_reason': self.flag_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'time_since_creation': self.get_time_since_creation(),
            'is_answered': self.is_answered(),
            'is_resolved': self.is_resolved(),
            'answer_count': self.get_answer_count(),
            'student': self.student.to_dict() if self.student and not self.is_anonymous else None,
            'subject': self.subject.to_dict() if self.subject else None,
            'course': self.course.to_dict() if self.course else None,
            'tags': [tag.to_dict() for tag in self.tags] if self.tags else []
        }


class Answer(db.Model):
    """
    Answer model for tutor responses to questions
    """
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Answer details
    content = db.Column(db.Text, nullable=False)
    
    # Answer metadata
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Answer status
    is_accepted = db.Column(db.Boolean, default=False)
    accepted_at = db.Column(db.DateTime)
    accepted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Answer engagement
    upvote_count = db.Column(db.Integer, default=0)
    downvote_count = db.Column(db.Integer, default=0)
    
    # Answer moderation
    is_flagged = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.String(500))
    moderated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Answer quality metrics
    helpful_count = db.Column(db.Integer, default=0)
    not_helpful_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='answered_questions')
    accepter = db.relationship('User', foreign_keys=[accepted_by])
    moderator = db.relationship('User', foreign_keys=[moderated_by])
    upvotes = db.relationship('AnswerVote', foreign_keys='AnswerVote.answer_id', backref='answer', lazy='dynamic')
    
    def __repr__(self):
        return f'<Answer {self.id}: Question {self.question_id}>'
    
    def get_vote_score(self):
        """Calculate vote score"""
        return self.upvote_count - self.downvote_count
    
    def get_helpful_score(self):
        """Calculate helpful score"""
        return self.helpful_count - self.not_helpful_count
    
    def get_time_since_creation(self):
        """Get time since answer was created"""
        from datetime import datetime
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'content': self.content,
            'question_id': self.question_id,
            'tutor_id': self.tutor_id,
            'is_accepted': self.is_accepted,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'accepted_by': self.accepted_by,
            'upvote_count': self.upvote_count,
            'downvote_count': self.downvote_count,
            'vote_score': self.get_vote_score(),
            'helpful_count': self.helpful_count,
            'not_helpful_count': self.not_helpful_count,
            'helpful_score': self.get_helpful_score(),
            'is_flagged': self.is_flagged,
            'flag_reason': self.flag_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'time_since_creation': self.get_time_since_creation(),
            'tutor': self.tutor.to_dict() if self.tutor else None
        }


class QuestionTag(db.Model):
    """
    Tag model for categorizing questions
    """
    __tablename__ = 'question_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Tag details
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tag = db.relationship('Tag', backref='question_tags')
    
    def __repr__(self):
        return f'<QuestionTag {self.id}: Question {self.question_id} - Tag {self.tag_id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'question_id': self.question_id,
            'tag_id': self.tag_id,
            'tag': self.tag.to_dict() if self.tag else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Tag(db.Model):
    """
    Tag model for question categorization
    """
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Tag details
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200))
    
    # Tag metadata
    color = db.Column(db.String(7), default='#007bff')  # Hex color code
    icon = db.Column(db.String(50))  # Icon class name
    
    # Tag usage statistics
    question_count = db.Column(db.Integer, default=0)
    
    # Tag status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tag {self.id}: {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'question_count': self.question_count,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class QuestionVote(db.Model):
    """
    Vote model for questions
    """
    __tablename__ = 'question_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Vote details
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Vote type
    vote_type = db.Column(db.Enum(
        'Upvote',
        'Downvote',
        name='vote_types'
    ), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='question_votes')
    
    # Unique constraint to prevent duplicate votes
    __table_args__ = (db.UniqueConstraint('question_id', 'user_id', name='unique_question_user_vote'),)
    
    def __repr__(self):
        return f'<QuestionVote {self.id}: {self.vote_type}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'question_id': self.question_id,
            'user_id': self.user_id,
            'vote_type': self.vote_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AnswerVote(db.Model):
    """
    Vote model for answers
    """
    __tablename__ = 'answer_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Vote details
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Vote type
    vote_type = db.Column(db.Enum(
        'Upvote',
        'Downvote',
        name='answer_vote_types'
    ), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='answer_votes')
    
    # Unique constraint to prevent duplicate votes
    __table_args__ = (db.UniqueConstraint('answer_id', 'user_id', name='unique_answer_user_vote'),)
    
    def __repr__(self):
        return f'<AnswerVote {self.id}: {self.vote_type}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'answer_id': self.answer_id,
            'user_id': self.user_id,
            'vote_type': self.vote_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class QuestionFollow(db.Model):
    """
    Follow model for tracking question followers
    """
    __tablename__ = 'question_follows'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Follow details
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Follow preferences
    notification_enabled = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='followed_questions')
    
    # Unique constraint to prevent duplicate follows
    __table_args__ = (db.UniqueConstraint('question_id', 'user_id', name='unique_question_user_follow'),)
    
    def __repr__(self):
        return f'<QuestionFollow {self.id}: User {self.user_id} follows Question {self.question_id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'question_id': self.question_id,
            'user_id': self.user_id,
            'notification_enabled': self.notification_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }