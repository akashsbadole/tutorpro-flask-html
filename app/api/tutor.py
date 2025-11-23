from flask import Blueprint, jsonify, request
from flask_login import current_user
from app.models import Booking, TutorProfile, LearnerProfile, User
from app.models.demo import DemoSession
from app.utils.decorators import tutor_required
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

tutor_api = Blueprint('tutor_api', __name__, url_prefix='/api/tutor')


@tutor_api.route('/bookings', methods=['GET'])
@tutor_required
def get_bookings():
    """Get tutor's bookings with filtering and pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = Booking.query.filter_by(tutor_id=current_user.tutor_profile.id)
        
        # Filter by status
        if status:
            query = query.filter(Booking.status == status)
        
        # Filter by date range
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Booking.scheduled_time >= start_date_obj)
        
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Booking.scheduled_time <= end_date_obj)
        
        # Paginate results
        bookings = query.order_by(Booking.scheduled_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        return jsonify({
            'success': True,
            'bookings': [booking.to_dict() for booking in bookings.items],
            'pagination': {
                'page': bookings.page,
                'pages': bookings.pages,
                'per_page': bookings.per_page,
                'total': bookings.total,
                'has_next': bookings.has_next,
                'has_prev': bookings.has_prev
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tutor_api.route('/bookings/<int:booking_id>', methods=['GET'])
@tutor_required
def get_booking(booking_id):
    """Get specific booking details"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Check if booking belongs to current tutor
        if booking.tutor_id != current_user.tutor_profile.id:
            return jsonify({
                'success': False,
                'error': 'Booking not found'
            }), 404
        
        return jsonify({
            'success': True,
            'booking': booking.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tutor_api.route('/bookings/<int:booking_id>', methods=['PUT'])
@tutor_required
def update_booking(booking_id):
    """Update booking details"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Check if booking belongs to current tutor
        if booking.tutor_id != current_user.tutor_profile.id:
            return jsonify({
                'success': False,
                'error': 'Booking not found'
            }), 404
        
        # Get update data
        data = request.get_json()
        
        # Update allowed fields
        if 'status' in data:
            booking.status = data['status']
        
        if 'scheduled_time' in data:
            booking.scheduled_time = datetime.fromisoformat(data['scheduled_time'])
        
        if 'duration_minutes' in data:
            booking.duration_minutes = data['duration_minutes']
        
        if 'notes' in data:
            booking.notes = data['notes']
        
        # Save changes
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'booking': booking.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tutor_api.route('/bookings/<int:booking_id>', methods=['DELETE'])
@tutor_required
def cancel_booking(booking_id):
    """Cancel a booking"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Check if booking belongs to current tutor
        if booking.tutor_id != current_user.tutor_profile.id:
            return jsonify({
                'success': False,
                'error': 'Booking not found'
            }), 404
        
        # Update status to cancelled
        booking.status = 'Cancelled'
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Booking cancelled successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tutor_api.route('/demos', methods=['GET'])
@tutor_required
def get_demo_requests():
    """Get tutor's demo requests with filtering and pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = DemoSession.query.filter_by(tutor_id=current_user.id)
        
        # Filter by status
        if status:
            query = query.filter(DemoSession.status == status)
        
        # Filter by date range
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(DemoSession.scheduled_date_time >= start_date_obj)
        
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(DemoSession.scheduled_date_time <= end_date_obj)
        
        # Paginate results
        demos = query.order_by(DemoSession.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        return jsonify({
            'success': True,
            'demos': [demo.to_dict() for demo in demos.items],
            'pagination': {
                'page': demos.page,
                'pages': demos.pages,
                'per_page': demos.per_page,
                'total': demos.total,
                'has_next': demos.has_next,
                'has_prev': demos.has_prev
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tutor_api.route('/demos/<int:demo_id>', methods=['GET'])
@tutor_required
def get_demo_request(demo_id):
    """Get specific demo request details"""
    try:
        demo = DemoSession.query.get_or_404(demo_id)
        
        # Check if demo belongs to current tutor
        if demo.tutor_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Demo request not found'
            }), 404
        
        return jsonify({
            'success': True,
            'demo': demo.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tutor_api.route('/demos/<int:demo_id>/approve', methods=['POST'])
@tutor_required
def approve_demo_request(demo_id):
    """Approve a demo request"""
    try:
        demo = DemoSession.query.get_or_404(demo_id)
        
        # Check if demo belongs to current tutor
        if demo.tutor_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Demo request not found'
            }), 404
        
        # Get scheduling data
        data = request.get_json()
        
        # Update demo with scheduling details
        demo.status = 'Confirmed'
        
        if 'scheduled_date' in data:
            demo.scheduled_date = datetime.strptime(data['scheduled_date'], '%Y-%m-%d').date()
        
        if 'scheduled_time' in data:
            demo.scheduled_time = datetime.strptime(data['scheduled_time'], '%H:%M').time()
        
        if 'meeting_link' in data:
            demo.meeting_link = data['meeting_link']
        
        # Save changes
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Demo request approved successfully',
            'demo': demo.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tutor_api.route('/demos/<int:demo_id>/reject', methods=['POST'])
@tutor_required
def reject_demo_request(demo_id):
    """Reject a demo request"""
    try:
        demo = DemoSession.query.get_or_404(demo_id)
        
        # Check if demo belongs to current tutor
        if demo.tutor_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Demo request not found'
            }), 404
        
        # Update status to rejected
        demo.status = 'Cancelled'
        
        # Save changes
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Demo request rejected successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tutor_api.route('/availability', methods=['GET'])
@tutor_required
def get_availability():
    """Get tutor's availability"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get tutor's availability
        from app.models.booking import TutorAvailability
        
        query = TutorAvailability.query.filter_by(tutor_id=current_user.tutor_profile.id)
        
        # Filter by date range
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(TutorAvailability.date >= start_date_obj)
        
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(TutorAvailability.date <= end_date_obj)
        
        # Get availability
        availability = query.all()
        
        # Format response
        return jsonify({
            'success': True,
            'availability': [avail.to_dict() for avail in availability]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tutor_api.route('/availability', methods=['POST'])
@tutor_required
def set_availability():
    """Set tutor's availability"""
    try:
        # Get availability data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'date' not in data or 'start_time' not in data or 'end_time' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: date, start_time, end_time'
            }), 400
        
        # Create availability record
        from app.models.booking import TutorAvailability
        
        availability = TutorAvailability(
            tutor_id=current_user.tutor_profile.id,
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(data['end_time'], '%H:%M').time(),
            is_available=data.get('is_available', True)
        )
        
        # Save to database
        from app import db
        db.session.add(availability)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Availability set successfully',
            'availability': availability.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tutor_api.route('/availability/<int:availability_id>', methods=['DELETE'])
@tutor_required
def delete_availability(availability_id):
    """Delete availability record"""
    try:
        from app.models.booking import TutorAvailability
        
        availability = TutorAvailability.query.get_or_404(availability_id)
        
        # Check if availability belongs to current tutor
        if availability.tutor_id != current_user.tutor_profile.id:
            return jsonify({
                'success': False,
                'error': 'Availability not found'
            }), 404
        
        # Delete availability
        from app import db
        db.session.delete(availability)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Availability deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tutor_api.route('/calendar', methods=['GET'])
@tutor_required
def get_calendar_data():
    """Get calendar data for a specific month"""
    try:
        # Get query parameters
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        # Get start and end dates for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Get bookings for the month
        bookings = Booking.query.filter(
            and_(
                Booking.tutor_id == current_user.tutor_profile.id,
                Booking.scheduled_time >= start_date,
                Booking.scheduled_time < end_date
            )
        ).all()
        
        # Get demo requests for the month
        demos = DemoSession.query.filter(
            and_(
                DemoSession.tutor_id == current_user.id,
                DemoSession.scheduled_date_time >= start_date.date(),
                DemoSession.scheduled_date_time < end_date.date()
            )
        ).all()
        
        # Format calendar data
        calendar_data = []
        
        # Add bookings to calendar
        for booking in bookings:
            calendar_data.append({
                'id': booking.id,
                'title': f'Booking with {booking.student.user_profile.full_name if booking.student.user_profile else booking.student.email}',
                'start': booking.scheduled_time.isoformat(),
                'end': (booking.scheduled_time + timedelta(minutes=booking.duration_minutes)).isoformat(),
                'type': 'booking',
                'status': booking.status,
                'color': get_booking_color(booking.status)
            })
        
        # Add demos to calendar
        for demo in demos:
            if demo.scheduled_date and demo.scheduled_time:
                start_datetime = datetime.combine(demo.scheduled_date, demo.scheduled_time)
                calendar_data.append({
                    'id': demo.id,
                    'title': f'Demo with {demo.student.user_profile.full_name if demo.student.user_profile else demo.student.email}',
                    'start': start_datetime.isoformat(),
                    'end': (start_datetime + timedelta(minutes=demo.duration_minutes)).isoformat(),
                    'type': 'demo',
                    'status': demo.status,
                    'color': get_demo_color(demo.status)
                })
        
        return jsonify({
            'success': True,
            'calendar_data': calendar_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_booking_color(status):
    """Get color for booking status"""
    colors = {
        'Pending': '#ffc107',
        'Confirmed': '#28a745',
        'Completed': '#17a2b8',
        'Cancelled': '#dc3545'
    }
    return colors.get(status, '#667eea')


def get_demo_color(status):
    """Get color for demo status"""
    colors = {
        'Pending': '#ffc107',
        'Confirmed': '#28a745',
        'Completed': '#17a2b8',
        'Cancelled': '#dc3545'
    }
    return colors.get(status, '#667eea')