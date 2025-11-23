from datetime import datetime
from app import db

class Playlist(db.Model):
    """
    YouTube playlist model for course content
    """
    __tablename__ = 'playlists'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Playlist details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    playlist_url = db.Column(db.String(500))  # YouTube playlist URL
    playlist_id = db.Column(db.String(100))  # YouTube playlist ID
    
    # Creator
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True, index=True)
    
    # Playlist settings
    is_public = db.Column(db.Boolean, default=False)  # Publicly discoverable
    allow_comments = db.Column(db.Boolean, default=True)  # Allow user comments
    allow_rating = db.Column(db.Boolean, default=True)  # Allow user ratings
    
    # Content tracking
    video_count = db.Column(db.Integer, default=0)
    total_duration = db.Column(db.Integer)  # Total duration in minutes
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='playlists')
    course = db.relationship('Course', backref='playlists')
    videos = db.relationship('PlaylistVideo', backref='playlist', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Playlist {self.id}: {self.title}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'playlist_url': self.playlist_url,
            'playlist_id': self.playlist_id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'is_public': self.is_public,
            'allow_comments': self.allow_comments,
            'allow_rating': self.allow_rating,
            'video_count': self.video_count,
            'total_duration': self.total_duration,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PlaylistVideo(db.Model):
    """
    Individual videos within a playlist
    """
    __tablename__ = 'playlist_videos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Video details
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False, index=True)
    video_id = db.Column(db.String(50))  # YouTube video ID
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)  # Duration in seconds
    position = db.Column(db.Integer, default=0)  # Position in playlist
    
    # Video metadata
    thumbnail_url = db.Column(db.String(500))  # YouTube thumbnail URL
    tags = db.Column(db.Text)  # Comma-separated tags
    
    # Learning objectives
    learning_objectives = db.Column(db.Text)  # JSON array of objectives
    key_topics = db.Column(db.Text)  # Key topics covered
    
    # Engagement tracking
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    playlist = db.relationship('Playlist', backref='videos')
    
    def __repr__(self):
        return f'<PlaylistVideo {self.id}: {self.title}>'
    
    def get_tags_list(self):
        """Get tags as list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def get_learning_objectives_list(self):
        """Get learning objectives as list"""
        import json
        try:
            return json.loads(self.learning_objectives) if self.learning_objectives else []
        except:
            return []
    
    def get_key_topics_list(self):
        """Get key topics as list"""
        import json
        try:
            return json.loads(self.key_topics) if self.key_topics else []
        except:
            return []
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'playlist_id': self.playlist_id,
            'video_id': self.video_id,
            'title': self.title,
            'description': self.description,
            'duration': self.duration,
            'position': self.position,
            'thumbnail_url': self.thumbnail_url,
            'tags': self.get_tags_list(),
            'learning_objectives': self.get_learning_objectives_list(),
            'key_topics': self.get_key_topics_list(),
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PlaylistComment(db.Model):
    """
    Comments on playlist videos
    """
    __tablename__ = 'playlist_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Comment details
    playlist_video_id = db.Column(db.Integer, db.ForeignKey('playlist_videos.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('playlist_comments.id'))  # For replies
    content = db.Column(db.Text, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='playlist_comments')
    playlist_video = db.relationship('PlaylistVideo', backref='comments')
    parent = db.relationship('PlaylistComment', remote_side=[id], backref='replies')
    replies = db.relationship('PlaylistComment', remote_side=[parent_id], backref='replies')
    
    def __repr__(self):
        return f'<PlaylistComment {self.id}: {self.content[:50]}...>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'playlist_video_id': self.playlist_video_id,
            'user_id': self.user_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PlaylistRating(db.Model):
    """
    Ratings for playlists and videos
    """
    __tablename__ = 'playlist_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Rating details
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=True, index=True)
    playlist_video_id = db.Column(db.Integer, db.ForeignKey('playlist_videos.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review = db.Column(db.Text)  # Optional text review
    
    # Validation
    is_helpful = db.Column(db.Boolean, default=False)  # Was this rating helpful
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='playlist_ratings')
    playlist = db.relationship('Playlist', backref='ratings')
    playlist_video = db.relationship('PlaylistVideo', backref='ratings')
    
    def __repr__(self):
        return f'<PlaylistRating {self.id}: {self.rating} stars>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'playlist_id': self.playlist_id,
            'playlist_video_id': self.playlist_video_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'review': self.review,
            'is_helpful': self.is_helpful,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }