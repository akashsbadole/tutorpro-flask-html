from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models.user import User
from app.models.booking import Booking


class PaymentMethod(db.Model):
    """
    Model for payment methods (UPI and PayPal integration)
    """
    __tablename__ = 'payment_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payment_type = db.Column(db.Enum('UPI', 'PayPal', 'Credit Card', 'Debit Card', name='payment_types'), 
                            nullable=False)
    method_details = db.Column(db.String(255), nullable=False)  # UPI ID, PayPal email, etc.
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='payment_methods')
    
    # Ensure only one default payment method per user
    def set_as_default(self):
        """Set this payment method as default for the user"""
        for payment_method in self.user.payment_methods:
            payment_method.is_default = False
        self.is_default = True
        db.session.commit()
    
    def __repr__(self):
        return f'<PaymentMethod {self.payment_type} for {self.user.email}>'


class Payment(db.Model):
    """
    Model for tracking transactions
    """
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.Enum('Pending', 'Completed', 'Failed', 'Refunded', name='payment_statuses'), 
                      nullable=False, default='Pending')
    payment_gateway = db.Column(db.String(50), nullable=False)  # 'PayPal', 'Razorpay', etc.
    gateway_transaction_id = db.Column(db.String(100))
    failure_reason = db.Column(db.Text)
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payment_method = db.relationship('PaymentMethod', backref='payments')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_payment_status', 'status'),
        db.Index('idx_payment_booking', 'booking_id'),
        db.Index('idx_payment_transaction', 'transaction_id'),
    )
    
    def __repr__(self):
        return f'<Payment {self.transaction_id} - {self.status}>'
    
    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'Completed'
    
    @property
    def is_pending(self):
        """Check if payment is pending"""
        return self.status == 'Pending'
    
    @property
    def is_failed(self):
        """Check if payment failed"""
        return self.status == 'Failed'
    
    def mark_as_completed(self):
        """Mark payment as completed"""
        self.status = 'Completed'
        self.processed_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_failed(self, reason=None):
        """Mark payment as failed"""
        self.status = 'Failed'
        self.failure_reason = reason
        db.session.commit()


class Transaction(db.Model):
    """
    Model for detailed payment records
    """
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    transaction_type = db.Column(db.Enum('Payment', 'Refund', 'Payout', name='transaction_types'), 
                               nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('Pending', 'Completed', 'Failed', name='transaction_statuses'), 
                      nullable=False, default='Pending')
    reference_id = db.Column(db.String(100))  # External reference ID
    gateway_response = db.Column(db.Text)  # Raw response from payment gateway
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    payment = db.relationship('Payment', backref='transactions')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_transaction_status', 'status'),
        db.Index('idx_transaction_payment', 'payment_id'),
    )
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type} - {self.status}>'
    
    @property
    def is_successful(self):
        """Check if transaction was successful"""
        return self.status == 'Completed'
    
    def mark_as_completed(self):
        """Mark transaction as completed"""
        self.status = 'Completed'
        self.completed_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_failed(self):
        """Mark transaction as failed"""
        self.status = 'Failed'
        db.session.commit()


class Payout(db.Model):
    """
    Model for tutor payouts
    """
    __tablename__ = 'payouts'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    payout_method = db.Column(db.Enum('Bank Transfer', 'UPI', 'PayPal', name='payout_methods'), 
                             nullable=False)
    payout_details = db.Column(db.String(255), nullable=False)  # Bank details, UPI ID, etc.
    status = db.Column(db.Enum('Pending', 'Processing', 'Completed', 'Failed', name='payout_statuses'), 
                      nullable=False, default='Pending')
    reference_id = db.Column(db.String(100))  # Payout reference from gateway
    failure_reason = db.Column(db.Text)
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tutor = db.relationship('TutorProfile', backref='payouts')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_payout_status', 'status'),
        db.Index('idx_payout_tutor', 'tutor_id'),
    )
    
    def __repr__(self):
        return f'<Payout {self.id} - {self.status}>'
    
    @property
    def is_successful(self):
        """Check if payout was successful"""
        return self.status == 'Completed'
    
    def mark_as_completed(self):
        """Mark payout as completed"""
        self.status = 'Completed'
        self.processed_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_failed(self, reason=None):
        """Mark payout as failed"""
        self.status = 'Failed'
        self.failure_reason = reason
        db.session.commit()