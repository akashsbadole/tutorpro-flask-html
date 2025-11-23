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
# from app.models.booking import BookingFeedback, DemoRequestFeedback
from app.models.payment import Payment
from app.tutor.forms import DemoRequestForm, FeedbackForm
from app import db
from app.utils.errors import ValidationError
import pytz
import uuid
import random
import string
from dateutil import parser


@bp.route('/demos')
@login_required
@tutor_required
def demos():
    """View all demo requests"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    query = DemoRequest.query.filter_by(tutor_id=tutor_profile.id)
    
    if status:
        query = query.filter_by(status=status)
    
    demo_requests = query.order_by(DemoRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get demo request statistics
    total_demos = DemoRequest.query.filter_by(tutor_id=tutor_profile.id).count()
    pending_demos = DemoRequest.query.filter_by(tutor_id=tutor_profile.id, status='Pending').count()
    confirmed_demos = DemoRequest.query.filter_by(tutor_id=tutor_profile.id, status='Confirmed').count()
    completed_demos = DemoRequest.query.filter_by(tutor_id=tutor_profile.id, status='Completed').count()
    
    return render_template('tutor/demos.html', 
                           demo_requests=demo_requests,
                           status=status,
                           total_demos=total_demos,
                           pending_demos=pending_demos,
                           confirmed_demos=confirmed_demos,
                           completed_demos=completed_demos)


@bp.route('/demos/<int:demo_id>')
@login_required
@tutor_required
def demo_details(demo_id):
    """View demo request details"""
    demo_request = DemoRequest.query.get_or_404(demo_id)
    
    if demo_request.tutor_id != current_user.tutor_profile.id:
        flash('You do not have permission to view this demo request', 'danger')
        return redirect(url_for('tutor.demos'))
    
    # Get student profile
    student_profile = demo_request.student.user_profile
    
    return render_template('tutor/demo_details.html', 
                           demo_request=demo_request,
                           student_profile=student_profile)


@bp.route('/demos/<int:demo_id>/approve', methods=['POST'])
@login_required
@tutor_required
def approve_demo(demo_id):
    """Approve a demo request"""
    demo_request = DemoRequest.query.get_or_404(demo_id)
    
    if demo_request.tutor_id != current_user.tutor_profile.id:
        return jsonify({'error': 'You do not have permission to modify this demo request'}), 403
    
    demo_request.status = 'Confirmed'
    demo_request.scheduled_time = datetime.combine(
        demo_request.preferred_date,
        demo_request.preferred_time
    )
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Demo request approved successfully'})


@bp.route('/demos/<int:demo_id>/reject', methods=['POST'])
@login_required
@tutor_required
def reject_demo(demo_id):
    """Reject a demo request"""
    demo_request = DemoRequest.query.get_or_404(demo_id)
    
    if demo_request.tutor_id != current_user.tutor_profile.id:
        return jsonify({'error': 'You do not have permission to modify this demo request'}), 403
    
    demo_request.status = 'Cancelled'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Demo request rejected successfully'})


@bp.route('/demos/<int:demo_id>/reschedule', methods=['GET', 'POST'])
@login_required
@tutor_required
def reschedule_demo(demo_id):
    """Reschedule a demo request"""
    demo_request = DemoRequest.query.get_or_404(demo_id)
    
    if demo_request.tutor_id != current_user.tutor_profile.id:
        flash('You do not have permission to modify this demo request', 'danger')
        return redirect(url_for('tutor.demos'))
    
    if demo_request.status != 'Confirmed':
        flash('Only confirmed demo requests can be rescheduled', 'warning')
        return redirect(url_for('tutor.demo_details', demo_id=demo_id))
    
    form = DemoRequestForm()
    
    if form.validate_on_submit():
        # Check for conflicts
        conflict = check_demo_conflict(
            current_user.tutor_profile.id,
            form.preferred_date.data,
            form.preferred_time.data,
            form.duration_minutes.data,
            demo_id
        )
        
        if conflict:
            flash('This time slot conflicts with another demo or booking', 'danger')
            return render_template('tutor/reschedule_demo.html', 
                                   demo_request=demo_request, 
                                   form=form,
                                   conflict=True)
        
        # Update demo request
        demo_request.preferred_date = form.preferred_date.data
        demo_request.preferred_time = form.preferred_time.data
        demo_request.duration_minutes = form.duration_minutes.data
        demo_request.notes = form.notes.data
        demo_request.scheduled_time = datetime.combine(
            form.preferred_date.data,
            form.preferred_time.data
        )
        db.session.commit()
        
        flash('Demo request rescheduled successfully', 'success')
        return redirect(url_for('tutor.demo_details', demo_id=demo_request.id))
    
    # Pre-fill form with current values
    form.preferred_date.data = demo_request.preferred_date
    form.preferred_time.data = demo_request.preferred_time
    form.duration_minutes.data = demo_request.duration_minutes
    form.notes.data = demo_request.notes or ''
    
    return render_template('tutor/reschedule_demo.html', 
                           demo_request=demo_request, 
                           form=form,
                           conflict=False)


@bp.route('/demos/<int:demo_id>/complete', methods=['POST'])
@login_required
@tutor_required
def complete_demo(demo_id):
    """Mark a demo as completed"""
    demo_request = DemoRequest.query.get_or_404(demo_id)
    
    if demo_request.tutor_id != current_user.tutor_profile.id:
        return jsonify({'error': 'You do not have permission to modify this demo request'}), 403
    
    demo_request.status = 'Completed'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Demo marked as completed'})


@bp.route('/demos/<int:demo_id>/feedback', methods=['GET', 'POST'])
@login_required
@tutor_required
def demo_feedback(demo_id):
    """Collect feedback for a demo"""
    demo_request = DemoRequest.query.get_or_404(demo_id)
    
    if demo_request.tutor_id != current_user.tutor_profile.id:
        flash('You do not have permission to view this demo request', 'danger')
        return redirect(url_for('tutor.demos'))
    
    if demo_request.status != 'Completed':
        flash('Feedback can only be collected for completed demos', 'warning')
        return redirect(url_for('tutor.demo_details', demo_id=demo_id))
    
    # Check if feedback already exists
    existing_feedback = DemoRequestFeedback.query.filter_by(demo_request_id=demo_id).first()
    if existing_feedback:
        flash('Feedback already collected for this demo', 'info')
        return redirect(url_for('tutor.demo_details', demo_id=demo_id))
    
    form = FeedbackForm()
    
    if form.validate_on_submit():
        # Create feedback record
        feedback = DemoRequestFeedback(
            demo_request_id=demo_id,
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
        return redirect(url_for('tutor.demo_details', demo_id=demo_id))
    
    return render_template('tutor/demo_feedback.html', 
                           demo_request=demo_request, 
                           form=form)


@bp.route('/demos/calendar')
@login_required
@tutor_required
def demos_calendar():
    """Display demos in calendar format"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    # Get current month and year
    today = datetime.now()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    
    # Get demos for the month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    demo_requests = DemoRequest.query.filter(
        DemoRequest.tutor_id == tutor_profile.id,
        DemoRequest.scheduled_time >= start_date,
        DemoRequest.scheduled_time <= end_date,
        DemoRequest.status.in_(['Confirmed', 'Completed'])
    ).order_by(DemoRequest.scheduled_time.asc()).all()
    
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
            'has_demo': False,
            'demo_count': 0,
            'demos': []
        }
        
        # Check for demos
        day_demos = [d for d in demo_requests if d.scheduled_time.date() == current_date.date()]
        if day_demos:
            day_data['has_demo'] = True
            day_data['demo_count'] = len(day_demos)
            day_data['demos'] = day_demos
        
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
    
    return render_template('tutor/demos_calendar.html',
                           calendar_data=calendar_data,
                           year=year,
                           month=month,
                           prev_month=prev_month,
                           prev_year=prev_year,
                           next_month=next_month,
                           next_year=next_year,
                           month_name=calendar.month_name[month])


@bp.route('/demos/export')
@login_required
@tutor_required
def export_demos():
    """Export demos to CSV"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    # Get filter parameters
    status = request.args.get('status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Build query
    query = DemoRequest.query.filter_by(tutor_id=tutor_profile.id)
    
    if status:
        query = query.filter_by(status=status)
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(DemoRequest.preferred_date >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(DemoRequest.preferred_date <= end_date)
    
    demo_requests = query.order_by(DemoRequest.created_at.desc()).all()
    
    # Create CSV content
    import csv
    import io
    
    output = io.StringIO()
    fieldnames = [
        'Demo ID', 'Student Email', 'Preferred Date', 'Preferred Time', 
        'Duration', 'Status', 'Notes', 'Created At'
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    # Write header
    writer.writeheader()
    
    # Write data
    for demo in demo_requests:
        writer.writerow({
            'Demo ID': demo.id,
            'Student Email': demo.student.email,
            'Preferred Date': demo.preferred_date.strftime('%Y-%m-%d'),
            'Preferred Time': demo.preferred_time.strftime('%H:%M'),
            'Duration': f"{demo.duration_minutes} minutes",
            'Status': demo.status,
            'Notes': demo.notes or '',
            'Created At': demo.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    # Create response
    output.seek(0)
    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=demos.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response


# Helper functions
def check_demo_conflict(tutor_id, preferred_date, preferred_time, duration_minutes, exclude_demo_id=None):
    """Check if a demo conflicts with existing demos or bookings"""
    scheduled_time = datetime.combine(preferred_date, preferred_time)
    end_time = scheduled_time + timedelta(minutes=duration_minutes)
    
    # Check for conflicting demos
    demo_query = DemoRequest.query.filter(
        DemoRequest.tutor_id == tutor_id,
        DemoRequest.status.in_(['Confirmed', 'Completed']),
        or_(
            and_(
                DemoRequest.scheduled_time <= scheduled_time,
                DemoRequest.end_time >= scheduled_time
            ),
            and_(
                DemoRequest.scheduled_time <= end_time,
                DemoRequest.end_time >= end_time
            ),
            and_(
                DemoRequest.scheduled_time >= scheduled_time,
                DemoRequest.end_time <= end_time
            )
        )
    )
    
    if exclude_demo_id:
        demo_query = demo_query.filter(DemoRequest.id != exclude_demo_id)
    
    if demo_query.first():
        return True
    
    # Check for conflicting bookings
    booking_query = Booking.query.filter(
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
    
    if booking_query.first():
        return True
    
    return False

