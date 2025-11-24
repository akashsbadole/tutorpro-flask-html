"""
Enterprise Service for TutorPro
Handles business logic for organization management, corporate training, and B2B features
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import current_app
from sqlalchemy import func, and_, or_
from app import db
from app.models.enterprise import (
    Organization, Department, OrganizationUser, TrainingProgram, 
    TrainingEnrollment, BillingInvoice, BulkOperation, OrganizationType
)
from app.models.user import User
from app.models.course import Course
from app.models.booking import Booking
from app.models.payment import Payment
import csv
import io
import uuid


class EnterpriseService:
    """Service class for enterprise operations"""
    
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.supported_import_formats = ['csv', 'xlsx']
    
    # Organization Management Methods
    
    def create_organization(self, org_data: Dict, admin_user_id: int) -> Organization:
        """Create a new organization with admin user"""
        try:
            organization = Organization(
                name=org_data['name'],
                type=OrganizationType(org_data.get('type', 'enterprise')),
                description=org_data.get('description', ''),
                industry=org_data.get('industry', ''),
                size=org_data.get('size', 'small'),
                website=org_data.get('website', ''),
                contact_email=org_data['contact_email'],
                contact_phone=org_data.get('contact_phone', ''),
                address=org_data.get('address', ''),
                city=org_data.get('city', ''),
                state=org_data.get('state', ''),
                country=org_data.get('country', ''),
                postal_code=org_data.get('postal_code', ''),
                subscription_plan=org_data.get('subscription_plan', 'basic'),
                subscription_status='active',
                billing_cycle=org_data.get('billing_cycle', 'monthly'),
                max_users=org_data.get('max_users', 100),
                primary_color=org_data.get('primary_color', '#007bff'),
                secondary_color=org_data.get('secondary_color', '#6c757d'),
                features=org_data.get('features', {}),
                admin_id=admin_user_id
            )
            
            db.session.add(organization)
            db.session.flush()  # Get the organization ID
            
            # Add admin as organization user
            admin_user = OrganizationUser(
                organization_id=organization.id,
                user_id=admin_user_id,
                role='admin',
                access_level='full',
                can_manage_users=True,
                can_view_analytics=True,
                can_manage_billing=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            current_app.logger.info(f"Created organization: {organization.name} with admin user {admin_user_id}")
            return organization
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating organization: {str(e)}")
            raise
    
    def update_organization(self, organization_id: int, org_data: Dict) -> Optional[Organization]:
        """Update organization details"""
        try:
            organization = Organization.query.get(organization_id)
            if not organization:
                return None
            
            # Update organization fields
            for key, value in org_data.items():
                if hasattr(organization, key) and key not in ['id', 'admin_id', 'created_at']:
                    setattr(organization, key, value)
            
            organization.updated_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"Updated organization: {organization.name}")
            return organization
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating organization: {str(e)}")
            raise
    
    def get_organization_analytics(self, organization_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Get comprehensive analytics for an organization"""
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Basic organization info
            org = Organization.query.get(organization_id)
            if not org:
                return {}
            
            # User analytics
            total_users = db.session.query(func.count(OrganizationUser.id))\
                .filter(OrganizationUser.organization_id == organization_id).scalar()
            
            active_users = db.session.query(func.count(OrganizationUser.id))\
                .filter(
                    OrganizationUser.organization_id == organization_id,
                    OrganizationUser.last_login_at >= start_date
                ).scalar()
            
            # Department analytics
            total_departments = db.session.query(func.count(Department.id))\
                .filter(Department.organization_id == organization_id).scalar()
            
            # Training analytics
            total_programs = db.session.query(func.count(TrainingProgram.id))\
                .filter(TrainingProgram.organization_id == organization_id).scalar()
            
            active_programs = db.session.query(func.count(TrainingProgram.id))\
                .filter(
                    TrainingProgram.organization_id == organization_id,
                    TrainingProgram.status == 'active'
                ).scalar()
            
            total_enrollments = db.session.query(func.count(TrainingEnrollment.id))\
                .join(TrainingProgram, TrainingEnrollment.training_program_id == TrainingProgram.id)\
                .filter(TrainingProgram.organization_id == organization_id).scalar()
            
            completed_enrollments = db.session.query(func.count(TrainingEnrollment.id))\
                .join(TrainingProgram, TrainingEnrollment.training_program_id == TrainingProgram.id)\
                .filter(
                    TrainingProgram.organization_id == organization_id,
                    TrainingEnrollment.status == 'completed'
                ).scalar()
            
            # Learning analytics
            total_hours = db.session.query(func.sum(Booking.duration_hours))\
                .join(OrganizationUser, Booking.student_id == OrganizationUser.user_id)\
                .filter(
                    OrganizationUser.organization_id == organization_id,
                    Booking.status == 'completed',
                    Booking.created_at >= start_date,
                    Booking.created_at <= end_date
                ).scalar() or 0
            
            # Financial analytics
            total_spending = db.session.query(func.sum(Payment.amount))\
                .join(OrganizationUser, Payment.user_id == OrganizationUser.user_id)\
                .filter(
                    OrganizationUser.organization_id == organization_id,
                    Payment.status == 'completed',
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date
                ).scalar() or 0
            
            # Department-wise distribution
            department_stats = db.session.query(
                Department.name,
                func.count(OrganizationUser.id).label('user_count'),
                func.sum(Booking.duration_hours).label('total_hours')
            ).join(OrganizationUser, Department.id == OrganizationUser.department_id)\
             .outerjoin(Booking, Booking.student_id == OrganizationUser.user_id)\
             .filter(
                 Department.organization_id == organization_id,
                 Booking.status == 'completed'
             ).group_by(Department.id).all()
            
            return {
                'organization_id': organization_id,
                'organization_name': org.name,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'user_analytics': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'user_engagement_rate': (active_users / total_users * 100) if total_users > 0 else 0
                },
                'department_analytics': {
                    'total_departments': total_departments,
                    'department_stats': [
                        {
                            'name': dept.name,
                            'user_count': dept.user_count or 0,
                            'total_hours': float(dept.total_hours or 0)
                        } for dept in department_stats
                    ]
                },
                'training_analytics': {
                    'total_programs': total_programs,
                    'active_programs': active_programs,
                    'total_enrollments': total_enrollments,
                    'completed_enrollments': completed_enrollments,
                    'completion_rate': (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
                },
                'learning_analytics': {
                    'total_learning_hours': float(total_hours),
                    'average_hours_per_user': float(total_hours / active_users) if active_users > 0 else 0
                },
                'financial_analytics': {
                    'total_spending': float(total_spending),
                    'average_spending_per_user': float(total_spending / active_users) if active_users > 0 else 0
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting organization analytics: {str(e)}")
            raise
    
    # User Management Methods
    
    def add_user_to_organization(self, organization_id: int, user_data: Dict) -> OrganizationUser:
        """Add a user to an organization"""
        try:
            # Check if user exists
            user = User.query.filter_by(email=user_data['email']).first()
            
            if not user:
                # Create new user
                user = User(
                    email=user_data['email'],
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    phone=user_data.get('phone', ''),
                    role='learner'
                )
                user.set_password(user_data.get('password', 'TempPassword123!'))
                db.session.add(user)
                db.session.flush()
            
            # Check if user is already in organization
            existing_membership = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=user.id
            ).first()
            
            if existing_membership:
                raise ValueError(f"User {user.email} is already a member of this organization")
            
            # Create organization user
            org_user = OrganizationUser(
                organization_id=organization_id,
                user_id=user.id,
                role=user_data.get('role', 'employee'),
                department_id=user_data.get('department_id'),
                job_title=user_data.get('job_title', ''),
                access_level=user_data.get('access_level', 'limited'),
                can_manage_users=user_data.get('can_manage_users', False),
                can_view_analytics=user_data.get('can_view_analytics', False),
                can_manage_billing=user_data.get('can_manage_billing', False)
            )
            
            db.session.add(org_user)
            
            # Update organization user count
            organization = Organization.query.get(organization_id)
            if organization:
                organization.current_users += 1
            
            db.session.commit()
            
            current_app.logger.info(f"Added user {user.email} to organization {organization_id}")
            return org_user
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding user to organization: {str(e)}")
            raise
    
    def bulk_import_users(self, organization_id: int, file_content: str, file_format: str = 'csv') -> BulkOperation:
        """Bulk import users from CSV file"""
        try:
            # Create bulk operation record
            bulk_op = BulkOperation(
                organization_id=organization_id,
                operation_type='user_import',
                status='processing',
                total_items=0
            )
            db.session.add(bulk_op)
            db.session.flush()
            
            # Parse file content
            if file_format == 'csv':
                users_data = self._parse_csv_users(file_content)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            bulk_op.total_items = len(users_data)
            processed_items = 0
            failed_items = 0
            errors = []
            
            # Process each user
            for user_data in users_data:
                try:
                    self.add_user_to_organization(organization_id, user_data)
                    processed_items += 1
                except Exception as e:
                    failed_items += 1
                    errors.append({
                        'row': processed_items + failed_items,
                        'data': user_data,
                        'error': str(e)
                    })
            
            # Update bulk operation
            bulk_op.processed_items = processed_items
            bulk_op.failed_items = failed_items
            bulk_op.error_details = errors
            bulk_op.status = 'completed' if failed_items == 0 else 'completed_with_errors'
            bulk_op.completed_at = datetime.utcnow()
            bulk_op.results_summary = {
                'processed': processed_items,
                'failed': failed_items,
                'success_rate': (processed_items / len(users_data) * 100) if users_data else 0
            }
            
            db.session.commit()
            
            current_app.logger.info(f"Bulk import completed for organization {organization_id}: {processed_items} processed, {failed_items} failed")
            return bulk_op
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in bulk import: {str(e)}")
            
            if bulk_op:
                bulk_op.status = 'failed'
                bulk_op.error_details = [{'error': str(e)}]
                bulk_op.completed_at = datetime.utcnow()
                db.session.commit()
            
            raise
    
    def _parse_csv_users(self, file_content: str) -> List[Dict]:
        """Parse CSV content for user import"""
        users = []
        try:
            csv_reader = csv.DictReader(io.StringIO(file_content))
            for row in csv_reader:
                users.append({
                    'email': row.get('email', '').strip(),
                    'first_name': row.get('first_name', '').strip(),
                    'last_name': row.get('last_name', '').strip(),
                    'phone': row.get('phone', '').strip(),
                    'role': row.get('role', 'employee').strip(),
                    'job_title': row.get('job_title', '').strip(),
                    'department_name': row.get('department_name', '').strip()
                })
        except Exception as e:
            raise ValueError(f"Error parsing CSV file: {str(e)}")
        
        return users
    
    # Training Program Methods
    
    def create_training_program(self, organization_id: int, program_data: Dict) -> TrainingProgram:
        """Create a new training program"""
        try:
            program = TrainingProgram(
                organization_id=organization_id,
                name=program_data['name'],
                description=program_data.get('description', ''),
                category=program_data.get('category', 'skills'),
                duration_hours=program_data.get('duration_hours', 0.0),
                required_completion_days=program_data.get('required_completion_days', 30),
                max_participants=program_data.get('max_participants', 0),
                is_mandatory=program_data.get('is_mandatory', False),
                content=program_data.get('content', ''),
                materials_url=program_data.get('materials_url', ''),
                assessment_required=program_data.get('assessment_required', False),
                passing_score=program_data.get('passing_score', 70.0),
                start_date=datetime.fromisoformat(program_data['start_date']) if program_data.get('start_date') else None,
                end_date=datetime.fromisoformat(program_data['end_date']) if program_data.get('end_date') else None,
                status='active'
            )
            
            db.session.add(program)
            db.session.commit()
            
            current_app.logger.info(f"Created training program: {program.name} for organization {organization_id}")
            return program
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating training program: {str(e)}")
            raise
    
    def enroll_users_in_training(self, program_id: int, user_ids: List[int]) -> List[TrainingEnrollment]:
        """Enroll multiple users in a training program"""
        try:
            enrollments = []
            program = TrainingProgram.query.get(program_id)
            
            if not program:
                raise ValueError(f"Training program {program_id} not found")
            
            for user_id in user_ids:
                # Check if user is already enrolled
                existing = TrainingEnrollment.query.filter_by(
                    training_program_id=program_id,
                    user_id=user_id
                ).first()
                
                if existing:
                    continue
                
                enrollment = TrainingEnrollment(
                    training_program_id=program_id,
                    user_id=user_id,
                    status='enrolled'
                )
                
                db.session.add(enrollment)
                enrollments.append(enrollment)
            
            db.session.commit()
            
            current_app.logger.info(f"Enrolled {len(enrollments)} users in training program {program_id}")
            return enrollments
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error enrolling users in training: {str(e)}")
            raise
    
    def update_training_progress(self, enrollment_id: int, progress_data: Dict) -> Optional[TrainingEnrollment]:
        """Update training enrollment progress"""
        try:
            enrollment = TrainingEnrollment.query.get(enrollment_id)
            if not enrollment:
                return None
            
            enrollment.progress_percentage = progress_data.get('progress_percentage', enrollment.progress_percentage)
            enrollment.status = progress_data.get('status', enrollment.status)
            
            if progress_data.get('score_achieved'):
                enrollment.score_achieved = progress_data['score_achieved']
            
            if progress_data.get('feedback_rating'):
                enrollment.feedback_rating = progress_data['feedback_rating']
            
            if progress_data.get('feedback_comments'):
                enrollment.feedback_comments = progress_data['feedback_comments']
            
            if enrollment.status == 'completed':
                enrollment.completion_date = datetime.utcnow()
                if enrollment.score_achieved and enrollment.score_achieved >= enrollment.training_program.passing_score:
                    enrollment.certificate_issued = True
            
            enrollment.updated_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"Updated training progress for enrollment {enrollment_id}")
            return enrollment
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating training progress: {str(e)}")
            raise
    
    # Billing Methods
    
    def generate_invoice(self, organization_id: int, billing_data: Dict) -> BillingInvoice:
        """Generate billing invoice for organization"""
        try:
            invoice_number = f"INV-{organization_id}-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            
            invoice = BillingInvoice(
                organization_id=organization_id,
                invoice_number=invoice_number,
                amount=billing_data['amount'],
                currency=billing_data.get('currency', 'USD'),
                billing_period_start=datetime.fromisoformat(billing_data['billing_period_start']) if billing_data.get('billing_period_start') else datetime.utcnow() - timedelta(days=30),
                billing_period_end=datetime.fromisoformat(billing_data['billing_period_end']) if billing_data.get('billing_period_end') else datetime.utcnow(),
                due_date=datetime.fromisoformat(billing_data['due_date']) if billing_data.get('due_date') else datetime.utcnow() + timedelta(days=30),
                line_items=billing_data.get('line_items', []),
                notes=billing_data.get('notes', ''),
                tax_amount=billing_data.get('tax_amount', 0.0),
                discount_amount=billing_data.get('discount_amount', 0.0)
            )
            
            db.session.add(invoice)
            db.session.commit()
            
            current_app.logger.info(f"Generated invoice {invoice_number} for organization {organization_id}")
            return invoice
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating invoice: {str(e)}")
            raise
    
    def get_organization_billing_summary(self, organization_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Get billing summary for organization"""
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Total billed amount
            total_billed = db.session.query(func.sum(BillingInvoice.amount))\
                .filter(
                    BillingInvoice.organization_id == organization_id,
                    BillingInvoice.issue_date >= start_date,
                    BillingInvoice.issue_date <= end_date
                ).scalar() or 0
            
            # Total paid amount
            total_paid = db.session.query(func.sum(BillingInvoice.amount))\
                .filter(
                    BillingInvoice.organization_id == organization_id,
                    BillingInvoice.status == 'paid',
                    BillingInvoice.payment_date >= start_date,
                    BillingInvoice.payment_date <= end_date
                ).scalar() or 0
            
            # Outstanding amount
            outstanding = db.session.query(func.sum(BillingInvoice.amount))\
                .filter(
                    BillingInvoice.organization_id == organization_id,
                    BillingInvoice.status.in_(['issued', 'overdue']),
                    BillingInvoice.due_date <= datetime.utcnow()
                ).scalar() or 0
            
            # Invoice count
            invoice_count = db.session.query(func.count(BillingInvoice.id))\
                .filter(
                    BillingInvoice.organization_id == organization_id,
                    BillingInvoice.issue_date >= start_date,
                    BillingInvoice.issue_date <= end_date
                ).scalar()
            
            return {
                'organization_id': organization_id,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'billing_summary': {
                    'total_billed': float(total_billed),
                    'total_paid': float(total_paid),
                    'outstanding_amount': float(outstanding),
                    'invoice_count': invoice_count,
                    'payment_rate': (total_paid / total_billed * 100) if total_billed > 0 else 0
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting billing summary: {str(e)}")
            raise
    
    # Department Management Methods
    
    def create_department(self, organization_id: int, department_data: Dict) -> Department:
        """Create a new department"""
        try:
            department = Department(
                organization_id=organization_id,
                name=department_data['name'],
                description=department_data.get('description', ''),
                head_of_department_id=department_data.get('head_of_department_id'),
                budget_allocated=department_data.get('budget_allocated', 0.0)
            )
            
            db.session.add(department)
            db.session.commit()
            
            current_app.logger.info(f"Created department: {department.name} for organization {organization_id}")
            return department
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating department: {str(e)}")
            raise
    
    def get_department_analytics(self, department_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Get analytics for a specific department"""
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            department = Department.query.get(department_id)
            if not department:
                return {}
            
            # User count
            user_count = db.session.query(func.count(OrganizationUser.id))\
                .filter(OrganizationUser.department_id == department_id).scalar()
            
            # Training completion
            completed_trainings = db.session.query(func.count(TrainingEnrollment.id))\
                .join(OrganizationUser, TrainingEnrollment.user_id == OrganizationUser.user_id)\
                .filter(
                    OrganizationUser.department_id == department_id,
                    TrainingEnrollment.status == 'completed',
                    TrainingEnrollment.completion_date >= start_date,
                    TrainingEnrollment.completion_date <= end_date
                ).scalar()
            
            # Learning hours
            total_hours = db.session.query(func.sum(Booking.duration_hours))\
                .join(OrganizationUser, Booking.student_id == OrganizationUser.user_id)\
                .filter(
                    OrganizationUser.department_id == department_id,
                    Booking.status == 'completed',
                    Booking.created_at >= start_date,
                    Booking.created_at <= end_date
                ).scalar() or 0
            
            return {
                'department_id': department_id,
                'department_name': department.name,
                'organization_id': department.organization_id,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'analytics': {
                    'user_count': user_count,
                    'completed_trainings': completed_trainings,
                    'total_learning_hours': float(total_hours),
                    'average_hours_per_user': float(total_hours / user_count) if user_count > 0 else 0
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting department analytics: {str(e)}")
            raise