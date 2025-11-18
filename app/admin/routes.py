from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.admin import bp
from app.utils.decorators import admin_required
from app.models.user import User, UserProfile
from app.models.tutor import TutorProfile
from app.models.course import Course, Subject
from app.models.booking import Booking
from app.models.payment import Payment, Payout
from app import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with key metrics and statistics"""
    # Get user statistics
    total_users = User.query.count()
    total_tutors = User.query.filter_by(role='Tutor').count()
    total_learners = User.query.filter_by(role='Learner').count()
    
    # Get booking statistics
    total_bookings = Booking.query.count()
    completed_bookings = Booking.query.filter_by(status='Completed').count()
    pending_bookings = Booking.query.filter_by(status='Pending').count()
    
    # Get payment statistics
    total_revenue = db.session.query(func.sum(Payment.amount)).filter_by(status='Completed').scalar() or 0
    total_payouts = db.session.query(func.sum(Payout.amount)).filter_by(status='Completed').scalar() or 0
    
    # Get recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    recent_payments = Payment.query.filter_by(status='Completed').order_by(Payment.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                           total_users=total_users,
                           total_tutors=total_tutors,
                           total_learners=total_learners,
                           total_bookings=total_bookings,
                           completed_bookings=completed_bookings,
                           pending_bookings=pending_bookings,
                           total_revenue=total_revenue,
                           total_payouts=total_payouts,
                           recent_users=recent_users,
                           recent_bookings=recent_bookings,
                           recent_payments=recent_payments)


@bp.route('/users')
@login_required
@admin_required
def users():
    """View all users with filtering and search capabilities"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    
    query = User.query
    
    if search:
        query = query.filter(User.email.contains(search))
    
    if role:
        query = query.filter_by(role=role)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search, role=role)


@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user details"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Update user details
        user.email = request.form.get('email', user.email)
        user.is_active = 'is_active' in request.form
        
        # Update user profile if exists
        if user.user_profile:
            user.user_profile.first_name = request.form.get('first_name', user.user_profile.first_name)
            user.user_profile.last_name = request.form.get('last_name', user.user_profile.last_name)
            user.user_profile.phone = request.form.get('phone', user.user_profile.phone)
        
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', user=user)


@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    
    # Don't allow deletion of the current admin user
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/courses')
@login_required
@admin_required
def courses():
    """View all courses"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    
    query = Course.query
    
    if search:
        query = query.filter(Course.title.contains(search))
    
    courses = query.order_by(Course.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/courses.html', courses=courses, search=search)


@bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    """Edit course details"""
    course = Course.query.get_or_404(course_id)
    subjects = Subject.query.all()
    
    if request.method == 'POST':
        # Update course details
        course.title = request.form.get('title', course.title)
        course.description = request.form.get('description', course.description)
        course.level = request.form.get('level', course.level)
        course.price = float(request.form.get('price', course.price))
        course.duration_hours = int(request.form.get('duration_hours', course.duration_hours))
        
        # Update subject if changed
        subject_id = int(request.form.get('subject_id', course.subject_id))
        if subject_id != course.subject_id:
            course.subject_id = subject_id
        
        db.session.commit()
        flash('Course updated successfully', 'success')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/edit_course.html', course=course, subjects=subjects)


@bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    """Delete a course"""
    course = Course.query.get_or_404(course_id)
    
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully', 'success')
    return redirect(url_for('admin.courses'))


@bp.route('/subjects')
@login_required
@admin_required
def subjects():
    """View all subjects"""
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)


@bp.route('/subjects/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_subject():
    """Create a new subject"""
    if request.method == 'POST':
        subject = Subject(
            name=request.form.get('name'),
            description=request.form.get('description'),
            category=request.form.get('category')
        )
        db.session.add(subject)
        db.session.commit()
        flash('Subject created successfully', 'success')
        return redirect(url_for('admin.subjects'))
    
    return render_template('admin/new_subject.html')


@bp.route('/subjects/<int:subject_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_subject(subject_id):
    """Delete a subject"""
    subject = Subject.query.get_or_404(subject_id)
    
    # Check if any courses are using this subject
    if Course.query.filter_by(subject_id=subject_id).count() > 0:
        flash('Cannot delete subject as it is being used by courses', 'danger')
        return redirect(url_for('admin.subjects'))
    
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully', 'success')
    return redirect(url_for('admin.subjects'))


@bp.route('/payments')
@login_required
@admin_required
def payments():
    """View all payments"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
    query = Payment.query
    
    if status:
        query = query.filter_by(status=status)
    
    payments = query.order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/payments.html', payments=payments, status=status)


@bp.route('/payouts')
@login_required
@admin_required
def payouts():
    """View all payouts"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
    query = Payout.query
    
    if status:
        query = query.filter_by(status=status)
    
    payouts = query.order_by(Payout.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/payouts.html', payouts=payouts, status=status)


@bp.route('/reports')
@login_required
@admin_required
def reports():
    """Generate system reports"""
    # Get date range from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Parse dates
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date = datetime.utcnow() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date = datetime.utcnow()
    
    # Generate report data
    # Revenue by date
    revenue_by_date = db.session.query(
        func.date(Payment.created_at).label('date'),
        func.sum(Payment.amount).label('total')
    ).filter(
        Payment.status == 'Completed',
        Payment.created_at >= start_date,
        Payment.created_at <= end_date
    ).group_by(
        func.date(Payment.created_at)
    ).order_by(
        func.date(Payment.created_at)
    ).all()
    
    # Top tutors by earnings
    top_tutors = db.session.query(
        TutorProfile.user_id,
        func.sum(Payment.amount).label('earnings'),
        User.email.label('email')
    ).join(
        Booking, Booking.tutor_id == TutorProfile.id
    ).join(
        Payment, Payment.booking_id == Booking.id
    ).filter(
        Payment.status == 'Completed',
        Booking.created_at >= start_date,
        Booking.created_at <= end_date
    ).group_by(
        TutorProfile.user_id, User.email
    ).order_by(
        desc('earnings')
    ).limit(10).all()
    
    return render_template('admin/reports.html', 
                           revenue_by_date=revenue_by_date,
                           top_tutors=top_tutors,
                           start_date=start_date.strftime('%Y-%m-%d'),
                           end_date=end_date.strftime('%Y-%m-%d'))


@bp.route('/api/users/stats')
@login_required
@admin_required
def user_stats():
    """API endpoint for user statistics"""
    stats = {
        'total': User.query.count(),
        'tutors': User.query.filter_by(role='Tutor').count(),
        'learners': User.query.filter_by(role='Learner').count(),
        'active_this_month': User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
    }
    
    return jsonify(stats)


@bp.route('/api/bookings/stats')
@login_required
@admin_required
def booking_stats():
    """API endpoint for booking statistics"""
    stats = {
        'total': Booking.query.count(),
        'completed': Booking.query.filter_by(status='Completed').count(),
        'pending': Booking.query.filter_by(status='Pending').count(),
        'this_month': Booking.query.filter(
            Booking.created_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
    }
    
    return jsonify(stats)