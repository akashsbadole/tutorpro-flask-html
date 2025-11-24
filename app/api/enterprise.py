"""
Enterprise API Endpoints for TutorPro
Provides RESTful API for organization management, corporate training, and B2B features
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from app import db
from app.models.enterprise import (
    Organization, Department, OrganizationUser, TrainingProgram, 
    TrainingEnrollment, BillingInvoice, BulkOperation
)
from app.models.user import User
from app.services.enterprise_service import EnterpriseService
from app.utils.decorators import require_role, admin_required

# Create blueprint
enterprise_bp = Blueprint('enterprise', __name__, url_prefix='/api/enterprise')

# Initialize service
enterprise_service = EnterpriseService()


# Organization Management Endpoints

@enterprise_bp.route('/organizations', methods=['GET'])
@login_required
@require_role(['admin'])
def get_organizations():
    """Get all organizations"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = Organization.query
        
        if search:
            query = query.filter(
                Organization.name.contains(search) |
                Organization.contact_email.contains(search) |
                Organization.industry.contains(search)
            )
        
        organizations = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'organizations': [org.to_dict() for org in organizations.items],
            'pagination': {
                'page': organizations.page,
                'pages': organizations.pages,
                'per_page': organizations.per_page,
                'total': organizations.total,
                'has_next': organizations.has_next,
                'has_prev': organizations.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting organizations: {str(e)}")
        return jsonify({'error': 'Failed to retrieve organizations'}), 500


@enterprise_bp.route('/organizations', methods=['POST'])
@login_required
@require_role(['admin'])
def create_organization():
    """Create a new organization"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'contact_email']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create organization
        organization = enterprise_service.create_organization(data, current_user.id)
        
        return jsonify({
            'message': 'Organization created successfully',
            'organization': organization.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating organization: {str(e)}")
        return jsonify({'error': 'Failed to create organization'}), 500


@enterprise_bp.route('/organizations/<int:organization_id>', methods=['GET'])
@login_required
def get_organization(organization_id):
    """Get organization details"""
    try:
        # Check if user has access to this organization
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or org_user.access_level == 'read_only':
                return jsonify({'error': 'Access denied'}), 403
        
        organization = Organization.query.get_or_404(organization_id)
        return jsonify(organization.to_dict())
        
    except Exception as e:
        current_app.logger.error(f"Error getting organization: {str(e)}")
        return jsonify({'error': 'Failed to retrieve organization'}), 500


@enterprise_bp.route('/organizations/<int:organization_id>', methods=['PUT'])
@login_required
def update_organization(organization_id):
    """Update organization details"""
    try:
        # Check if user has permission to update organization
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or not org_user.can_manage_users:
                return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        organization = enterprise_service.update_organization(organization_id, data)
        
        if not organization:
            return jsonify({'error': 'Organization not found'}), 404
        
        return jsonify({
            'message': 'Organization updated successfully',
            'organization': organization.to_dict()
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating organization: {str(e)}")
        return jsonify({'error': 'Failed to update organization'}), 500


@enterprise_bp.route('/organizations/<int:organization_id>/analytics', methods=['GET'])
@login_required
def get_organization_analytics(organization_id):
    """Get organization analytics"""
    try:
        # Check if user has access to analytics
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or not org_user.can_view_analytics:
                return jsonify({'error': 'Access denied'}), 403
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        analytics = enterprise_service.get_organization_analytics(
            organization_id, start_date, end_date
        )
        
        return jsonify(analytics)
        
    except Exception as e:
        current_app.logger.error(f"Error getting organization analytics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve analytics'}), 500


# User Management Endpoints

@enterprise_bp.route('/organizations/<int:organization_id>/users', methods=['GET'])
@login_required
def get_organization_users(organization_id):
    """Get users in an organization"""
    try:
        # Check if user has access to organization
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user:
                return jsonify({'error': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = db.session.query(OrganizationUser, User).join(
            User, OrganizationUser.user_id == User.id
        ).filter(OrganizationUser.organization_id == organization_id)
        
        if search:
            query = query.filter(
                User.first_name.contains(search) |
                User.last_name.contains(search) |
                User.email.contains(search)
            )
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        users_data = []
        for org_user, user in pagination.items:
            user_data = user.to_dict()
            user_data.update(org_user.to_dict())
            users_data.append(user_data)
        
        return jsonify({
            'users': users_data,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting organization users: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users'}), 500


@enterprise_bp.route('/organizations/<int:organization_id>/users', methods=['POST'])
@login_required
def add_user_to_organization(organization_id):
    """Add a user to an organization"""
    try:
        # Check if user has permission to add users
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or not org_user.can_manage_users:
                return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if 'email' not in data:
            return jsonify({'error': 'Missing required field: email'}), 400
        
        org_user = enterprise_service.add_user_to_organization(organization_id, data)
        
        return jsonify({
            'message': 'User added successfully',
            'organization_user': org_user.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error adding user to organization: {str(e)}")
        return jsonify({'error': 'Failed to add user'}), 500


@enterprise_bp.route('/organizations/<int:organization_id>/users/bulk-import', methods=['POST'])
@login_required
def bulk_import_users(organization_id):
    """Bulk import users to an organization"""
    try:
        # Check if user has permission to import users
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or not org_user.can_manage_users:
                return jsonify({'error': 'Access denied'}), 403
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file content
        file_content = file.read().decode('utf-8')
        file_format = 'csv' if file.filename.endswith('.csv') else 'xlsx'
        
        bulk_operation = enterprise_service.bulk_import_users(
            organization_id, file_content, file_format
        )
        
        return jsonify({
            'message': 'Bulk import started',
            'bulk_operation': bulk_operation.to_dict()
        }), 202
        
    except Exception as e:
        current_app.logger.error(f"Error in bulk import: {str(e)}")
        return jsonify({'error': 'Failed to process bulk import'}), 500


@enterprise_bp.route('/bulk-operations/<int:operation_id>', methods=['GET'])
@login_required
def get_bulk_operation_status(operation_id):
    """Get bulk operation status"""
    try:
        operation = BulkOperation.query.get_or_404(operation_id)
        
        # Check if user has access to this operation
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=operation.organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user:
                return jsonify({'error': 'Access denied'}), 403
        
        return jsonify(operation.to_dict())
        
    except Exception as e:
        current_app.logger.error(f"Error getting bulk operation: {str(e)}")
        return jsonify({'error': 'Failed to retrieve operation status'}), 500


# Department Management Endpoints

@enterprise_bp.route('/organizations/<int:organization_id>/departments', methods=['GET'])
@login_required
def get_departments(organization_id):
    """Get departments in an organization"""
    try:
        # Check if user has access to organization
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user:
                return jsonify({'error': 'Access denied'}), 403
        
        departments = Department.query.filter_by(organization_id=organization_id).all()
        
        return jsonify({
            'departments': [dept.to_dict() for dept in departments]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting departments: {str(e)}")
        return jsonify({'error': 'Failed to retrieve departments'}), 500


@enterprise_bp.route('/organizations/<int:organization_id>/departments', methods=['POST'])
@login_required
def create_department(organization_id):
    """Create a new department"""
    try:
        # Check if user has permission to create departments
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or not org_user.can_manage_users:
                return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if 'name' not in data:
            return jsonify({'error': 'Missing required field: name'}), 400
        
        department = enterprise_service.create_department(organization_id, data)
        
        return jsonify({
            'message': 'Department created successfully',
            'department': department.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating department: {str(e)}")
        return jsonify({'error': 'Failed to create department'}), 500


@enterprise_bp.route('/departments/<int:department_id>/analytics', methods=['GET'])
@login_required
def get_department_analytics(department_id):
    """Get department analytics"""
    try:
        department = Department.query.get_or_404(department_id)
        
        # Check if user has access to department analytics
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=department.organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or not org_user.can_view_analytics:
                return jsonify({'error': 'Access denied'}), 403
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        analytics = enterprise_service.get_department_analytics(
            department_id, start_date, end_date
        )
        
        return jsonify(analytics)
        
    except Exception as e:
        current_app.logger.error(f"Error getting department analytics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve analytics'}), 500


# Training Program Endpoints

@enterprise_bp.route('/organizations/<int:organization_id>/training-programs', methods=['GET'])
@login_required
def get_training_programs(organization_id):
    """Get training programs for an organization"""
    try:
        # Check if user has access to organization
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user:
                return jsonify({'error': 'Access denied'}), 403
        
        programs = TrainingProgram.query.filter_by(organization_id=organization_id).all()
        
        return jsonify({
            'training_programs': [program.to_dict() for program in programs]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting training programs: {str(e)}")
        return jsonify({'error': 'Failed to retrieve training programs'}), 500


@enterprise_bp.route('/organizations/<int:organization_id>/training-programs', methods=['POST'])
@login_required
def create_training_program(organization_id):
    """Create a new training program"""
    try:
        # Check if user has permission to create training programs
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or not org_user.can_manage_users:
                return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if 'name' not in data:
            return jsonify({'error': 'Missing required field: name'}), 400
        
        program = enterprise_service.create_training_program(organization_id, data)
        
        return jsonify({
            'message': 'Training program created successfully',
            'training_program': program.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating training program: {str(e)}")
        return jsonify({'error': 'Failed to create training program'}), 500


@enterprise_bp.route('/training-programs/<int:program_id>/enroll', methods=['POST'])
@login_required
def enroll_users_in_training(program_id):
    """Enroll users in a training program"""
    try:
        data = request.get_json()
        
        if 'user_ids' not in data:
            return jsonify({'error': 'Missing required field: user_ids'}), 400
        
        user_ids = data['user_ids']
        if not isinstance(user_ids, list):
            return jsonify({'error': 'user_ids must be an array'}), 400
        
        # Check if user has permission to enroll users
        program = TrainingProgram.query.get_or_404(program_id)
        
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=program.organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or not org_user.can_manage_users:
                return jsonify({'error': 'Access denied'}), 403
        
        enrollments = enterprise_service.enroll_users_in_training(program_id, user_ids)
        
        return jsonify({
            'message': f'Enrolled {len(enrollments)} users in training program',
            'enrollments': [enrollment.to_dict() for enrollment in enrollments]
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error enrolling users in training: {str(e)}")
        return jsonify({'error': 'Failed to enroll users'}), 500


@enterprise_bp.route('/training-enrollments/<int:enrollment_id>/progress', methods=['PUT'])
@login_required
def update_training_progress(enrollment_id):
    """Update training enrollment progress"""
    try:
        data = request.get_json()
        
        # Check if user has permission to update progress
        enrollment = TrainingEnrollment.query.get_or_404(enrollment_id)
        
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=enrollment.training_program.organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or (org_user.user_id != enrollment.user_id and not org_user.can_manage_users):
                return jsonify({'error': 'Access denied'}), 403
        
        updated_enrollment = enterprise_service.update_training_progress(enrollment_id, data)
        
        if not updated_enrollment:
            return jsonify({'error': 'Enrollment not found'}), 404
        
        return jsonify({
            'message': 'Training progress updated successfully',
            'enrollment': updated_enrollment.to_dict()
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating training progress: {str(e)}")
        return jsonify({'error': 'Failed to update progress'}), 500


# Billing Endpoints

@enterprise_bp.route('/organizations/<int:organization_id>/invoices', methods=['GET'])
@login_required
def get_organization_invoices(organization_id):
    """Get billing invoices for an organization"""
    try:
        # Check if user has access to billing
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or not org_user.can_manage_billing:
                return jsonify({'error': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        invoices = BillingInvoice.query.filter_by(organization_id=organization_id)\
            .order_by(BillingInvoice.issue_date.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'invoices': [invoice.to_dict() for invoice in invoices.items],
            'pagination': {
                'page': invoices.page,
                'pages': invoices.pages,
                'per_page': invoices.per_page,
                'total': invoices.total,
                'has_next': invoices.has_next,
                'has_prev': invoices.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting invoices: {str(e)}")
        return jsonify({'error': 'Failed to retrieve invoices'}), 500


@enterprise_bp.route('/organizations/<int:organization_id>/invoices', methods=['POST'])
@login_required
def generate_invoice(organization_id):
    """Generate a billing invoice for an organization"""
    try:
        # Check if user has permission to generate invoices
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or not org_user.can_manage_billing:
                return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if 'amount' not in data:
            return jsonify({'error': 'Missing required field: amount'}), 400
        
        invoice = enterprise_service.generate_invoice(organization_id, data)
        
        return jsonify({
            'message': 'Invoice generated successfully',
            'invoice': invoice.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating invoice: {str(e)}")
        return jsonify({'error': 'Failed to generate invoice'}), 500


@enterprise_bp.route('/organizations/<int:organization_id>/billing-summary', methods=['GET'])
@login_required
def get_billing_summary(organization_id):
    """Get billing summary for an organization"""
    try:
        # Check if user has access to billing
        if not current_user.is_admin:
            org_user = OrganizationUser.query.filter_by(
                organization_id=organization_id,
                user_id=current_user.id
            ).first()
            
            if not org_user or not org_user.can_manage_billing:
                return jsonify({'error': 'Access denied'}), 403
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        summary = enterprise_service.get_organization_billing_summary(
            organization_id, start_date, end_date
        )
        
        return jsonify(summary)
        
    except Exception as e:
        current_app.logger.error(f"Error getting billing summary: {str(e)}")
        return jsonify({'error': 'Failed to retrieve billing summary'}), 500