"""
Enterprise Models for TutorPro
Handles organization management, corporate training, and B2B features
"""

from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, JSON, Enum
from sqlalchemy.orm import relationship
import enum

class OrganizationType(enum.Enum):
    ENTERPRISE = "enterprise"
    EDUCATIONAL = "educational"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"

class Organization(db.Model):
    """Organization model for B2B customers"""
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    type = Column(Enum(OrganizationType), default=OrganizationType.ENTERPRISE)
    description = Column(Text)
    industry = Column(String(100))
    size = Column(String(50))  # small, medium, large, enterprise
    website = Column(String(255))
    logo_url = Column(String(500))
    contact_email = Column(String(120), nullable=False)
    contact_phone = Column(String(50))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Billing and subscription
    subscription_plan = Column(String(50))  # basic, professional, enterprise
    subscription_status = Column(String(20), default='active')  # active, suspended, cancelled
    billing_cycle = Column(String(20))  # monthly, annual
    max_users = Column(Integer, default=100)
    current_users = Column(Integer, default=0)
    
    # Branding and customization
    primary_color = Column(String(7), default='#007bff')
    secondary_color = Column(String(7), default='#6c757d')
    custom_logo_url = Column(String(500))
    custom_domain = Column(String(255))
    
    # Features and permissions
    features = Column(JSON)  # Store enabled features as JSON
    api_access_enabled = Column(Boolean, default=False)
    sso_enabled = Column(Boolean, default=False)
    
    # Compliance and security
    compliance_requirements = Column(JSON)  # Store compliance requirements
    data_retention_days = Column(Integer, default=365)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    admin_id = Column(Integer, ForeignKey('users.id'))
    admin = relationship('User', foreign_keys=[admin_id], backref='managed_organizations')
    
    users = relationship('OrganizationUser', back_populates='organization', cascade='all, delete-orphan')
    departments = relationship('Department', back_populates='organization', cascade='all, delete-orphan')
    training_programs = relationship('TrainingProgram', back_populates='organization', cascade='all, delete-orphan')
    billing_invoices = relationship('BillingInvoice', back_populates='organization', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Organization {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value if self.type else None,
            'description': self.description,
            'industry': self.industry,
            'size': self.size,
            'website': self.website,
            'logo_url': self.logo_url,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'subscription_plan': self.subscription_plan,
            'subscription_status': self.subscription_status,
            'billing_cycle': self.billing_cycle,
            'max_users': self.max_users,
            'current_users': self.current_users,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'custom_logo_url': self.custom_logo_url,
            'custom_domain': self.custom_domain,
            'features': self.features,
            'api_access_enabled': self.api_access_enabled,
            'sso_enabled': self.sso_enabled,
            'compliance_requirements': self.compliance_requirements,
            'data_retention_days': self.data_retention_days,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Department(db.Model):
    """Department model for organization structure"""
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    head_of_department_id = Column(Integer, ForeignKey('users.id'))
    budget_allocated = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='departments')
    head_of_department = relationship('User', foreign_keys=[head_of_department_id], backref='managed_departments')
    users = relationship('OrganizationUser', back_populates='department')
    
    def __repr__(self):
        return f'<Department {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'name': self.name,
            'description': self.description,
            'head_of_department_id': self.head_of_department_id,
            'budget_allocated': self.budget_allocated,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class OrganizationUser(db.Model):
    """Association table for organization users"""
    __tablename__ = 'organization_users'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'))
    role = Column(String(50), nullable=False)  # admin, manager, employee, learner
    job_title = Column(String(100))
    
    # Permissions and access
    permissions = Column(JSON)  # Store specific permissions as JSON
    access_level = Column(String(20))  # full, limited, read_only
    can_manage_users = Column(Boolean, default=False)
    can_view_analytics = Column(Boolean, default=False)
    can_manage_billing = Column(Boolean, default=False)
    
    # Training and compliance
    training_completed = Column(JSON)  # Store completed training modules
    compliance_status = Column(String(20), default='pending')
    last_login_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='users')
    user = relationship('User', backref='organization_memberships')
    department = relationship('Department', back_populates='users')
    
    def __repr__(self):
        return f'<OrganizationUser {self.user_id} in {self.organization_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'user_id': self.user_id,
            'department_id': self.department_id,
            'role': self.role,
            'job_title': self.job_title,
            'permissions': self.permissions,
            'access_level': self.access_level,
            'can_manage_users': self.can_manage_users,
            'can_view_analytics': self.can_view_analytics,
            'can_manage_billing': self.can_manage_billing,
            'training_completed': self.training_completed,
            'compliance_status': self.compliance_status,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TrainingProgram(db.Model):
    """Training program model for corporate training"""
    __tablename__ = 'training_programs'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # compliance, skills, onboarding, etc.
    
    # Training details
    duration_hours = Column(Float, default=0.0)
    required_completion_days = Column(Integer, default=30)
    max_participants = Column(Integer, default=0)
    is_mandatory = Column(Boolean, default=False)
    
    # Content and materials
    content = Column(Text)
    materials_url = Column(String(500))
    assessment_required = Column(Boolean, default=False)
    passing_score = Column(Float, default=70.0)
    
    # Status and scheduling
    status = Column(String(20), default='draft')  # draft, active, completed, archived
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='training_programs')
    enrollments = relationship('TrainingEnrollment', back_populates='training_program', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TrainingProgram {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'duration_hours': self.duration_hours,
            'required_completion_days': self.required_completion_days,
            'max_participants': self.max_participants,
            'is_mandatory': self.is_mandatory,
            'content': self.content,
            'materials_url': self.materials_url,
            'assessment_required': self.assessment_required,
            'passing_score': self.passing_score,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TrainingEnrollment(db.Model):
    """Training enrollment model for tracking participant progress"""
    __tablename__ = 'training_enrollments'
    
    id = Column(Integer, primary_key=True)
    training_program_id = Column(Integer, ForeignKey('training_programs.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(DateTime)
    
    # Progress and performance
    progress_percentage = Column(Float, default=0.0)
    score_achieved = Column(Float)
    status = Column(String(20), default='enrolled')  # enrolled, in_progress, completed, failed, dropped
    
    # Feedback and assessment
    feedback_rating = Column(Integer)  # 1-5 scale
    feedback_comments = Column(Text)
    certificate_issued = Column(Boolean, default=False)
    certificate_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    training_program = relationship('TrainingProgram', back_populates='enrollments')
    user = relationship('User', backref='training_enrollments')
    
    def __repr__(self):
        return f'<TrainingEnrollment {self.user_id} in {self.training_program_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'training_program_id': self.training_program_id,
            'user_id': self.user_id,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'progress_percentage': self.progress_percentage,
            'score_achieved': self.score_achieved,
            'status': self.status,
            'feedback_rating': self.feedback_rating,
            'feedback_comments': self.feedback_comments,
            'certificate_issued': self.certificate_issued,
            'certificate_url': self.certificate_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BillingInvoice(db.Model):
    """Billing invoice model for enterprise customers"""
    __tablename__ = 'billing_invoices'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    invoice_number = Column(String(50), nullable=False, unique=True)
    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    
    # Billing details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    billing_period_start = Column(DateTime)
    billing_period_end = Column(DateTime)
    
    # Status and payment
    status = Column(String(20), default='issued')  # issued, paid, overdue, cancelled
    payment_method = Column(String(50))
    payment_date = Column(DateTime)
    
    # Line items (stored as JSON)
    line_items = Column(JSON)  # Array of billing items
    
    # Notes and metadata
    notes = Column(Text)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', back_populates='billing_invoices')
    
    def __repr__(self):
        return f'<BillingInvoice {self.invoice_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'invoice_number': self.invoice_number,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'amount': self.amount,
            'currency': self.currency,
            'billing_period_start': self.billing_period_start.isoformat() if self.billing_period_start else None,
            'billing_period_end': self.billing_period_end.isoformat() if self.billing_period_end else None,
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'line_items': self.line_items,
            'notes': self.notes,
            'tax_amount': self.tax_amount,
            'discount_amount': self.discount_amount,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BulkOperation(db.Model):
    """Bulk operation tracking for enterprise features"""
    __tablename__ = 'bulk_operations'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    operation_type = Column(String(50), nullable=False)  # user_import, course_creation, etc.
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    
    # Operation details
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    error_details = Column(JSON)  # Store error details as JSON
    
    # File and data
    source_file_url = Column(String(500))
    results_summary = Column(JSON)  # Summary of operation results
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization')
    creator = relationship('User', foreign_keys=[created_by], backref='bulk_operations')
    
    def __repr__(self):
        return f'<BulkOperation {self.operation_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'operation_type': self.operation_type,
            'status': self.status,
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'failed_items': self.failed_items,
            'error_details': self.error_details,
            'source_file_url': self.source_file_url,
            'results_summary': self.results_summary,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }