from datetime import datetime
from app import db

class VerificationDocument(db.Model):
    """
    Documents uploaded for tutor verification
    """
    __tablename__ = 'verification_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False, index=True)
    
    # Document details
    document_type = db.Column(db.Enum(
        'Government ID', 
        'Educational Certificate', 
        'Professional Certification', 
        'Address Proof', 
        'Work Experience', 
        'Police Clearance', 
        'Bank Account', 
        'Profile Photo', 
        'Video Introduction',
        name='document_types'
    ), nullable=False)
    
    document_name = db.Column(db.String(200), nullable=False)
    document_number = db.Column(db.String(100))  # ID number, certificate number, etc.
    issuing_authority = db.Column(db.String(200))  # Issuing organization
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    
    # File information
    file_url = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # File size in bytes
    file_type = db.Column(db.String(50))  # MIME type
    thumbnail_url = db.Column(db.String(255))  # For images
    
    # Verification status
    verification_status = db.Column(db.Enum(
        'Pending', 
        'Under Review', 
        'Verified', 
        'Rejected', 
        'Expired', 
        'Requires Resubmission',
        name='verification_statuses'
    ), default='Pending', index=True)
    
    verification_notes = db.Column(db.Text)  # Admin notes
    rejection_reason = db.Column(db.Text)  # Reason for rejection
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin who verified
    verification_date = db.Column(db.DateTime)
    
    # Auto-expiration
    is_expirable = db.Column(db.Boolean, default=False)  # Whether document expires
    expiry_reminder_sent = db.Column(db.Boolean, default=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=False)  # Whether students can see this
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='verification_documents')
    tutor_profile = db.relationship('TutorProfile', backref='verification_documents_list')
    verifier = db.relationship('User', foreign_keys=[verified_by])
    
    def __repr__(self):
        return f'<VerificationDocument {self.document_type} - {self.user.email}>'
    
    def is_expired(self):
        """Check if document has expired"""
        if not self.is_expirable or not self.expiry_date:
            return False
        return datetime.utcnow().date() > self.expiry_date
    
    def days_until_expiry(self):
        """Days until document expires"""
        if not self.expiry_date:
            return None
        delta = self.expiry_date - datetime.utcnow().date()
        return delta.days if delta.days > 0 else 0
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'tutor_profile_id': self.tutor_profile_id,
            'document_type': self.document_type,
            'document_name': self.document_name,
            'document_number': self.document_number if include_sensitive else None,
            'issuing_authority': self.issuing_authority,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'thumbnail_url': self.thumbnail_url,
            'verification_status': self.verification_status,
            'verification_notes': self.verification_notes,
            'rejection_reason': self.rejection_reason,
            'verified_by': self.verified_by,
            'verification_date': self.verification_date.isoformat() if self.verification_date else None,
            'is_expirable': self.is_expirable,
            'expiry_reminder_sent': self.expiry_reminder_sent,
            'is_active': self.is_active,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_expired': self.is_expired(),
            'days_until_expiry': self.days_until_expiry()
        }
        
        if include_sensitive:
            data['file_url'] = self.file_url
            
        return data


class Review(db.Model):
    """
    Student reviews and ratings for tutors
    """
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)  # Associated booking if applicable
    
    # Rating details (1-5 scale)
    overall_rating = db.Column(db.Integer, nullable=False)  # 1-5 overall rating
    teaching_quality = db.Column(db.Integer)  # 1-5 teaching quality
    communication = db.Column(db.Integer)  # 1-5 communication skills
    punctuality = db.Column(db.Integer)  # 1-5 punctuality
    value_for_money = db.Column(db.Integer)  # 1-5 value for money
    subject_knowledge = db.Column(db.Integer)  # 1-5 subject knowledge
    patience = db.Column(db.Integer)  # 1-5 patience level
    
    # Review content
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    pros = db.Column(db.Text)  # JSON array of positive points
    cons = db.Column(db.Text)  # JSON array of areas for improvement
    
    # Moderation
    moderation_status = db.Column(db.Enum(
        'Pending', 
        'Approved', 
        'Rejected', 
        'Flagged', 
        name='review_moderation_status'
    ), default='Pending', index=True)
    
    moderation_notes = db.Column(db.Text)
    moderated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    moderated_date = db.Column(db.DateTime)
    
    # Response
    tutor_response = db.Column(db.Text)  # Tutor's response to review
    tutor_response_date = db.Column(db.DateTime)
    
    # Status
    is_verified_purchase = db.Column(db.Boolean, default=False)  # From actual booking
    is_featured = db.Column(db.Boolean, default=False)  # Featured review
    is_hidden = db.Column(db.Boolean, default=False)  # Hidden from public view
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='reviews_given')
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='reviews_received')
    tutor_profile = db.relationship('TutorProfile', backref='reviews_list')
    booking = db.relationship('Booking', backref='review')
    moderator = db.relationship('User', foreign_keys=[moderated_by])
    
    def __repr__(self):
        return f'<Review {self.student_id}->{self.tutor_id} ({self.overall_rating} stars)>'
    
    def get_pros_list(self):
        """Get list of pros"""
        import json
        try:
            return json.loads(self.pros) if self.pros else []
        except:
            return []
    
    def get_cons_list(self):
        """Get list of cons"""
        import json
        try:
            return json.loads(self.cons) if self.cons else []
        except:
            return []
    
    def calculate_average_rating(self):
        """Calculate average of all sub-ratings"""
        ratings = [
            self.teaching_quality,
            self.communication,
            self.punctuality,
            self.value_for_money,
            self.subject_knowledge,
            self.patience
        ]
        valid_ratings = [r for r in ratings if r is not None]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else self.overall_rating
    
    def to_dict(self, include_student_info=False):
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'tutor_id': self.tutor_id,
            'tutor_profile_id': self.tutor_profile_id,
            'booking_id': self.booking_id,
            'overall_rating': self.overall_rating,
            'teaching_quality': self.teaching_quality,
            'communication': self.communication,
            'punctuality': self.punctuality,
            'value_for_money': self.value_for_money,
            'subject_knowledge': self.subject_knowledge,
            'patience': self.patience,
            'title': self.title,
            'comment': self.comment,
            'pros': self.get_pros_list(),
            'cons': self.get_cons_list(),
            'moderation_status': self.moderation_status,
            'moderation_notes': self.moderation_notes,
            'moderated_by': self.moderated_by,
            'moderated_date': self.moderated_date.isoformat() if self.moderated_date else None,
            'tutor_response': self.tutor_response,
            'tutor_response_date': self.tutor_response_date.isoformat() if self.tutor_response_date else None,
            'is_verified_purchase': self.is_verified_purchase,
            'is_featured': self.is_featured,
            'is_hidden': self.is_hidden,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'average_rating': self.calculate_average_rating()
        }
        
        if include_student_info:
            student_profile = self.student.user_profile if self.student else None
            data['student_name'] = student_profile.full_name if student_profile else 'Anonymous'
            data['student_avatar'] = student_profile.avatar_url if student_profile else None
            
        return data


class TutorRating(db.Model):
    """
    Aggregated rating statistics for tutors
    """
    __tablename__ = 'tutor_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False, index=True)
    
    # Rating aggregates
    average_rating = db.Column(db.Float, default=0.0)  # Overall average
    teaching_quality_avg = db.Column(db.Float, default=0.0)
    communication_avg = db.Column(db.Float, default=0.0)
    punctuality_avg = db.Column(db.Float, default=0.0)
    value_for_money_avg = db.Column(db.Float, default=0.0)
    subject_knowledge_avg = db.Column(db.Float, default=0.0)
    patience_avg = db.Column(db.Float, default=0.0)
    
    # Review counts
    total_reviews = db.Column(db.Integer, default=0)
    five_star_reviews = db.Column(db.Integer, default=0)
    four_star_reviews = db.Column(db.Integer, default=0)
    three_star_reviews = db.Column(db.Integer, default=0)
    two_star_reviews = db.Column(db.Integer, default=0)
    one_star_reviews = db.Column(db.Integer, default=0)
    
    # Verification stats
    verified_purchase_reviews = db.Column(db.Integer, default=0)
    
    # Timestamps
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tutor = db.relationship('User', backref='rating_summary')
    tutor_profile = db.relationship('TutorProfile', backref='rating_summary_list')
    
    def __repr__(self):
        return f'<TutorRating {self.tutor_id} ({self.average_rating} stars)>'
    
    def get_rating_distribution(self):
        """Get rating distribution as percentage"""
        if self.total_reviews == 0:
            return {
                '5_star': 0, '4_star': 0, '3_star': 0, '2_star': 0, '1_star': 0
            }
        
        return {
            '5_star': round((self.five_star_reviews / self.total_reviews) * 100, 1),
            '4_star': round((self.four_star_reviews / self.total_reviews) * 100, 1),
            '3_star': round((self.three_star_reviews / self.total_reviews) * 100, 1),
            '2_star': round((self.two_star_reviews / self.total_reviews) * 100, 1),
            '1_star': round((self.one_star_reviews / self.total_reviews) * 100, 1)
        }
    
    def update_ratings(self):
        """Update aggregated ratings from reviews"""
        from sqlalchemy import func
        
        # Get rating aggregates from reviews
        rating_data = db.session.query(
            func.avg(Review.overall_rating).label('avg_overall'),
            func.avg(Review.teaching_quality).label('avg_teaching'),
            func.avg(Review.communication).label('avg_communication'),
            func.avg(Review.punctuality).label('avg_punctuality'),
            func.avg(Review.value_for_money).label('avg_value'),
            func.avg(Review.subject_knowledge).label('avg_knowledge'),
            func.avg(Review.patience).label('avg_patience'),
            func.count(Review.id).label('total'),
            func.sum(func.case([(Review.overall_rating == 5, 1)], else_=0)).label('five_star'),
            func.sum(func.case([(Review.overall_rating == 4, 1)], else_=0)).label('four_star'),
            func.sum(func.case([(Review.overall_rating == 3, 1)], else_=0)).label('three_star'),
            func.sum(func.case([(Review.overall_rating == 2, 1)], else_=0)).label('two_star'),
            func.sum(func.case([(Review.overall_rating == 1, 1)], else_=0)).label('one_star'),
            func.sum(func.case([(Review.is_verified_purchase == True, 1)], else_=0)).label('verified')
        ).filter_by(
            tutor_id=self.tutor_id,
            moderation_status='Approved',
            is_hidden=False
        ).first()
        
        if rating_data.total > 0:
            self.average_rating = float(rating_data.avg_overall) if rating_data.avg_overall else 0.0
            self.teaching_quality_avg = float(rating_data.avg_teaching) if rating_data.avg_teaching else 0.0
            self.communication_avg = float(rating_data.avg_communication) if rating_data.avg_communication else 0.0
            self.punctuality_avg = float(rating_data.avg_punctuality) if rating_data.avg_punctuality else 0.0
            self.value_for_money_avg = float(rating_data.avg_value) if rating_data.avg_value else 0.0
            self.subject_knowledge_avg = float(rating_data.avg_knowledge) if rating_data.avg_knowledge else 0.0
            self.patience_avg = float(rating_data.avg_patience) if rating_data.avg_patience else 0.0
            
            self.total_reviews = rating_data.total
            self.five_star_reviews = rating_data.five_star or 0
            self.four_star_reviews = rating_data.four_star or 0
            self.three_star_reviews = rating_data.three_star or 0
            self.two_star_reviews = rating_data.two_star or 0
            self.one_star_reviews = rating_data.one_star or 0
            self.verified_purchase_reviews = rating_data.verified or 0
        else:
            # Reset to defaults if no reviews
            self.average_rating = 0.0
            self.teaching_quality_avg = 0.0
            self.communication_avg = 0.0
            self.punctuality_avg = 0.0
            self.value_for_money_avg = 0.0
            self.subject_knowledge_avg = 0.0
            self.patience_avg = 0.0
            self.total_reviews = 0
            self.five_star_reviews = 0
            self.four_star_reviews = 0
            self.three_star_reviews = 0
            self.two_star_reviews = 0
            self.one_star_reviews = 0
            self.verified_purchase_reviews = 0
        
        self.last_updated = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'tutor_id': self.tutor_id,
            'tutor_profile_id': self.tutor_profile_id,
            'average_rating': round(self.average_rating, 1),
            'teaching_quality_avg': round(self.teaching_quality_avg, 1),
            'communication_avg': round(self.communication_avg, 1),
            'punctuality_avg': round(self.punctuality_avg, 1),
            'value_for_money_avg': round(self.value_for_money_avg, 1),
            'subject_knowledge_avg': round(self.subject_knowledge_avg, 1),
            'patience_avg': round(self.patience_avg, 1),
            'total_reviews': self.total_reviews,
            'five_star_reviews': self.five_star_reviews,
            'four_star_reviews': self.four_star_reviews,
            'three_star_reviews': self.three_star_reviews,
            'two_star_reviews': self.two_star_reviews,
            'one_star_reviews': self.one_star_reviews,
            'verified_purchase_reviews': self.verified_purchase_reviews,
            'rating_distribution': self.get_rating_distribution(),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }