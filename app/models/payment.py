from datetime import datetime
from app import db

class Payment(db.Model):
    """
    Payment records for bookings and marketplace transactions
    """
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Associated entities
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    payment_type = db.Column(db.Enum(
        'Session Fee', 
        'Package Purchase', 
        'Subscription', 
        'Workshop Fee', 
        'Material Fee',
        name='payment_types'
    ), nullable=False, default='Session Fee')
    
    # Payment method
    payment_method = db.Column(db.Enum(
        'Credit Card', 
        'Debit Card', 
        'PayPal', 
        'Stripe', 
        'Bank Transfer', 
        'UPI', 
        'Wallet',
        name='payment_methods'
    ), nullable=False)
    
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'))
    
    # Gateway information
    gateway = db.Column(db.String(50))  # Stripe, PayPal, etc.
    gateway_transaction_id = db.Column(db.String(100))  # Transaction ID from gateway
    gateway_payment_intent_id = db.Column(db.String(100))  # Payment intent ID
    gateway_status = db.Column(db.String(50))  # Status from gateway
    
    # Status tracking
    status = db.Column(db.Enum(
        'Pending', 
        'Processing', 
        'Completed', 
        'Failed', 
        'Cancelled', 
        'Refunded', 
        'Partially Refunded',
        name='payment_statuses'
    ), nullable=False, default='Pending', index=True)
    
    # Fee breakdown
    platform_fee = db.Column(db.Numeric(10, 2), default=0)  # Platform commission
    payment_gateway_fee = db.Column(db.Numeric(10, 2), default=0)  # Gateway fees
    net_amount_to_tutor = db.Column(db.Numeric(10, 2))  # Amount after fees
    
    # Refund information
    refund_amount = db.Column(db.Numeric(10, 2), default=0)
    refund_reason = db.Column(db.Text)
    refund_date = db.Column(db.DateTime)
    refund_id = db.Column(db.String(100))  # Refund transaction ID
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
    
    # Relationships
    booking = db.relationship('Booking', backref='payment_records')
    student = db.relationship('User', foreign_keys=[student_id], backref='payments_made')
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='payments_received')
    payment_method_obj = db.relationship('PaymentMethod', backref='payments')
    refunds = db.relationship('Refund', backref='payment_refunds', lazy='dynamic')
    
    def __repr__(self):
        return f'<Payment {self.id}: {self.amount} {self.currency} ({self.status})>'
    
    def calculate_fees(self):
        """Calculate platform and gateway fees"""
        # Platform fee (typically 10-20%)
        platform_fee_rate = 0.15  # 15% platform fee
        self.platform_fee = float(self.amount) * platform_fee_rate
        
        # Gateway fee (typically 2.9% + $0.30 for cards)
        gateway_fee_rate = 0.029  # 2.9%
        gateway_fee_fixed = 0.30   # $0.30
        self.payment_gateway_fee = (float(self.amount) * gateway_fee_rate) + gateway_fee_fixed
        
        # Calculate net amount to tutor
        self.net_amount_to_tutor = float(self.amount) - self.platform_fee - self.payment_gateway_fee
    
    def can_be_refunded(self):
        """Check if payment can be refunded"""
        if self.status not in ['Completed']:
            return False
        
        # Check refund time window (e.g., 30 days)
        if self.completed_at:
            days_since_completion = (datetime.utcnow() - self.completed_at).days
            return days_since_completion <= 30
        
        return False
    
    def get_refundable_amount(self):
        """Get amount that can be refunded"""
        if not self.can_be_refunded():
            return 0
        
        return float(self.amount) - float(self.refund_amount or 0)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'booking_id': self.booking_id,
            'student_id': self.student_id,
            'tutor_id': self.tutor_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'payment_type': self.payment_type,
            'payment_method': self.payment_method,
            'payment_method_id': self.payment_method_id,
            'gateway': self.gateway,
            'gateway_transaction_id': self.gateway_transaction_id if include_sensitive else None,
            'gateway_payment_intent_id': self.gateway_payment_intent_id if include_sensitive else None,
            'gateway_status': self.gateway_status,
            'status': self.status,
            'platform_fee': float(self.platform_fee) if self.platform_fee else 0,
            'payment_gateway_fee': float(self.payment_gateway_fee) if self.payment_gateway_fee else 0,
            'net_amount_to_tutor': float(self.net_amount_to_tutor) if self.net_amount_to_tutor else 0,
            'refund_amount': float(self.refund_amount) if self.refund_amount else 0,
            'refund_reason': self.refund_reason,
            'refund_date': self.refund_date.isoformat() if self.refund_date else None,
            'refund_id': self.refund_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'can_be_refunded': self.can_be_refunded(),
            'refundable_amount': self.get_refundable_amount()
        }
        
        return data


class PaymentMethod(db.Model):
    """
    User payment methods for marketplace transactions
    """
    __tablename__ = 'payment_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Method details
    method_type = db.Column(db.Enum(
        'Credit Card', 
        'Debit Card', 
        'PayPal', 
        'Bank Account', 
        'UPI', 
        'Digital Wallet',
        name='payment_method_types'
    ), nullable=False)
    
    # Card details (encrypted)
    card_last_four = db.Column(db.String(4))
    card_brand = db.Column(db.String(50))  # Visa, Mastercard, etc.
    card_expiry_month = db.Column(db.Integer)
    card_expiry_year = db.Column(db.Integer)
    
    # Gateway details
    gateway = db.Column(db.String(50))  # Stripe, PayPal, etc.
    gateway_method_id = db.Column(db.String(100))  # Method ID from gateway
    gateway_customer_id = db.Column(db.String(100))  # Customer ID from gateway
    
    # Bank details (encrypted)
    bank_name = db.Column(db.String(100))
    bank_account_last_four = db.Column(db.String(4))
    bank_routing_number = db.Column(db.String(50))
    
    # PayPal details
    paypal_email = db.Column(db.String(255))
    paypal_user_id = db.Column(db.String(100))
    
    # UPI details
    upi_id = db.Column(db.String(100))
    upi_provider = db.Column(db.String(50))
    
    # Status
    is_verified = db.Column(db.Boolean, default=False)
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Usage limits
    daily_limit = db.Column(db.Numeric(10, 2))
    monthly_limit = db.Column(db.Numeric(10, 2))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='payment_methods')
    
    def __repr__(self):
        return f'<PaymentMethod {self.id}: {self.method_type} for user {self.user_id}>'
    
    def is_expired(self):
        """Check if payment method is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def get_display_name(self):
        """Get user-friendly display name"""
        if self.method_type in ['Credit Card', 'Debit Card']:
            return f"{self.card_brand} ending in {self.card_last_four}"
        elif self.method_type == 'PayPal':
            return f"PayPal ({self.paypal_email})"
        elif self.method_type == 'Bank Account':
            return f"{self.bank_name} ending in {self.bank_account_last_four}"
        elif self.method_type == 'UPI':
            return f"UPI ({self.upi_id})"
        else:
            return self.method_type
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'method_type': self.method_type,
            'card_brand': self.card_brand,
            'card_last_four': self.card_last_four,
            'card_expiry_month': self.card_expiry_month,
            'card_expiry_year': self.card_expiry_year,
            'gateway': self.gateway,
            'bank_name': self.bank_name,
            'bank_account_last_four': self.bank_account_last_four,
            'paypal_email': self.paypal_email,
            'upi_id': self.upi_id,
            'upi_provider': self.upi_provider,
            'is_verified': self.is_verified,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'daily_limit': float(self.daily_limit) if self.daily_limit else None,
            'monthly_limit': float(self.monthly_limit) if self.monthly_limit else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired(),
            'display_name': self.get_display_name()
        }
        
        if include_sensitive:
            data['gateway_method_id'] = self.gateway_method_id
            data['gateway_customer_id'] = self.gateway_customer_id
            data['bank_routing_number'] = self.bank_routing_number
            data['paypal_user_id'] = self.paypal_user_id
            
        return data


class Payout(db.Model):
    """
    Tutor payout records
    """
    __tablename__ = 'payouts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Payout details
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    
    # Payout method
    payout_method = db.Column(db.Enum(
        'Bank Transfer', 
        'PayPal', 
        'Stripe', 
        'Check', 
        'UPI',
        name='payout_methods'
    ), nullable=False)
    
    payout_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'))
    
    # Gateway information
    gateway = db.Column(db.String(50))
    gateway_payout_id = db.Column(db.String(100))
    gateway_status = db.Column(db.String(50))
    
    # Status
    status = db.Column(db.Enum(
        'Pending', 
        'Processing', 
        'Completed', 
        'Failed', 
        'Cancelled',
        name='payout_statuses'
    ), nullable=False, default='Pending', index=True)
    
    # Fee information
    processing_fee = db.Column(db.Numeric(10, 2), default=0)
    net_amount = db.Column(db.Numeric(10, 2))
    
    # Associated payments
    payment_ids = db.Column(db.Text)  # JSON array of payment IDs included in this payout
    
    # Processing details
    processed_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    failure_reason = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tutor = db.relationship('User', backref='payouts')
    payment_method_obj = db.relationship('PaymentMethod', backref='payouts')
    
    def __repr__(self):
        return f'<Payout {self.id}: {self.amount} {self.currency} to tutor {self.tutor_id}>'
    
    def get_payment_ids_list(self):
        """Get list of payment IDs"""
        import json
        try:
            return json.loads(self.payment_ids) if self.payment_ids else []
        except:
            return []
    
    def calculate_net_amount(self):
        """Calculate net amount after processing fees"""
        processing_fee_rate = 0.02  # 2% processing fee
        self.processing_fee = float(self.amount) * processing_fee_rate
        self.net_amount = float(self.amount) - self.processing_fee
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'tutor_id': self.tutor_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'payout_method': self.payout_method,
            'payout_method_id': self.payout_method_id,
            'gateway': self.gateway,
            'gateway_payout_id': self.gateway_payout_id,
            'gateway_status': self.gateway_status,
            'status': self.status,
            'processing_fee': float(self.processing_fee) if self.processing_fee else 0,
            'net_amount': float(self.net_amount) if self.net_amount else 0,
            'payment_ids': self.get_payment_ids_list(),
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'failure_reason': self.failure_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Refund(db.Model):
    """
    Refund records for payments
    """
    __tablename__ = 'refunds'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Associated payment
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False, index=True)
    
    # Refund details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    reason = db.Column(db.Text)
    
    # Gateway information
    gateway_refund_id = db.Column(db.String(100))
    gateway_status = db.Column(db.String(50))
    
    # Status
    status = db.Column(db.Enum(
        'Pending', 
        'Processing', 
        'Completed', 
        'Failed', 
        'Cancelled',
        name='refund_statuses'
    ), nullable=False, default='Pending', index=True)
    
    # Processing details
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin who processed
    processing_notes = db.Column(db.Text)
    failure_reason = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    payment = db.relationship('Payment', backref='refund_records')
    processor = db.relationship('User', backref='processed_refunds')
    
    def __repr__(self):
        return f'<Refund {self.id}: {self.amount} {self.currency} for payment {self.payment_id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'reason': self.reason,
            'gateway_refund_id': self.gateway_refund_id,
            'gateway_status': self.gateway_status,
            'status': self.status,
            'processed_by': self.processed_by,
            'processing_notes': self.processing_notes,
            'failure_reason': self.failure_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class Transaction(db.Model):
    """
    General transaction log for all financial activities
    """
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Transaction details
    transaction_type = db.Column(db.Enum(
        'Payment', 
        'Refund', 
        'Payout', 
        'Fee', 
        'Adjustment', 
        'Bonus',
        name='transaction_types'
    ), nullable=False)
    
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    
    # Associated entities
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    related_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)  # Other party in transaction
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), index=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), index=True)
    refund_id = db.Column(db.Integer, db.ForeignKey('refunds.id'), index=True)
    payout_id = db.Column(db.Integer, db.ForeignKey('payouts.id'), index=True)
    
    # Description
    description = db.Column(db.Text)
    reference_id = db.Column(db.String(100))  # External reference
    
    # Balance impact
    balance_before = db.Column(db.Numeric(10, 2))
    balance_after = db.Column(db.Numeric(10, 2))
    
    # Status
    status = db.Column(db.Enum(
        'Pending', 
        'Completed', 
        'Failed', 
        'Cancelled',
        name='transaction_statuses'
    ), nullable=False, default='Pending')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='transactions')
    related_user = db.relationship('User', foreign_keys=[related_user_id])
    booking = db.relationship('Booking', backref='transactions')
    payment = db.relationship('Payment', backref='transactions')
    refund = db.relationship('Refund', backref='transactions')
    payout = db.relationship('Payout', backref='transactions')
    
    def __repr__(self):
        return f'<Transaction {self.id}: {self.transaction_type} {self.amount} {self.currency}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount),
            'currency': self.currency,
            'user_id': self.user_id,
            'related_user_id': self.related_user_id,
            'booking_id': self.booking_id,
            'payment_id': self.payment_id,
            'refund_id': self.refund_id,
            'payout_id': self.payout_id,
            'description': self.description,
            'reference_id': self.reference_id,
            'balance_before': float(self.balance_before) if self.balance_before else None,
            'balance_after': float(self.balance_after) if self.balance_after else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }