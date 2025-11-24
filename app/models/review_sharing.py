from datetime import datetime
from app import db

class ReviewSharing(db.Model):
    """
    Review sharing functionality for social media and testimonials
    """
    __tablename__ = 'review_sharing'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Review and user
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Sharing settings
    sharing_code = db.Column(db.String(20), unique=True, nullable=False, index=True)  # Unique code for public access
    platform = db.Column(db.Enum(
        'LinkedIn',
        'Facebook',
        'Twitter',
        'Instagram',
        'WhatsApp',
        'Email',
        'Custom',
        name='sharing_platforms'
    ), nullable=False, default='LinkedIn')
    
    # Content
    custom_message = db.Column(db.Text)  # Custom message to accompany review
    include_rating = db.Column(db.Boolean, default=True)  # Include rating in shared content
    include_reviewer_name = db.Column(db.Boolean, default=False)  # Include reviewer's name
    
    # Visibility and access
    is_public = db.Column(db.Boolean, default=False)  # Publicly discoverable
    allow_anonymous_view = db.Column(db.Boolean, default=True)  # Allow viewing without login
    password_protected = db.Column(db.Boolean, default=False)
    access_password = db.Column(db.String(100))
    
    # Tracking
    view_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)  # How many times shared
    conversion_rate = db.Column(db.Float, default=0.0)  # Conversion rate (views to signups)
    
    # Expiration
    expires_at = db.Column(db.DateTime)  # When sharing link expires
    auto_post_to_profile = db.Column(db.Boolean, default=False)  # Auto-post to user's LinkedIn profile
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_shared_at = db.Column(db.DateTime)
    
    # Relationships
    review = db.relationship('TutorReview', backref='sharing')
    user = db.relationship('User', backref='shared_reviews')
    
    def __repr__(self):
        return f'<ReviewSharing {self.id}: {self.platform}>'
    
    def is_accessible(self):
        """Check if sharing link is still accessible"""
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def get_sharing_url(self):
        """Generate sharing URL based on platform"""
        base_url = f"https://tutorpro.com/shared/review/{self.sharing_code}"
        
        if self.platform == 'LinkedIn':
            return f"https://www.linkedin.com/sharingArticle-offsite/?url={base_url}"
        elif self.platform == 'Facebook':
            return f"https://www.facebook.com/sharer/sharer.php?u={base_url}"
        elif self.platform == 'Twitter':
            return f"https://twitter.com/intent/tweet?text=Check%20out%20this%20review%20on%20TutorPro%3A%20{base_url}"
        elif self.platform == 'WhatsApp':
            return f"https://wa.me/?text={base_url}"
        else:
            return base_url
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'review_id': self.review_id,
            'user_id': self.user_id,
            'sharing_code': self.sharing_code,
            'platform': self.platform,
            'custom_message': self.custom_message,
            'include_rating': self.include_rating,
            'include_reviewer_name': self.include_reviewer_name,
            'is_public': self.is_public,
            'allow_anonymous_view': self.allow_anonymous_view,
            'password_protected': self.password_protected,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'view_count': self.view_count,
            'click_count': self.click_count,
            'share_count': self.share_count,
            'conversion_rate': self.conversion_rate,
            'sharing_url': self.get_sharing_url(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_shared_at': self.last_shared_at.isoformat() if self.last_shared_at else None,
            'is_accessible': self.is_accessible()
        }


class SocialMediaPost(db.Model):
    """
    Social media posts for reviews and testimonials
    """
    __tablename__ = 'social_media_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Post details
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=True, index=True)
    platform = db.Column(db.Enum(
        'LinkedIn',
        'Facebook',
        'Twitter',
        'Instagram',
        'Blog',
        'Forum',
        name='post_platforms'
    ), nullable=False, default='LinkedIn')
    
    # Content
    post_url = db.Column(db.String(500))  # URL to the actual post
    post_id = db.Column(db.String(100))  # Platform-specific post ID
    content = db.Column(db.Text)  # Post content
    media_url = db.Column(db.String(500))  # Attached media URL
    media_type = db.Column(db.Enum(
        'Image',
        'Video',
        'Carousel',
        'Document',
        name='media_types'
    ), nullable=True)
    
    # Post metadata
    hashtags = db.Column(db.Text)  # Comma-separated hashtags
    mention_users = db.Column(db.Text)  # Comma-separated mentioned users
    
    # Engagement tracking
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    click_through_rate = db.Column(db.Float, default=0.0)  # CTR for linked content
    
    # Scheduling
    scheduled_at = db.Column(db.DateTime)  # When to post
    is_posted = db.Column(db.Boolean, default=False)  # Whether posted yet
    auto_post = db.Column(db.Boolean, default=False)  # Auto-post option
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    posted_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='social_media_posts')
    review = db.relationship('TutorReview', backref='social_posts')
    
    def __repr__(self):
        return f'<SocialMediaPost {self.id}: {self.platform}>'
    
    def get_hashtags_list(self):
        """Get hashtags as list"""
        if self.hashtags:
            return [tag.strip() for tag in self.hashtags.split(',') if tag.strip()]
        return []
    
    def get_mentioned_users_list(self):
        """Get mentioned users as list"""
        if self.mention_users:
            return [user.strip() for user in self.mention_users.split(',') if user.strip()]
        return []
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'review_id': self.review_id,
            'platform': self.platform,
            'post_url': self.post_url,
            'post_id': self.post_id,
            'content': self.content,
            'media_url': self.media_url,
            'media_type': self.media_type,
            'hashtags': self.get_hashtags_list(),
            'mention_users': self.get_mentioned_users_list(),
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'shares_count': self.shares_count,
            'click_through_rate': self.click_through_rate,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'is_posted': self.is_posted,
            'auto_post': self.auto_post,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }