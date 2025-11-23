from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from app.tutor import bp
from app.utils.decorators import tutor_required
from app.models.user import User, UserProfile
from app.models.tutor import TutorProfile
from app.models.course import Course
from app.models import Subject
from app.models.booking import Booking
from app.models.tutor import TutorAvailability
from app.models.demo import DemoSession as DemoRequest
# from app.models.booking import MeetingLink
from app.models.payment import Payment
from app.tutor.forms import BookingForm, RescheduleForm, FeedbackForm, MeetingLinkForm
from app import db
from app.utils.errors import ValidationError
import pytz
import uuid
import random
import string
from dateutil import parser


@bp.route('/bookings')
@login_required
@tutor_required
def bookings():
    """View all bookings"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    date_filter = request.args.get('date_filter', '')
    
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    query = Booking.query.filter_by(tutor_id=tutor_profile.id)
    
    if status:
        query = query.filter_by(status=status)
    
    if date_filter:
        if date_filter == 'today':
            today = datetime.utcnow().date()
            query = query.filter(Booking.scheduled_time >= today)
        elif date_filter == 'week':
            start_of_week = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
            query = query.filter(Booking.scheduled_time >= start_of_week)
        elif date_filter == 'month':
            start_of_month = datetime.utcnow().replace(day=1)
            query = query.filter(Booking.scheduled_time >= start_of_month)
    
    bookings = query.order_by(Booking.scheduled_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get booking statistics
    total_bookings = Booking.query.filter_by(tutor_id=tutor_profile.id).count()
    upcoming_bookings = Booking.query.filter(
        Booking.tutor_id == tutor_profile.id,
        Booking.scheduled_time > datetime.utcnow(),
        Booking.status.in_(['Pending', 'Confirmed'])
    ).count()
    completed_bookings = Booking.query.filter(
        Booking.tutor_id == tutor_profile.id,
        Booking.status == 'Completed'
    ).count()
    
    return render_template('tutor/bookings.html', 
                           bookings=bookings,
                           status=status,
                           date_filter=date_filter,
                           total_bookings=total_bookings,
                           upcoming_bookings=upcoming_bookings,
                           completed_bookings=completed_bookings)


@bp.route('/bookings/<int:booking_id>')
@login_required
@tutor_required
def booking_details(booking_id):
    """View booking details"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.tutor_id != current_user.tutor_profile.id:
        flash('You do not have permission to view this booking', 'danger')
        return redirect(url_for('tutor.bookings'))
    
    # Get meeting link if exists
    meeting_link = booking.meeting_link
    
    return render_template('tutor/booking_details.html', 
                           booking=booking,
                           meeting_link=meeting_link)


@bp.route('/bookings/<int:booking_id>/confirm', methods=['POST'])
@login_required
@tutor_required
def confirm_booking(booking_id):
    """Confirm a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.tutor_id != current_user.tutor_profile.id:
        return jsonify({'error': 'You do not have permission to modify this booking'}), 403
    
    booking.status = 'Confirmed'
    db.session.commit()
    
    # Generate meeting link
    generate_meeting_link(booking)
    
    return jsonify({'success': True, 'message': 'Booking confirmed successfully'})


@bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@tutor_required
def cancel_booking(booking_id):
    """Cancel a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.tutor_id != current_user.tutor_profile.id:
        return jsonify({'error': 'You do not have permission to modify this booking'}), 403
    
    booking.status = 'Cancelled'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Booking cancelled successfully'})


@bp.route('/bookings/<int:booking_id>/reschedule', methods=['GET', 'POST'])
@login_required
@tutor_required
def reschedule_booking(booking_id):
    """Reschedule a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.tutor_id != current_user.tutor_profile.id:
        flash('You do not have permission to modify this booking', 'danger')
        return redirect(url_for('tutor.bookings'))
    
    form = RescheduleForm()
    
    if form.validate_on_submit():
        # Check for conflicts
        conflict = check_booking_conflict(
            booking.tutor_id,
            form.new_scheduled_time.data,
            form.new_duration_minutes.data,
            booking.id
        )
        
        if conflict:
            flash('This time slot conflicts with another booking', 'danger')
            return render_template('tutor/reschedule_booking.html', 
                                   booking=booking, 
                                   form=form,
                                   conflict=True)
        
        # Update booking
        booking.scheduled_time = form.new_scheduled_time.data
        booking.duration_minutes = form.new_duration_minutes.data
        booking.notes = form.notes.data
        db.session.commit()
        
        # Generate new meeting link
        generate_meeting_link(booking)
        
        flash('Booking rescheduled successfully', 'success')
        return redirect(url_for('tutor.booking_details', booking_id=booking.id))
    
    # Pre-fill form with current values
    form.new_scheduled_time.data = booking.scheduled_time
    form.new_duration_minutes.data = booking.duration_minutes
    form.notes.data = booking.notes or ''
    
    return render_template('tutor/reschedule_booking.html', 
                           booking=booking, 
                           form=form,
                           conflict=False)


@bp.route('/bookings/<int:booking_id>/complete', methods=['POST'])
@login_required
@tutor_required
def complete_booking(booking_id):
    """Mark a booking as completed"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.tutor_id != current_user.tutor_profile.id:
        return jsonify({'error': 'You do not have permission to modify this booking'}), 403
    
    booking.status = 'Completed'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Booking marked as completed'})


@bp.route('/bookings/<int:booking_id>/feedback', methods=['GET', 'POST'])
@login_required
@tutor_required
def booking_feedback(booking_id):
    """Collect feedback for a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.tutor_id != current_user.tutor_profile.id:
        flash('You do not have permission to view this booking', 'danger')
        return redirect(url_for('tutor.bookings'))
    
    if booking.status != 'Completed':
        flash('Feedback can only be collected for completed bookings', 'warning')
        return redirect(url_for('tutor.booking_details', booking_id=booking.id))
    
    form = FeedbackForm()
    
    if form.validate_on_submit():
        # Create feedback record
        feedback = BookingFeedback(
            booking_id=booking.id,
            rating=form.rating.data,
            teaching_quality=form.teaching_quality.data,
            communication=form.communication.data,
            preparation=form.preparation.data,
            value_for_money=form.value_for_money.data,
            comments=form.comments.data,
            would_recommend=form.would_recommend.data
        )
        db.session.add(feedback)
        db.session.commit()
        
        flash('Feedback collected successfully', 'success')
        return redirect(url_for('tutor.booking_details', booking_id=booking.id))
    
    return render_template('tutor/booking_feedback.html', 
                           booking=booking, 
                           form=form)


@bp.route('/bookings/<int:booking_id>/meeting-link', methods=['GET', 'POST'])
@login_required
@tutor_required
def generate_meeting_link(booking_id):
    """Generate meeting link for a booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.tutor_id != current_user.tutor_profile.id:
        return jsonify({'error': 'You do not have permission to modify this booking'}), 403
    
    form = MeetingLinkForm()
    
    if form.validate_on_submit():
        # Check if meeting link already exists
        if booking.meeting_link:
            # Update existing meeting link
            meeting_link = booking.meeting_link
            meeting_link.platform = form.platform.data
            meeting_link.meeting_url = form.meeting_url.data
            meeting_link.meeting_id = form.meeting_id.data
            meeting_link.password = form.password.data
            meeting_link.expires_at = form.expires_at.data
        else:
            # Create new meeting link
            meeting_link = MeetingLink(
                booking_id=booking.id,
                platform=form.platform.data,
                meeting_url=form.meeting_url.data,
                meeting_id=form.meeting_id.data,
                password=form.password.data,
                expires_at=form.expires_at.data
            )
            db.session.add(meeting_link)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Meeting link updated successfully'})
    
    # Pre-fill form with existing values
    if booking.meeting_link:
        form.platform.data = booking.meeting_link.platform
        form.meeting_url.data = booking.meeting_link.meeting_url
        form.meeting_id.data = booking.meeting_link.meeting_id
        form.password.data = booking.meeting_link.password
        form.expires_at.data = booking.meeting_link.expires_at
    
    return render_template('tutor/meeting_link.html', 
                           booking=booking, 
                           form=form)


@bp.route('/bookings/calendar')
@login_required
@tutor_required
def bookings_calendar():
    """Display bookings in calendar format"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    # Get current month and year
    today = datetime.now()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    
    # Get bookings for the month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    bookings = Booking.query.filter(
        Booking.tutor_id == tutor_profile.id,
        Booking.scheduled_time >= start_date,
        Booking.scheduled_time <= end_date
    ).order_by(Booking.scheduled_time.asc()).all()
    
    # Build calendar data
    calendar_data = []
    current_date = start_date
    
    while current_date <= end_date:
        day_data = {
            'date': current_date.strftime('%Y-%m-%d'),
            'day_of_week': current_date.weekday(),
            'day_name': calendar.day_name[current_date.weekday()],
            'date_num': current_date.day,
            'is_weekend': current_date.weekday() >= 5,
            'has_booking': False,
            'booking_count': 0,
            'bookings': []
        }
        
        # Check for bookings
        day_bookings = [b for b in bookings if b.scheduled_time.date() == current_date.date()]
        if day_bookings:
            day_data['has_booking'] = True
            day_data['booking_count'] = len(day_bookings)
            day_data['bookings'] = day_bookings
        
        calendar_data.append(day_data)
        current_date += timedelta(days=1)
    
    # Get previous and next month
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    return render_template('tutor/bookings_calendar.html',
                           calendar_data=calendar_data,
                           year=year,
                           month=month,
                           prev_month=prev_month,
                           prev_year=prev_year,
                           next_month=next_month,
                           next_year=next_year,
                           month_name=calendar.month_name[month])


@bp.route('/bookings/check-availability')
@login_required
@tutor_required
def check_booking_availability():
    """Check if a time slot is available for booking"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    # Get parameters
    datetime_str = request.args.get('datetime')
    duration = request.args.get('duration', type=int, default=60)
    exclude_booking_id = request.args.get('exclude_booking_id', type=int, default=None)
    
    if not datetime_str:
        return jsonify({'error': 'Datetime parameter is required'}), 400
    
    try:
        # Parse datetime
        dt = parser.parse(datetime_str)
        
        # Check for conflicts
        conflict = check_booking_conflict(tutor_profile.id, dt, duration, exclude_booking_id)
        
        if conflict:
            return jsonify({
                'available': False,
                'message': 'Time slot conflicts with another booking',
                'conflicting_booking_id': conflict.id
            })
        
        return jsonify({
            'available': True,
            'message': 'Time slot is available'
        })
    
    except Exception as e:
        current_app.logger.error(f"Error checking booking availability: {str(e)}")
        return jsonify({'error': 'Error checking availability'}), 500


@bp.route('/bookings/export')
@login_required
@tutor_required
def export_bookings():
    """Export bookings to CSV"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    # Get filter parameters
    status = request.args.get('status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Build query
    query = Booking.query.filter_by(tutor_id=tutor_profile.id)
    
    if status:
        query = query.filter_by(status=status)
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Booking.scheduled_time >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Booking.scheduled_time <= end_date)
    
    bookings = query.order_by(Booking.scheduled_time.desc()).all()
    
    # Create CSV content
    output = io.StringIO()
    fieldnames = [
        'Booking ID', 'Student Email', 'Course Title', 'Scheduled Time', 
        'Duration', 'Status', 'Amount', 'Currency', 'Created At'
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    # Write header
    writer.writeheader()
    
    # Write data
    for booking in bookings:
        writer.writerow({
            'Booking ID': booking.id,
            'Student Email': booking.student.email,
            'Course Title': booking.course.title,
            'Scheduled Time': booking.scheduled_time.strftime('%Y-%m-%d %H:%M'),
            'Duration': f"{booking.duration_minutes} minutes",
            'Status': booking.status,
            'Amount': f"{booking.amount} {booking.currency}",
            'Created At': booking.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    # Create response
    output.seek(0)
    response = current_app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=bookings.csv'}
    )
    
    return response


# Helper functions
def check_booking_conflict(tutor_id, scheduled_time, duration_minutes, exclude_booking_id=None):
    """Check if a booking conflicts with existing bookings"""
    end_time = scheduled_time + timedelta(minutes=duration_minutes)
    
    query = Booking.query.filter(
        Booking.tutor_id == tutor_id,
        Booking.status.in_(['Pending', 'Confirmed']),
        or_(
            and_(
                Booking.scheduled_time <= scheduled_time,
                Booking.end_time >= scheduled_time
            ),
            and_(
                Booking.scheduled_time <= end_time,
                Booking.end_time >= end_time
            ),
            and_(
                Booking.scheduled_time >= scheduled_time,
                Booking.end_time <= end_time
            )
        )
    )
    
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    
    return query.first()


def generate_meeting_link(booking):
    """Generate a meeting link for a booking"""
    if not booking.meeting_link:
        # Create Zoom meeting link
        meeting_id = ''.join(random.choices(string.digits, k=11))
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        meeting_link = MeetingLink(
            booking_id=booking.id,
            platform='Zoom',
            meeting_url=f"https://zoom.us/j/{meeting_id}",
            meeting_id=meeting_id,
            password=password,
            expires_at=booking.scheduled_time + timedelta(hours=24)
        )
        db.session.add(meeting_link)
        db.session.commit()
        return meeting_link
    return booking.meeting_link


# Model for booking feedback (needs to be added to models)
class BookingFeedback(db.Model):
    """
    Model for booking feedback
    """
    __tablename__ = 'booking_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    teaching_quality = db.Column(db.Integer, nullable=False)
    communication = db.Column(db.Integer, nullable=False)
    preparation = db.Column(db.Integer, nullable=False)
    value_for_money = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    would_recommend = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    booking = db.relationship('Booking', backref='feedback')
    
    def __repr__(self):
        return f'<BookingFeedback {self.booking_id} - {self.rating}>'