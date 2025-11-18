from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.student import bp
from app.utils.decorators import learner_required
from app.models.user import User, UserProfile, LearnerProfile
from app.models.tutor import TutorProfile
from app.models.course import Course, Subject
from app.models.booking import Booking, DemoRequest
from app.models.payment import Payment, PaymentMethod
from app.models.review import Review
from app import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json


@bp.route('/dashboard')
@login_required
@learner_required
def dashboard():
    """Learner dashboard with key metrics and statistics"""
    # Get learner profile
    learner_profile = current_user.learner_profile
    if not learner_profile:
        # Create learner profile if it doesn't exist
        learner_profile = LearnerProfile(user_id=current_user.id)
        db.session.add(learner_profile)
        db.session.commit()
    
    # Get booking statistics
    total_bookings = Booking.query.filter_by(student_id=current_user.id).count()
    upcoming_bookings = Booking.query.filter(
        Booking.student_id == current_user.id,
        Booking.scheduled_time > datetime.utcnow(),
        Booking.status.in_(['Pending', 'Confirmed'])
    ).count()
    
    # Get payment statistics
    total_spent = db.session.query(func.sum(Payment.amount)).join(
        Booking, Booking.id == Payment.booking_id
    ).filter(
        Booking.student_id == current_user.id,
        Payment.status == 'Completed'
    ).scalar() or 0
    
    # Get review statistics
    reviews_written = Review.query.filter_by(reviewer_id=current_user.id).count()
    
    # Get upcoming bookings
    upcoming_booking_list = Booking.query.filter(
        Booking.student_id == current_user.id,
        Booking.scheduled_time > datetime.utcnow(),
        Booking.status.in_(['Pending', 'Confirmed'])
    ).order_by(Booking.scheduled_time.asc()).limit(5).all()
    
    # Get recent bookings
    recent_bookings = Booking.query.filter(
        Booking.student_id == current_user.id,
        Booking.scheduled_time <= datetime.utcnow()
    ).order_by(Booking.scheduled_time.desc()).limit(5).all()
    
    # Get enrolled courses
    enrolled_courses = db.session.query(Course).join(
        Booking, Booking.course_id == Course.id
    ).filter(
        Booking.student_id == current_user.id
    ).distinct().all()
    
    return render_template('student/dashboard.html', 
                           learner_profile=learner_profile,
                           total_bookings=total_bookings,
                           upcoming_bookings=upcoming_bookings,
                           total_spent=total_spent,
                           reviews_written=reviews_written,
                           upcoming_booking_list=upcoming_booking_list,
                           recent_bookings=recent_bookings,
                           enrolled_courses=enrolled_courses)


@bp.route('/profile')
@login_required
@learner_required
def profile():
    """View and edit learner profile"""
    learner_profile = current_user.learner_profile
    if not learner_profile:
        # Create learner profile if it doesn't exist
        learner_profile = LearnerProfile(user_id=current_user.id)
        db.session.add(learner_profile)
        db.session.commit()
    
    return render_template('student/profile.html', learner_profile=learner_profile)


@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@learner_required
def edit_profile():
    """Edit learner profile"""
    learner_profile = current_user.learner_profile
    if not learner_profile:
        # Create learner profile if it doesn't exist
        learner_profile = LearnerProfile(user_id=current_user.id)
        db.session.add(learner_profile)
        db.session.commit()
    
    if request.method == 'POST':
        # Update learner profile
        learner_profile.learning_goals = request.form.get('learning_goals', learner_profile.learning_goals)
        learner_profile.preferred_subjects = request.form.get('preferred_subjects', learner_profile.preferred_subjects)
        learner_profile.budget_range_min = float(request.form.get('budget_range_min', learner_profile.budget_range_min or 0))
        learner_profile.budget_range_max = float(request.form.get('budget_range_max', learner_profile.budget_range_max or 0))
        learner_profile.preferred_tutor_gender = request.form.get('preferred_tutor_gender', learner_profile.preferred_tutor_gender)
        learner_profile.experience_level = request.form.get('experience_level', learner_profile.experience_level)
        learner_profile.language_preference = request.form.get('language_preference', learner_profile.language_preference)
        
        # Update user profile
        if current_user.user_profile:
            current_user.user_profile.first_name = request.form.get('first_name', current_user.user_profile.first_name)
            current_user.user_profile.last_name = request.form.get('last_name', current_user.user_profile.last_name)
            current_user.user_profile.phone = request.form.get('phone', current_user.user_profile.phone)
            current_user.user_profile.bio = request.form.get('bio', current_user.user_profile.bio)
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('student.profile'))
    
    return render_template('student/edit_profile.html', learner_profile=learner_profile)


@bp.route('/bookings')
@login_required
@learner_required
def bookings():
    """View all bookings"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
    query = Booking.query.filter_by(student_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    bookings = query.order_by(Booking.scheduled_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('student/bookings.html', bookings=bookings, status=status)


@bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@learner_required
def cancel_booking(booking_id):
    """Cancel a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.student_id != current_user.id:
        flash('You do not have permission to modify this booking', 'danger')
        return redirect(url_for('student.bookings'))
    
    booking.status = 'Cancelled'
    db.session.commit()
    
    flash('Booking cancelled successfully', 'success')
    return redirect(url_for('student.bookings'))


@bp.route('/courses')
@login_required
@learner_required
def courses():
    """View enrolled courses"""
    enrolled_courses = db.session.query(Course).join(
        Booking, Booking.course_id == Course.id
    ).filter(
        Booking.student_id == current_user.id
    ).distinct().all()
    
    return render_template('student/courses.html', enrolled_courses=enrolled_courses)


@bp.route('/courses/<int:course_id>')
@login_required
@learner_required
def course_detail(course_id):
    """View course details"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user is enrolled in this course
    is_enrolled = Booking.query.filter_by(
        student_id=current_user.id,
        course_id=course_id
    ).first() is not None
    
    return render_template('student/course_detail.html', course=course, is_enrolled=is_enrolled)


@bp.route('/tutors')
@login_required
@learner_required
def tutors():
    """Browse and search tutors"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    subject = request.args.get('subject', '')
    rating = request.args.get('rating', '')
    price_min = request.args.get('price_min', '')
    price_max = request.args.get('price_max', '')
    
    query = TutorProfile.query.filter_by(is_verified=True)
    
    if subject:
        query = query.join(TutorSubject).filter(TutorSubject.subject_id == subject)
    
    if rating:
        query = query.filter(TutorProfile.rating >= float(rating))
    
    if price_min:
        query = query.filter(TutorProfile.hourly_rate >= float(price_min))
    
    if price_max:
        query = query.filter(TutorProfile.hourly_rate <= float(price_max))
    
    tutors = query.order_by(desc(TutorProfile.rating)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get all subjects for filter
    subjects = Subject.query.all()
    
    return render_template('student/tutors.html', 
                           tutors=tutors,
                           subjects=subjects,
                           subject=subject,
                           rating=rating,
                           price_min=price_min,
                           price_max=price_max)


@bp.route('/tutors/<int:tutor_id>')
@login_required
@learner_required
def tutor_detail(tutor_id):
    """View tutor details"""
    tutor_profile = TutorProfile.query.get_or_404(tutor_id)
    
    # Get tutor's subjects
    subjects = tutor_profile.subjects
    
    # Get upcoming availability
    now = datetime.utcnow()
    upcoming_availabilities = []
    
    # Get bookings for the next 7 days
    start_date = now
    end_date = now + timedelta(days=7)
    
    bookings = Booking.query.filter(
        Booking.tutor_id == tutor_profile.id,
        Booking.scheduled_time >= start_date,
        Booking.scheduled_time <= end_date
    ).order_by(Booking.scheduled_time.asc()).all()
    
    # Get reviews
    reviews = Review.query.filter_by(tutor_id=tutor_profile.id).order_by(
        Review.created_at.desc()
    ).limit(5).all()
    
    return render_template('student/tutor_detail.html',
                           tutor_profile=tutor_profile,
                           subjects=subjects,
                           bookings=bookings,
                           reviews=reviews)


@bp.route('/demo-request', methods=['GET', 'POST'])
@login_required
@learner_required
def demo_request():
    """Request a demo class"""
    tutor_id = request.args.get('tutor_id', type=int)
    tutor = TutorProfile.query.get_or_404(tutor_id)
    
    if request.method == 'POST':
        demo_request = DemoRequest(
            student_id=current_user.id,
            tutor_id=tutor_id,
            preferred_date=request.form.get('preferred_date'),
            preferred_time=request.form.get('preferred_time'),
            duration_minutes=int(request.form.get('duration_minutes', 30)),
            notes=request.form.get('notes')
        )
        db.session.add(demo_request)
        db.session.commit()
        
        flash('Demo request submitted successfully', 'success')
        return redirect(url_for('student.tutor_detail', tutor_id=tutor_id))
    
    return render_template('student/demo_request.html', tutor=tutor)


@bp.route('/payments')
@login_required
@learner_required
def payments():
    """View payment history"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
    query = Payment.query.join(
        Booking, Booking.id == Payment.booking_id
    ).filter(
        Booking.student_id == current_user.id
    )
    
    if status:
        query = query.filter_by(status=status)
    
    payments = query.order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('student/payments.html', payments=payments, status=status)


@bp.route('/payment-methods')
@login_required
@learner_required
def payment_methods():
    """Manage payment methods"""
    payment_methods = current_user.payment_methods
    
    return render_template('student/payment_methods.html', payment_methods=payment_methods)


@bp.route('/payment-methods/new', methods=['GET', 'POST'])
@login_required
@learner_required
def new_payment_method():
    """Add a new payment method"""
    if request.method == 'POST':
        payment_method = PaymentMethod(
            user_id=current_user.id,
            payment_type=request.form.get('payment_type'),
            method_details=request.form.get('method_details')
        )
        db.session.add(payment_method)
        db.session.commit()
        
        # Set as default if requested
        if 'set_as_default' in request.form:
            payment_method.set_as_default()
        
        flash('Payment method added successfully', 'success')
        return redirect(url_for('student.payment_methods'))
    
    return render_template('student/new_payment_method.html')


@bp.route('/payment-methods/<int:payment_id>/delete', methods=['POST'])
@login_required
@learner_required
def delete_payment_method(payment_id):
    """Delete a payment method"""
    payment_method = PaymentMethod.query.get_or_404(payment_id)
    
    if payment_method.user_id != current_user.id:
        flash('You do not have permission to modify this payment method', 'danger')
        return redirect(url_for('student.payment_methods'))
    
    db.session.delete(payment_method)
    db.session.commit()
    
    flash('Payment method deleted successfully', 'success')
    return redirect(url_for('student.payment_methods'))


@bp.route('/reviews')
@login_required
@learner_required
def reviews():
    """View reviews written by the learner"""
    reviews = Review.query.filter_by(reviewer_id=current_user.id).order_by(
        Review.created_at.desc()
    ).all()
    
    return render_template('student/reviews.html', reviews=reviews)


@bp.route('/reviews/<int:booking_id>/new', methods=['GET', 'POST'])
@login_required
@learner_required
def new_review(booking_id):
    """Write a review for a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user is the student and booking is completed
    if booking.student_id != current_user.id or booking.status != 'Completed':
        flash('You cannot review this booking', 'danger')
        return redirect(url_for('student.bookings'))
    
    # Check if review already exists
    existing_review = Review.query.filter_by(
        reviewer_id=current_user.id,
        booking_id=booking_id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this booking', 'warning')
        return redirect(url_for('student.bookings'))
    
    if request.method == 'POST':
        review = Review(
            reviewer_id=current_user.id,
            tutor_id=booking.tutor_id,
            booking_id=booking_id,
            rating=int(request.form.get('rating')),
            comment=request.form.get('comment'),
            is_verified=True,
            is_public=True
        )
        db.session.add(review)
        db.session.commit()
        
        # Update tutor rating summary
        tutor_rating_summary = booking.tutor.rating_summary
        if not tutor_rating_summary:
            tutor_rating_summary = TutorRatingSummary(tutor_id=booking.tutor_id)
            db.session.add(tutor_rating_summary)
        
        tutor_rating_summary.update_ratings()
        db.session.commit()
        
        flash('Review submitted successfully', 'success')
        return redirect(url_for('student.bookings'))
    
    return render_template('student/new_review.html', booking=booking)


@bp.route('/settings')
@login_required
@learner_required
def settings():
    """Learner settings"""
    return render_template('student/settings.html')