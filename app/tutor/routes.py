from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.tutor import bp
from app.utils.decorators import tutor_required
from app.models.user import User, UserProfile
from app.models.tutor import TutorProfile
from app.models.course import Course, Subject, TutorSubject
from app.models.booking import Booking, TutorAvailability
from app.models.payment import Payment, Payout
from app.models.review import Review, TutorRatingSummary
from app import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json


@bp.route('/dashboard')
@login_required
@tutor_required
def dashboard():
    """Tutor dashboard with key metrics and statistics"""
    # Get tutor profile
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    # Get booking statistics
    total_bookings = Booking.query.filter_by(tutor_id=tutor_profile.id).count()
    upcoming_bookings = Booking.query.filter(
        Booking.tutor_id == tutor_profile.id,
        Booking.scheduled_time > datetime.utcnow(),
        Booking.status.in_(['Pending', 'Confirmed'])
    ).count()
    
    # Get payment statistics
    total_earnings = db.session.query(func.sum(Payment.amount)).join(
        Booking, Booking.id == Payment.booking_id
    ).filter(
        Booking.tutor_id == tutor_profile.id,
        Payment.status == 'Completed'
    ).scalar() or 0
    
    pending_payouts = db.session.query(func.sum(Payout.amount)).filter(
        Payout.tutor_id == tutor_profile.id,
        Payout.status.in_(['Pending', 'Processing'])
    ).scalar() or 0
    
    # Get review statistics
    total_reviews = Review.query.filter_by(tutor_id=tutor_profile.id).count()
    average_rating = Review.query.filter_by(tutor_id=tutor_profile.id).with_entities(
        func.avg(Review.rating)
    ).scalar() or 0
    
    # Get upcoming bookings
    upcoming_booking_list = Booking.query.filter(
        Booking.tutor_id == tutor_profile.id,
        Booking.scheduled_time > datetime.utcnow(),
        Booking.status.in_(['Pending', 'Confirmed'])
    ).order_by(Booking.scheduled_time.asc()).limit(5).all()
    
    # Get recent reviews
    recent_reviews = Review.query.filter_by(tutor_id=tutor_profile.id).order_by(
        Review.created_at.desc()
    ).limit(5).all()
    
    # Get rating summary
    rating_summary = tutor_profile.rating_summary
    if not rating_summary:
        rating_summary = TutorRatingSummary(tutor_id=tutor_profile.id)
        db.session.add(rating_summary)
        db.session.commit()
    
    return render_template('tutor/dashboard.html', 
                           tutor_profile=tutor_profile,
                           total_bookings=total_bookings,
                           upcoming_bookings=upcoming_bookings,
                           total_earnings=total_earnings,
                           pending_payouts=pending_payouts,
                           total_reviews=total_reviews,
                           average_rating=average_rating,
                           upcoming_booking_list=upcoming_booking_list,
                           recent_reviews=recent_reviews,
                           rating_summary=rating_summary)


@bp.route('/profile')
@login_required
@tutor_required
def profile():
    """View and edit tutor profile"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        # Create tutor profile if it doesn't exist
        tutor_profile = TutorProfile(user_id=current_user.id)
        db.session.add(tutor_profile)
        db.session.commit()
    
    return render_template('tutor/profile.html', tutor_profile=tutor_profile)


@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@tutor_required
def edit_profile():
    """Edit tutor profile"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        # Create tutor profile if it doesn't exist
        tutor_profile = TutorProfile(user_id=current_user.id)
        db.session.add(tutor_profile)
        db.session.commit()
    
    if request.method == 'POST':
        # Update tutor profile
        tutor_profile.title = request.form.get('title', tutor_profile.title)
        tutor_profile.description = request.form.get('description', tutor_profile.description)
        tutor_profile.hourly_rate = float(request.form.get('hourly_rate', tutor_profile.hourly_rate))
        tutor_profile.video_intro_url = request.form.get('video_intro_url', tutor_profile.video_intro_url)
        
        # Update user profile
        if current_user.user_profile:
            current_user.user_profile.first_name = request.form.get('first_name', current_user.user_profile.first_name)
            current_user.user_profile.last_name = request.form.get('last_name', current_user.user_profile.last_name)
            current_user.user_profile.phone = request.form.get('phone', current_user.user_profile.phone)
            current_user.user_profile.bio = request.form.get('bio', current_user.user_profile.bio)
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('tutor.profile'))
    
    return render_template('tutor/edit_profile.html', tutor_profile=tutor_profile)


@bp.route('/schedule')
@login_required
@tutor_required
def schedule():
    """View and manage tutor schedule"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    # Get availability
    availabilities = TutorAvailability.query.filter_by(tutor_id=tutor_profile.id).all()
    
    # Get bookings for the next 7 days
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=7)
    
    bookings = Booking.query.filter(
        Booking.tutor_id == tutor_profile.id,
        Booking.scheduled_time >= start_date,
        Booking.scheduled_time <= end_date
    ).order_by(Booking.scheduled_time.asc()).all()
    
    return render_template('tutor/schedule.html', 
                           availabilities=availabilities,
                           bookings=bookings,
                           start_date=start_date,
                           end_date=end_date)


@bp.route('/schedule/availability', methods=['GET', 'POST'])
@login_required
@tutor_required
def manage_availability():
    """Manage tutor availability"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    if request.method == 'POST':
        # Process availability update
        day_of_week = int(request.form.get('day_of_week'))
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        is_available = 'is_available' in request.form
        
        # Parse time
        start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = datetime.strptime(end_time, '%H:%M').time()
        
        # Check if availability already exists
        availability = TutorAvailability.query.filter_by(
            tutor_id=tutor_profile.id,
            day_of_week=day_of_week
        ).first()
        
        if availability:
            # Update existing availability
            availability.start_time = start_time
            availability.end_time = end_time
            availability.is_available = is_available
        else:
            # Create new availability
            availability = TutorAvailability(
                tutor_id=tutor_profile.id,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                is_available=is_available
            )
            db.session.add(availability)
        
        db.session.commit()
        flash('Availability updated successfully', 'success')
        return redirect(url_for('tutor.schedule'))
    
    # Get existing availability
    availabilities = TutorAvailability.query.filter_by(tutor_id=tutor_profile.id).all()
    
    return render_template('tutor/manage_availability.html', 
                           availabilities=availabilities)


@bp.route('/bookings')
@login_required
@tutor_required
def bookings():
    """View all bookings"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    query = Booking.query.filter_by(tutor_id=tutor_profile.id)
    
    if status:
        query = query.filter_by(status=status)
    
    bookings = query.order_by(Booking.scheduled_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('tutor/bookings.html', bookings=bookings, status=status)


@bp.route('/bookings/<int:booking_id>/confirm', methods=['POST'])
@login_required
@tutor_required
def confirm_booking(booking_id):
    """Confirm a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.tutor_id != current_user.tutor_profile.id:
        flash('You do not have permission to modify this booking', 'danger')
        return redirect(url_for('tutor.bookings'))
    
    booking.status = 'Confirmed'
    db.session.commit()
    
    flash('Booking confirmed successfully', 'success')
    return redirect(url_for('tutor.bookings'))


@bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@tutor_required
def cancel_booking(booking_id):
    """Cancel a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.tutor_id != current_user.tutor_profile.id:
        flash('You do not have permission to modify this booking', 'danger')
        return redirect(url_for('tutor.bookings'))
    
    booking.status = 'Cancelled'
    db.session.commit()
    
    flash('Booking cancelled successfully', 'success')
    return redirect(url_for('tutor.bookings'))


@bp.route('/earnings')
@login_required
@tutor_required
def earnings():
    """View earnings and payment information"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    # Get payments
    payments = Payment.query.join(
        Booking, Booking.id == Payment.booking_id
    ).filter(
        Booking.tutor_id == tutor_profile.id,
        Payment.status == 'Completed'
    ).order_by(Payment.created_at.desc()).all()
    
    # Get payouts
    payouts = Payout.query.filter_by(tutor_id=tutor_profile.id).order_by(
        Payout.created_at.desc()
    ).all()
    
    # Calculate totals
    total_earnings = sum(p.amount for p in payments)
    total_payouts = sum(p.amount for p in payouts if p.status == 'Completed')
    pending_payouts = sum(p.amount for p in payouts if p.status in ['Pending', 'Processing'])
    
    return render_template('tutor/earnings.html',
                           payments=payments,
                           payouts=payouts,
                           total_earnings=total_earnings,
                           total_payouts=total_payouts,
                           pending_payouts=pending_payouts)


@bp.route('/reviews')
@login_required
@tutor_required
def reviews():
    """View and manage reviews"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    # Get reviews
    reviews = Review.query.filter_by(tutor_id=tutor_profile.id).order_by(
        Review.created_at.desc()
    ).all()
    
    # Get rating summary
    rating_summary = tutor_profile.rating_summary
    if not rating_summary:
        rating_summary = TutorRatingSummary(tutor_id=tutor_profile.id)
        db.session.add(rating_summary)
        db.session.commit()
    
    return render_template('tutor/reviews.html',
                           reviews=reviews,
                           rating_summary=rating_summary)


@bp.route('/subjects')
@login_required
@tutor_required
def subjects():
    """Manage tutor subjects"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    # Get current subjects
    current_subjects = tutor_profile.subjects
    
    # Get all subjects for selection
    all_subjects = Subject.query.all()
    
    return render_template('tutor/subjects.html',
                           current_subjects=current_subjects,
                           all_subjects=all_subjects)


@bp.route('/subjects/<int:subject_id>/add', methods=['POST'])
@login_required
@tutor_required
def add_subject(subject_id):
    """Add a subject to tutor's profile"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    subject = Subject.query.get_or_404(subject_id)
    
    # Check if already added
    if any(s.id == subject.id for s in tutor_profile.subjects):
        flash('Subject already added to your profile', 'warning')
        return redirect(url_for('tutor.subjects'))
    
    # Add subject
    tutor_subject = TutorSubject(
        tutor_id=tutor_profile.id,
        subject_id=subject.id,
        proficiency_level=request.form.get('proficiency_level', 'Intermediate')
    )
    db.session.add(tutor_subject)
    db.session.commit()
    
    flash('Subject added successfully', 'success')
    return redirect(url_for('tutor.subjects'))


@bp.route('/subjects/<int:subject_id>/remove', methods=['POST'])
@login_required
@tutor_required
def remove_subject(subject_id):
    """Remove a subject from tutor's profile"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    # Remove subject
    tutor_subject = TutorSubject.query.filter_by(
        tutor_id=tutor_profile.id,
        subject_id=subject_id
    ).first()
    
    if tutor_subject:
        db.session.delete(tutor_subject)
        db.session.commit()
        flash('Subject removed successfully', 'success')
    
    return redirect(url_for('tutor.subjects'))


@bp.route('/settings')
@login_required
@tutor_required
def settings():
    """Tutor settings"""
    return render_template('tutor/settings.html')