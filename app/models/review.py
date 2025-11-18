from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.booking import Booking


class Review(db.Model):
    """
    Model for student reviews
    """
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 scale
    comment = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)  # Verified if booking was completed
    is_public = db.Column(db.Boolean, default=True)  # Whether review is publicly visible
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviews_written')
    tutor = db.relationship('TutorProfile', foreign_keys=[tutor_id], backref='reviews_received')
    booking = db.relationship('Booking', foreign_keys=[booking_id], backref='review')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_review_tutor', 'tutor_id'),
        db.Index('idx_review_rating', 'rating'),
        db.Index('idx_review_verified', 'is_verified'),
    )
    
    def __repr__(self):
        return f'<Review {self.reviewer.email} for {self.tutor.user.email} - {self.rating}/5>'
    
    @property
    def is_positive(self):
        """Check if review is positive (rating >= 4)"""
        return self.rating >= 4
    
    @property
    def is_negative(self):
        """Check if review is negative (rating <= 2)"""
        return self.rating <= 2
    
    def verify_review(self):
        """Mark review as verified"""
        self.is_verified = True
        db.session.commit()
    
    def toggle_public_visibility(self):
        """Toggle public visibility of review"""
        self.is_public = not self.is_public
        db.session.commit()


class Rating(db.Model):
    """
    Model for rating system
    """
    __tablename__ = 'ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 scale
    rating_aspect = db.Column(db.Enum('Teaching Quality', 'Communication', 'Punctuality', 'Preparation', 
                                     'Value for Money', name='rating_aspects'), nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tutor = db.relationship('TutorProfile', backref='ratings')
    student = db.relationship('User', foreign_keys=[student_id], backref='ratings_given')
    booking = db.relationship('Booking', foreign_keys=[booking_id], backref='ratings')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_rating_tutor', 'tutor_id'),
        db.Index('idx_rating_aspect', 'rating_aspect'),
    )
    
    def __repr__(self):
        return f'<Rating {self.rating_aspect} - {self.rating}/5 for {self.tutor.user.email}>'
    
    @property
    def is_positive(self):
        """Check if rating is positive (rating >= 4)"""
        return self.rating >= 4
    
    @property
    def is_negative(self):
        """Check if rating is negative (rating <= 2)"""
        return self.rating <= 2


class TutorRatingSummary(db.Model):
    """
    Model to store aggregated rating summaries for tutors
    """
    __tablename__ = 'tutor_rating_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False, unique=True)
    
    # Overall rating
    overall_rating = db.Column(db.Numeric(3, 2), default=0.0)  # Average rating
    total_reviews = db.Column(db.Integer, default=0)
    
    # Rating breakdown by aspect
    teaching_quality_rating = db.Column(db.Numeric(3, 2), default=0.0)
    communication_rating = db.Column(db.Numeric(3, 2), default=0.0)
    punctuality_rating = db.Column(db.Numeric(3, 2), default=0.0)
    preparation_rating = db.Column(db.Numeric(3, 2), default=0.0)
    value_for_money_rating = db.Column(db.Numeric(3, 2), default=0.0)
    
    # Distribution of ratings
    five_star_count = db.Column(db.Integer, default=0)
    four_star_count = db.Column(db.Integer, default=0)
    three_star_count = db.Column(db.Integer, default=0)
    two_star_count = db.Column(db.Integer, default=0)
    one_star_count = db.Column(db.Integer, default=0)
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tutor = db.relationship('TutorProfile', backref='rating_summary')
    
    def __repr__(self):
        return f'<TutorRatingSummary for {self.tutor.user.email} - {self.overall_rating}/5>'
    
    def update_ratings(self):
        """Update rating summary based on all reviews"""
        reviews = self.tutor.reviews.filter_by(is_public=True).all()
        
        if not reviews:
            self.overall_rating = 0.0
            self.total_reviews = 0
            return
        
        # Calculate overall rating
        total_rating = sum(review.rating for review in reviews)
        self.overall_rating = total_rating / len(reviews)
        self.total_reviews = len(reviews)
        
        # Calculate rating by aspect
        ratings_by_aspect = {
            'Teaching Quality': [],
            'Communication': [],
            'Punctuality': [],
            'Preparation': [],
            'Value for Money': []
        }
        
        # Get all ratings for this tutor
        all_ratings = self.tutor.ratings.all()
        for rating in all_ratings:
            if rating.rating_aspect in ratings_by_aspect:
                ratings_by_aspect[rating.rating_aspect].append(rating.rating)
        
        # Calculate average for each aspect
        self.teaching_quality_rating = sum(ratings_by_aspect['Teaching Quality']) / len(ratings_by_aspect['Teaching Quality']) if ratings_by_aspect['Teaching Quality'] else 0.0
        self.communication_rating = sum(ratings_by_aspect['Communication']) / len(ratings_by_aspect['Communication']) if ratings_by_aspect['Communication'] else 0.0
        self.punctuality_rating = sum(ratings_by_aspect['Punctuality']) / len(ratings_by_aspect['Punctuality']) if ratings_by_aspect['Punctuality'] else 0.0
        self.preparation_rating = sum(ratings_by_aspect['Preparation']) / len(ratings_by_aspect['Preparation']) if ratings_by_aspect['Preparation'] else 0.0
        self.value_for_money_rating = sum(ratings_by_aspect['Value for Money']) / len(ratings_by_aspect['Value for Money']) if ratings_by_aspect['Value for Money'] else 0.0
        
        # Calculate rating distribution
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating_distribution[review.rating] += 1
        
        self.one_star_count = rating_distribution[1]
        self.two_star_count = rating_distribution[2]
        self.three_star_count = rating_distribution[3]
        self.four_star_count = rating_distribution[4]
        self.five_star_count = rating_distribution[5]
        
        self.last_updated = datetime.utcnow()
        db.session.commit()