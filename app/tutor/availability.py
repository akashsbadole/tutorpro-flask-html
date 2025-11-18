from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import pytz
import calendar
from sqlalchemy import or_, and_
from app.tutor import bp
from app.utils.decorators import tutor_required
from app.models.user import User, UserProfile
from app.models.tutor import TutorProfile
from app.models.course import Subject, Course
from app.models.booking import Booking, TutorAvailability
from app.tutor.forms import AvailabilityForm, BulkAvailabilityForm
from app import db
from app.utils.errors import ValidationError
import csv
import io
from dateutil import parser
import json


@bp.route('/availability')
@login_required
@tutor_required
def availability():
    """Manage tutor availability with calendar interface"""
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
    
    # Get user profile for timezone
    user_profile = current_user.user_profile
    timezone = user_profile.timezone if user_profile else 'UTC'
    
    return render_template('tutor/availability.html', 
                           tutor_profile=tutor_profile,
                           availabilities=availabilities,
                           bookings=bookings,
                           start_date=start_date,
                           end_date=end_date,
                           timezone=timezone)


@bp.route('/availability/calendar')
@login_required
@tutor_required
def availability_calendar():
    """Display availability in calendar format"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    # Get current month and year
    today = datetime.now()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    
    # Get availability for the month
    availabilities = TutorAvailability.query.filter_by(tutor_id=tutor_profile.id).all()
    
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
            'has_availability': False,
            'availability': None
        }
        
        # Check for bookings
        day_bookings = [b for b in bookings if b.scheduled_time.date() == current_date.date()]
        if day_bookings:
            day_data['has_booking'] = True
            day_data['booking_count'] = len(day_bookings)
        
        # Check for availability
        day_availability = [a for a in availabilities if a.day_of_week == current_date.weekday()]
        if day_availability:
            day_data['has_availability'] = True
            day_data['availability'] = day_availability[0]
        
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
    
    return render_template('tutor/availability_calendar.html',
                           calendar_data=calendar_data,
                           year=year,
                           month=month,
                           prev_month=prev_month,
                           prev_year=prev_year,
                           next_month=next_month,
                           next_year=next_year,
                           month_name=calendar.month_name[month])


@bp.route('/availability/update', methods=['POST'])
@login_required
@tutor_required
def update_availability():
    """Update tutor availability"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    form = AvailabilityForm()
    
    if form.validate_on_submit():
        # Check if availability already exists
        availability = TutorAvailability.query.filter_by(
            tutor_id=tutor_profile.id,
            day_of_week=form.day_of_week.data
        ).first()
        
        if availability:
            # Update existing availability
            availability.start_time = form.start_time.data
            availability.end_time = form.end_time.data
            availability.is_available = form.is_available.data
        else:
            # Create new availability
            availability = TutorAvailability(
                tutor_id=tutor_profile.id,
                day_of_week=form.day_of_week.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                is_available=form.is_available.data
            )
            db.session.add(availability)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Availability updated successfully'})
    
    return jsonify({'error': 'Invalid form data'}), 400


@bp.route('/availability/delete/<int:availability_id>', methods=['POST'])
@login_required
@tutor_required
def delete_availability(availability_id):
    """Delete tutor availability"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    availability = TutorAvailability.query.get_or_404(availability_id)
    
    if availability.tutor_id != tutor_profile.id:
        return jsonify({'error': 'You do not have permission to delete this availability'}), 403
    
    db.session.delete(availability)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Availability deleted successfully'})


@bp.route('/availability/bulk-import', methods=['POST'])
@login_required
@tutor_required
def bulk_import_availability():
    """Import availability from CSV"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    form = BulkAvailabilityForm()
    
    if form.validate_on_submit():
        csv_file = form.csv_file.data
        if csv_file:
            try:
                # Read CSV file
                stream = io.StringIO(csv_file.stream.read().decode('utf-8'))
                csv_reader = csv.DictReader(stream)
                
                # Process each row
                for row in csv_reader:
                    day_of_week = int(row.get('day_of_week', 0))
                    start_time = datetime.strptime(row.get('start_time', '00:00'), '%H:%M').time()
                    end_time = datetime.strptime(row.get('end_time', '00:00'), '%H:%M').time()
                    is_available = row.get('is_available', 'true').lower() == 'true'
                    
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
                return jsonify({'success': True, 'message': 'Availability imported successfully'})
            
            except Exception as e:
                current_app.logger.error(f"Error importing availability: {str(e)}")
                return jsonify({'error': 'Error importing availability'}), 500
    
    return jsonify({'error': 'Invalid form data'}), 400


@bp.route('/availability/bulk-export')
@login_required
@tutor_required
def bulk_export_availability():
    """Export availability to CSV"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    # Get availability
    availabilities = TutorAvailability.query.filter_by(tutor_id=tutor_profile.id).all()
    
    # Create CSV content
    output = io.StringIO()
    fieldnames = ['day_of_week', 'day_name', 'start_time', 'end_time', 'is_available']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    # Write header
    writer.writeheader()
    
    # Write data
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for availability in availabilities:
        writer.writerow({
            'day_of_week': availability.day_of_week,
            'day_name': day_names[availability.day_of_week],
            'start_time': availability.start_time.strftime('%H:%M'),
            'end_time': availability.end_time.strftime('%H:%M'),
            'is_available': availability.is_available
        })
    
    # Create response
    output.seek(0)
    response = current_app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=availability.csv'}
    )
    
    return response


@bp.route('/availability/check-availability')
@login_required
@tutor_required
def check_availability():
    """Check if tutor is available at a specific time"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    # Get parameters
    datetime_str = request.args.get('datetime')
    duration = request.args.get('duration', type=int, default=60)
    
    if not datetime_str:
        return jsonify({'error': 'Datetime parameter is required'}), 400
    
    try:
        # Parse datetime
        dt = parser.parse(datetime_str)
        
        # Get timezone
        user_profile = current_user.user_profile
        timezone = user_profile.timezone if user_profile else 'UTC'
        
        # Convert to UTC if needed
        if timezone != 'UTC':
            tz = pytz.timezone(timezone)
            if dt.tzinfo is None:
                dt = tz.localize(dt)
            dt = dt.astimezone(pytz.UTC)
        
        # Check day of week
        day_of_week = dt.weekday()
        
        # Get availability for this day
        availability = TutorAvailability.query.filter_by(
            tutor_id=tutor_profile.id,
            day_of_week=day_of_week,
            is_available=True
        ).first()
        
        if not availability:
            return jsonify({
                'available': False,
                'message': 'No availability set for this day'
            })
        
        # Check time range
        start_time = datetime.combine(dt.date(), availability.start_time)
        end_time = datetime.combine(dt.date(), availability.end_time)
        
        if dt < start_time or dt >= end_time:
            return jsonify({
                'available': False,
                'message': 'Time is outside of availability hours'
            })
        
        # Check for overlapping bookings
        end_time_booking = dt + timedelta(minutes=duration)
        
        overlapping_booking = Booking.query.filter(
            Booking.tutor_id == tutor_profile.id,
            Booking.status.in_(['Pending', 'Confirmed']),
            or_(
                and_(
                    Booking.scheduled_time <= dt,
                    Booking.end_time >= dt
                ),
                and_(
                    Booking.scheduled_time <= end_time_booking,
                    Booking.end_time >= end_time_booking
                ),
                and_(
                    Booking.scheduled_time >= dt,
                    Booking.end_time <= end_time_booking
                )
            )
        ).first()
        
        if overlapping_booking:
            return jsonify({
                'available': False,
                'message': 'Time slot already booked',
                'booking_id': overlapping_booking.id
            })
        
        return jsonify({
            'available': True,
            'message': 'Time slot is available'
        })
    
    except Exception as e:
        current_app.logger.error(f"Error checking availability: {str(e)}")
        return jsonify({'error': 'Error checking availability'}), 500


@bp.route('/availability/set-special-availability', methods=['POST'])
@login_required
@tutor_required
def set_special_availability():
    """Set special availability for a specific date"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    # Get parameters
    date_str = request.form.get('date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    is_available = request.form.get('is_available', 'true').lower() == 'true'
    
    if not date_str or not start_time or not end_time:
        return jsonify({'error': 'Date, start time, and end time are required'}), 400
    
    try:
        # Parse date and times
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = datetime.strptime(end_time, '%H:%M').time()
        
        # Check if special availability already exists for this date
        special_availability = SpecialAvailability.query.filter_by(
            tutor_id=tutor_profile.id,
            date=date
        ).first()
        
        if special_availability:
            # Update existing special availability
            special_availability.start_time = start_time
            special_availability.end_time = end_time
            special_availability.is_available = is_available
        else:
            # Create new special availability
            special_availability = SpecialAvailability(
                tutor_id=tutor_profile.id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                is_available=is_available
            )
            db.session.add(special_availability)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Special availability set successfully'})
    
    except Exception as e:
        current_app.logger.error(f"Error setting special availability: {str(e)}")
        return jsonify({'error': 'Error setting special availability'}), 500


@bp.route('/availability/special-availability/<int:special_availability_id>', methods=['DELETE'])
@login_required
@tutor_required
def delete_special_availability(special_availability_id):
    """Delete special availability"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    special_availability = SpecialAvailability.query.get_or_404(special_availability_id)
    
    if special_availability.tutor_id != tutor_profile.id:
        return jsonify({'error': 'You do not have permission to delete this special availability'}), 403
    
    db.session.delete(special_availability)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Special availability deleted successfully'})


@bp.route('/availability/time-slots')
@login_required
@tutor_required
def get_available_time_slots():
    """Get available time slots for a specific date"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    # Get parameters
    date_str = request.args.get('date')
    duration = request.args.get('duration', type=int, default=60)
    
    if not date_str:
        return jsonify({'error': 'Date parameter is required'}), 400
    
    try:
        # Parse date
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get day of week
        day_of_week = date.weekday()
        
        # Get regular availability for this day
        regular_availability = TutorAvailability.query.filter_by(
            tutor_id=tutor_profile.id,
            day_of_week=day_of_week,
            is_available=True
        ).first()
        
        if not regular_availability:
            return jsonify({'available_slots': []})
        
        # Check for special availability
        special_availability = SpecialAvailability.query.filter_by(
            tutor_id=tutor_profile.id,
            date=date
        ).first()
        
        # Use special availability if it exists
        if special_availability:
            start_time = special_availability.start_time
            end_time = special_availability.end_time
        else:
            start_time = regular_availability.start_time
            end_time = regular_availability.end_time
        
        # Get existing bookings for this date
        bookings = Booking.query.filter(
            Booking.tutor_id == tutor_profile.id,
            Booking.scheduled_time >= datetime.combine(date, datetime.min.time()),
            Booking.scheduled_time <= datetime.combine(date, datetime.max.time()),
            Booking.status.in_(['Pending', 'Confirmed'])
        ).order_by(Booking.scheduled_time.asc()).all()
        
        # Generate available time slots
        available_slots = []
        current_time = datetime.combine(date, start_time)
        
        while current_time + timedelta(minutes=duration) <= datetime.combine(date, end_time):
            # Check if this time slot conflicts with any booking
            conflict = False
            for booking in bookings:
                booking_start = booking.scheduled_time
                booking_end = booking.end_time
                
                if (current_time < booking_end and 
                    current_time + timedelta(minutes=duration) > booking_start):
                    conflict = True
                    break
            
            if not conflict:
                available_slots.append({
                    'start_time': current_time.strftime('%H:%M'),
                    'end_time': (current_time + timedelta(minutes=duration)).strftime('%H:%M'),
                    'datetime': current_time.isoformat()
                })
            
            # Move to next slot (15-minute intervals)
            current_time += timedelta(minutes=15)
        
        return jsonify({'available_slots': available_slots})
    
    except Exception as e:
        current_app.logger.error(f"Error getting available time slots: {str(e)}")
        return jsonify({'error': 'Error getting available time slots'}), 500