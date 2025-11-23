from datetime import datetime
from app import db

class YouTubePlaylist(db.Model):
    """
    YouTube playlist model for course supplementary materials
    """
    __tablename__ = 'youtube_playlists'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Playlist details
    playlist_id = db.Column(db.String(100), unique=True, nullable=False, index=True)  # YouTube playlist ID
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Course association
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True, index=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Playlist metadata
    thumbnail_url = db.Column(db.String(500))
    channel_title = db.Column(db.String(200))
    published_at = db.Column(db.DateTime)
    video_count = db.Column(db.Integer, default=0)
    total_duration = db.Column(db.Integer, default=0)  # Total duration in seconds
    
    # Playlist settings
    is_public = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    
    # Learning objectives
    learning_objectives = db.Column(db.Text)  # JSON array of learning objectives
    
    # Tags and categories
    tags = db.Column(db.Text)  # JSON array of tags
    difficulty_level = db.Column(db.Enum(
        'Beginner',
        'Intermediate',
        'Advanced',
        name='playlist_difficulty_levels'
    ), nullable=False, default='Beginner')
    
    # Engagement tracking
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='youtube_playlists')
    tutor = db.relationship('User', backref='youtube_playlists')
    videos = db.relationship('YouTubeVideo', backref='playlist', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<YouTubePlaylist {self.id}: {self.title}>'
    
    def get_formatted_duration(self):
        """Get formatted total duration (HH:MM:SS)"""
        hours = self.total_duration // 3600
        minutes = (self.total_duration % 3600) // 60
        seconds = self.total_duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'playlist_id': self.playlist_id,
            'title': self.title,
            'description': self.description,
            'course_id': self.course_id,
            'tutor_id': self.tutor_id,
            'thumbnail_url': self.thumbnail_url,
            'channel_title': self.channel_title,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'video_count': self.video_count,
            'total_duration': self.total_duration,
            'formatted_duration': self.get_formatted_duration(),
            'is_public': self.is_public,
            'is_featured': self.is_featured,
            'sort_order': self.sort_order,
            'learning_objectives': self.learning_objectives,
            'tags': self.tags,
            'difficulty_level': self.difficulty_level,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class YouTubeVideo(db.Model):
    """
    Individual video model within YouTube playlists
    """
    __tablename__ = 'youtube_videos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Video details
    video_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # YouTube video ID
    playlist_id = db.Column(db.Integer, db.ForeignKey('youtube_playlists.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Video metadata
    thumbnail_url = db.Column(db.String(500))
    duration = db.Column(db.Integer, default=0)  # Duration in seconds
    published_at = db.Column(db.DateTime)
    position = db.Column(db.Integer, default=0)  # Position in playlist
    
    # Video content
    transcript_available = db.Column(db.Boolean, default=False)
    transcript_text = db.Column(db.Text)
    language = db.Column(db.String(10), default='en')
    
    # Learning objectives
    learning_objectives = db.Column(db.Text)  # JSON array of learning objectives
    
    # Engagement tracking
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    
    # Video settings
    is_public = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('VideoComment', backref='video', lazy='dynamic', cascade='all, delete-orphan')
    ratings = db.relationship('VideoRating', backref='video', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<YouTubeVideo {self.id}: {self.title}>'
    
    def get_formatted_duration(self):
        """Get formatted duration (MM:SS or HH:MM:SS)"""
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def get_average_rating(self):
        """Calculate average rating"""
        ratings = self.ratings.all()
        if not ratings:
            return 0.0
        
        total = sum(rating.rating for rating in ratings)
        return round(total / len(ratings), 2)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'playlist_id': self.playlist_id,
            'title': self.title,
            'description': self.description,
            'thumbnail_url': self.thumbnail_url,
            'duration': self.duration,
            'formatted_duration': self.get_formatted_duration(),
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'position': self.position,
            'transcript_available': self.transcript_available,
            'transcript_text': self.transcript_text,
            'language': self.language,
            'learning_objectives': self.learning_objectives,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'is_public': self.is_public,
            'is_featured': self.is_featured,
            'average_rating': self.get_average_rating(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class VideoComment(db.Model):
    """
    Comments on YouTube videos
    """
    __tablename__ = 'video_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Comment details
    video_id = db.Column(db.Integer, db.ForeignKey('youtube_videos.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('video_comments.id'), nullable=True)  # For threaded comments
    
    # Comment content
    content = db.Column(db.Text, nullable=False)
    
    # Comment metadata
    is_pinned = db.Column(db.Boolean, default=False)
    is_edited = db.Column(db.Boolean, default=False)
    edited_at = db.Column(db.DateTime)
    like_count = db.Column(db.Integer, default=0)
    
    # Moderation
    is_hidden = db.Column(db.Boolean, default=False)
    hidden_reason = db.Column(db.String(200))
    moderated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='video_comments')
    moderator = db.relationship('User', foreign_keys=[moderated_by])
    replies = db.relationship('VideoComment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def __repr__(self):
        return f'<VideoComment {self.id}: {self.content[:50]}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'user_id': self.user_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'is_pinned': self.is_pinned,
            'is_edited': self.is_edited,
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
            'like_count': self.like_count,
            'is_hidden': self.is_hidden,
            'hidden_reason': self.hidden_reason,
            'moderated_by': self.moderated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': self.user.to_dict() if self.user else None,
            'reply_count': self.replies.count() if self.replies else 0
        }


class VideoRating(db.Model):
    """
    Ratings for YouTube videos
    """
    __tablename__ = 'video_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Rating details
    video_id = db.Column(db.Integer, db.ForeignKey('youtube_videos.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Rating value (1-5 stars)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    
    # Review content (optional)
    review = db.Column(db.Text)
    
    # Rating metadata
    helpful_count = db.Column(db.Integer, default=0)
    not_helpful_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='video_ratings')
    
    # Unique constraint to prevent duplicate ratings
    __table_args__ = (db.UniqueConstraint('video_id', 'user_id', name='unique_video_user_rating'),)
    
    def __repr__(self):
        return f'<VideoRating {self.id}: {self.rating} stars>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'review': self.review,
            'helpful_count': self.helpful_count,
            'not_helpful_count': self.not_helpful_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': self.user.to_dict() if self.user else None
        }