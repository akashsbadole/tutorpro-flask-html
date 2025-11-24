"""
Enterprise Admin Routes for TutorPro
Provides admin interface for organization management and corporate training
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models.enterprise import (
    Organization, Department, OrganizationUser, TrainingProgram, 
    TrainingEnrollment, BillingInvoice, BulkOperation
)
from app.models.user import User
from app.services.enterprise_service import EnterpriseService
from app.utils.decorators import admin_required

# Create blueprint
enterprise_bp = Blueprint('enterprise', __name__, url_prefix='/admin/enterprise')

# Initialize service
enterprise_service = EnterpriseService()


# Organization Management Routes

@enterprise_bp.route('/organizations')
@login_required
@admin_required
def organizations():
    """Organizations management page"""
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
    
    organizations = query.order_by(Organization.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/enterprise/organizations.html', 
                         organizations=organizations, 
                         search=search)


@enterprise_bp.route('/organizations/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_organization():
    """Create new organization"""
    if request.method == 'POST':
        try:
            data = {
                'name': request.form.get('name'),
                'type': request.form.get('type', 'enterprise'),
                'description': request.form.get('description', ''),
                'industry': request.form.get('industry', ''),
                'size': request.form.get('size', 'small'),
                'website': request.form.get('website', ''),
                'contact_email': request.form.get('contact_email'),
                'contact_phone': request.form.get('contact_phone', ''),
                'address': request.form.get('address', ''),
                'city': request.form.get('city', ''),
                'state': request.form.get('state', ''),
                'country': request.form.get('country', ''),
                'postal_code': request.form.get('postal_code', ''),
                'subscription_plan': request.form.get('subscription_plan', 'basic'),
                'billing_cycle': request.form.get('billing_cycle', 'monthly'),
                'max_users': int(request.form.get('max_users', 100)),
                'primary_color': request.form.get('primary_color', '#007bff'),
                'secondary_color': request.form.get('secondary_color', '#6c757d')
            }
            
            organization = enterprise_service.create_organization(data, current_user.id)
            flash(f'Organization "{organization.name}" created successfully!', 'success')
            return redirect(url_for('enterprise.organization_detail', id=organization.id))
            
        except Exception as e:
            current_app.logger.error(f"Error creating organization: {str(e)}")
            flash(f'Error creating organization: {str(e)}', 'error')
    
    return render_template('admin/enterprise/new_organization.html')


@enterprise_bp.route('/organizations/<int:id>')
@login_required
@admin_required
def organization_detail(id):
    """Organization detail page"""
    organization = Organization.query.get_or_404(id)
    
    # Get organization analytics
    analytics = enterprise_service.get_organization_analytics(id)
    
    # Get recent users
    recent_users = db.session.query(OrganizationUser, User)\
        .join(User, OrganizationUser.user_id == User.id)\
        .filter(OrganizationUser.organization_id == id)\
        .order_by(OrganizationUser.created_at.desc())\
        .limit(10).all()
    
    # Get recent invoices
    recent_invoices = BillingInvoice.query\
        .filter_by(organization_id=id)\
        .order_by(BillingInvoice.issue_date.desc())\
        .limit(10).all()
    
    return render_template('admin/enterprise/organization_detail.html',
                         organization=organization,
                         analytics=analytics,
                         recent_users=recent_users,
                         recent_invoices=recent_invoices)


@enterprise_bp.route('/organizations/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_organization(id):
    """Edit organization"""
    organization = Organization.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            data = {
                'name': request.form.get('name'),
                'description': request.form.get('description', ''),
                'industry': request.form.get('industry', ''),
                'size': request.form.get('size', 'small'),
                'website': request.form.get('website', ''),
                'contact_email': request.form.get('contact_email'),
                'contact_phone': request.form.get('contact_phone', ''),
                'address': request.form.get('address', ''),
                'city': request.form.get('city', ''),
                'state': request.form.get('state', ''),
                'country': request.form.get('country', ''),
                'postal_code': request.form.get('postal_code', ''),
                'subscription_plan': request.form.get('subscription_plan', 'basic'),
                'billing_cycle': request.form.get('billing_cycle', 'monthly'),
                'max_users': int(request.form.get('max_users', 100)),
                'primary_color': request.form.get('primary_color', '#007bff'),
                'secondary_color': request.form.get('secondary_color', '#6c757d')
            }
            
            updated_org = enterprise_service.update_organization(id, data)
            flash(f'Organization "{updated_org.name}" updated successfully!', 'success')
            return redirect(url_for('enterprise.organization_detail', id=id))
            
        except Exception as e:
            current_app.logger.error(f"Error updating organization: {str(e)}")
            flash(f'Error updating organization: {str(e)}', 'error')
    
    return render_template('admin/enterprise/edit_organization.html', organization=organization)


@enterprise_bp.route('/organizations/<int:id>/users')
@login_required
@admin_required
def organization_users(id):
    """Organization users management page"""
    organization = Organization.query.get_or_404(id)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    query = db.session.query(OrganizationUser, User).join(
        User, OrganizationUser.user_id == User.id
    ).filter(OrganizationUser.organization_id == id)
    
    if search:
        query = query.filter(
            User.first_name.contains(search) |
            User.last_name.contains(search) |
            User.email.contains(search)
        )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/enterprise/organization_users.html',
                         organization=organization,
                         users=pagination)


@enterprise_bp.route('/organizations/<int:id>/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_organization_user(id):
    """Add new user to organization"""
    organization = Organization.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            data = {
                'email': request.form.get('email'),
                'first_name': request.form.get('first_name', ''),
                'last_name': request.form.get('last_name', ''),
                'phone': request.form.get('phone', ''),
                'role': request.form.get('role', 'employee'),
                'job_title': request.form.get('job_title', ''),
                'department_id': request.form.get('department_id') or None,
                'access_level': request.form.get('access_level', 'limited'),
                'can_manage_users': request.form.get('can_manage_users') == 'on',
                'can_view_analytics': request.form.get('can_view_analytics') == 'on',
                'can_manage_billing': request.form.get('can_manage_billing') == 'on'
            }
            
            org_user = enterprise_service.add_user_to_organization(id, data)
            flash(f'User "{data["email"]}" added successfully!', 'success')
            return redirect(url_for('enterprise.organization_users', id=id))
            
        except Exception as e:
            current_app.logger.error(f"Error adding user to organization: {str(e)}")
            flash(f'Error adding user: {str(e)}', 'error')
    
    # Get departments for dropdown
    departments = Department.query.filter_by(organization_id=id).all()
    
    return render_template('admin/enterprise/new_organization_user.html',
                         organization=organization,
                         departments=departments)


@enterprise_bp.route('/organizations/<int:id>/users/bulk-import', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_import_users(id):
    """Bulk import users to organization"""
    organization = Organization.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file provided', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            # Read file content
            file_content = file.read().decode('utf-8')
            file_format = 'csv' if file.filename.endswith('.csv') else 'xlsx'
            
            bulk_operation = enterprise_service.bulk_import_users(
                id, file_content, file_format
            )
            
            flash(f'Bulk import started! Operation ID: {bulk_operation.id}', 'success')
            return redirect(url_for('enterprise.bulk_operations', id=id))
            
        except Exception as e:
            current_app.logger.error(f"Error in bulk import: {str(e)}")
            flash(f'Error processing bulk import: {str(e)}', 'error')
    
    return render_template('admin/enterprise/bulk_import_users.html',
                         organization=organization)


@enterprise_bp.route('/organizations/<int:id>/departments')
@login_required
@admin_required
def organization_departments(id):
    """Organization departments management page"""
    organization = Organization.query.get_or_404(id)
    departments = Department.query.filter_by(organization_id=id).all()
    
    return render_template('admin/enterprise/organization_departments.html',
                         organization=organization,
                         departments=departments)


@enterprise_bp.route('/organizations/<int:id>/departments/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_department(id):
    """Create new department"""
    organization = Organization.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            data = {
                'name': request.form.get('name'),
                'description': request.form.get('description', ''),
                'head_of_department_id': request.form.get('head_of_department_id') or None,
                'budget_allocated': float(request.form.get('budget_allocated', 0.0))
            }
            
            department = enterprise_service.create_department(id, data)
            flash(f'Department "{department.name}" created successfully!', 'success')
            return redirect(url_for('enterprise.organization_departments', id=id))
            
        except Exception as e:
            current_app.logger.error(f"Error creating department: {str(e)}")
            flash(f'Error creating department: {str(e)}', 'error')
    
    # Get organization users for department head selection
    users = db.session.query(OrganizationUser, User)\
        .join(User, OrganizationUser.user_id == User.id)\
        .filter(OrganizationUser.organization_id == id)\
        .all()
    
    return render_template('admin/enterprise/new_department.html',
                         organization=organization,
                         users=users)


# Training Program Routes

@enterprise_bp.route('/organizations/<int:id>/training-programs')
@login_required
@admin_required
def training_programs(id):
    """Training programs management page"""
    organization = Organization.query.get_or_404(id)
    programs = TrainingProgram.query.filter_by(organization_id=id).all()
    
    return render_template('admin/enterprise/training_programs.html',
                         organization=organization,
                         programs=programs)


@enterprise_bp.route('/organizations/<int:id>/training-programs/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_training_program(id):
    """Create new training program"""
    organization = Organization.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            data = {
                'name': request.form.get('name'),
                'description': request.form.get('description', ''),
                'category': request.form.get('category', 'skills'),
                'duration_hours': float(request.form.get('duration_hours', 0.0)),
                'required_completion_days': int(request.form.get('required_completion_days', 30)),
                'max_participants': int(request.form.get('max_participants', 0)),
                'is_mandatory': request.form.get('is_mandatory') == 'on',
                'content': request.form.get('content', ''),
                'materials_url': request.form.get('materials_url', ''),
                'assessment_required': request.form.get('assessment_required') == 'on',
                'passing_score': float(request.form.get('passing_score', 70.0)),
                'start_date': request.form.get('start_date'),
                'end_date': request.form.get('end_date')
            }
            
            program = enterprise_service.create_training_program(id, data)
            flash(f'Training program "{program.name}" created successfully!', 'success')
            return redirect(url_for('enterprise.training_programs', id=id))
            
        except Exception as e:
            current_app.logger.error(f"Error creating training program: {str(e)}")
            flash(f'Error creating training program: {str(e)}', 'error')
    
    return render_template('admin/enterprise/new_training_program.html',
                         organization=organization)


@enterprise_bp.route('/training-programs/<int:program_id>/enrollments')
@login_required
@admin_required
def training_enrollments(program_id):
    """Training program enrollments page"""
    program = TrainingProgram.query.get_or_404(program_id)
    
    enrollments = db.session.query(TrainingEnrollment, User)\
        .join(User, TrainingEnrollment.user_id == User.id)\
        .filter(TrainingEnrollment.training_program_id == program_id)\
        .all()
    
    return render_template('admin/enterprise/training_enrollments.html',
                         program=program,
                         enrollments=enrollments)


# Billing Routes

@enterprise_bp.route('/organizations/<int:id>/billing')
@login_required
@admin_required
def organization_billing(id):
    """Organization billing page"""
    organization = Organization.query.get_or_404(id)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    invoices = BillingInvoice.query.filter_by(organization_id=id)\
        .order_by(BillingInvoice.issue_date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Get billing summary
    billing_summary = enterprise_service.get_organization_billing_summary(id)
    
    return render_template('admin/enterprise/organization_billing.html',
                         organization=organization,
                         invoices=invoices,
                         billing_summary=billing_summary)


@enterprise_bp.route('/organizations/<int:id>/invoices/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_invoice(id):
    """Create new invoice"""
    organization = Organization.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Parse line items from form
            line_items = []
            item_count = int(request.form.get('item_count', 1))
            
            for i in range(item_count):
                description = request.form.get(f'item_{i}_description', '')
                quantity = float(request.form.get(f'item_{i}_quantity', 0))
                unit_price = float(request.form.get(f'item_{i}_unit_price', 0))
                
                if description and quantity > 0 and unit_price > 0:
                    line_items.append({
                        'description': description,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total': quantity * unit_price
                    })
            
            data = {
                'amount': float(request.form.get('amount', 0)),
                'currency': request.form.get('currency', 'USD'),
                'billing_period_start': request.form.get('billing_period_start'),
                'billing_period_end': request.form.get('billing_period_end'),
                'due_date': request.form.get('due_date'),
                'line_items': line_items,
                'notes': request.form.get('notes', ''),
                'tax_amount': float(request.form.get('tax_amount', 0.0)),
                'discount_amount': float(request.form.get('discount_amount', 0.0))
            }
            
            invoice = enterprise_service.generate_invoice(id, data)
            flash(f'Invoice "{invoice.invoice_number}" created successfully!', 'success')
            return redirect(url_for('enterprise.organization_billing', id=id))
            
        except Exception as e:
            current_app.logger.error(f"Error creating invoice: {str(e)}")
            flash(f'Error creating invoice: {str(e)}', 'error')
    
    return render_template('admin/enterprise/new_invoice.html',
                         organization=organization)


# Bulk Operations Routes

@enterprise_bp.route('/organizations/<int:id>/bulk-operations')
@login_required
@admin_required
def bulk_operations(id):
    """Bulk operations tracking page"""
    organization = Organization.query.get_or_404(id)
    
    operations = BulkOperation.query.filter_by(organization_id=id)\
        .order_by(BulkOperation.started_at.desc())\
        .all()
    
    return render_template('admin/enterprise/bulk_operations.html',
                         organization=organization,
                         operations=operations)


@enterprise_bp.route('/bulk-operations/<int:operation_id>')
@login_required
@admin_required
def bulk_operation_detail(operation_id):
    """Bulk operation detail page"""
    operation = BulkOperation.query.get_or_404(operation_id)
    
    return render_template('admin/enterprise/bulk_operation_detail.html',
                         operation=operation)


# Analytics Routes

@enterprise_bp.route('/organizations/<int:id>/analytics')
@login_required
@admin_required
def organization_analytics(id):
    """Organization analytics page"""
    organization = Organization.query.get_or_404(id)
    
    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.fromisoformat(start_date)
    if end_date:
        end_date = datetime.fromisoformat(end_date)
    
    # Get analytics
    analytics = enterprise_service.get_organization_analytics(id, start_date, end_date)
    
    return render_template('admin/enterprise/organization_analytics.html',
                         organization=organization,
                         analytics=analytics)