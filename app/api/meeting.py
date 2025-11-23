from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.meeting import (Meeting, MeetingParticipant, MeetingRecording, MeetingTemplate,
                               MeetingCalendar, MeetingReminder, MeetingAnalytics)
from app.models.demo import DemoSession, DemoFeedback, DemoTemplate, DemoAvailability
# DemoRequestFeedback model doesn't exist, removed import
from app.models.user import User
from app.models.tutor import TutorProfile
from app import db
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import secrets
import json


meeting_api = Blueprint('meeting_api', __name__, url_prefix='/api/meeting')


def require_api_key(f):
    """Decorator to require API key"""
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config.get('API_KEY'):
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated_function


@meeting_api.route('/meetings', methods=['GET'])
@login_required
def get_meetings():
    """Get meetings with filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    meeting_type = request.args.get('type')
    platform = request.args.get('platform')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Meeting.query
    
    # Filter by user role
    if current_user.is_tutor():
        tutor_profile = current_user.tutor_profile
        if tutor_profile:
            query = query.filter_by(host_id=current_user.id, host_type='Tutor')
    elif current_user.is_admin():
        query = query.filter_by(host_type='Admin')
    else:
        # Students can see meetings they're participating in
        query = query.join(MeetingParticipant).filter_by(user_id=current_user.id)
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    
    if meeting_type:
        query = query.filter_by(meeting_type=meeting_type)
    
    if platform:
        query = query.filter_by(platform=platform)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Meeting.scheduled_time >= date_from)
        except ValueError:
            return jsonify({'error': 'Invalid date_from format'}), 400
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Meeting.scheduled_time <= date_to)
        except ValueError:
            return jsonify({'error': 'Invalid date_to format'}), 400
    
    # Paginate
    meetings = query.order_by(Meeting.scheduled_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'meetings': [meeting.to_dict() for meeting in meetings.items],
        'pagination': {
            'page': meetings.page,
            'pages': meetings.pages,
            'per_page': meetings.per_page,
            'total': meetings.total,
            'has_next': meetings.has_next,
            'has_prev': meetings.has_prev
        }
    })


@meeting_api.route('/meetings/<int:id>', methods=['GET'])
@login_required
def get_meeting(id):
    """Get specific meeting details"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_view_meeting(meeting):
        return jsonify({'error': 'Permission denied'}), 403
    
    return jsonify(meeting.to_dict())


@meeting_api.route('/meetings', methods=['POST'])
@login_required
def create_meeting():
    """Create a new meeting"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['title', 'scheduled_time', 'duration_minutes', 'platform']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        meeting = Meeting(
            title=data['title'],
            description=data.get('description', ''),
            meeting_type=data.get('meeting_type', 'Regular'),
            scheduled_time=datetime.fromisoformat(data['scheduled_time']),
            duration_minutes=data['duration_minutes'],
            timezone=data.get('timezone', 'UTC'),
            host_id=current_user.id,
            host_type='Tutor' if current_user.is_tutor() else 'Admin',
            platform=data['platform'],
            meeting_url=data.get('meeting_url'),
            meeting_id=data.get('meeting_id'),
            password=data.get('password'),
            max_participants=data.get('max_participants', 100),
            enable_recording=data.get('enable_recording', False),
            enable_waiting_room=data.get('enable_waiting_room', True),
            enable_participant_video=data.get('enable_participant_video', True),
            enable_participant_audio=data.get('enable_participant_audio', True),
            enable_chat=data.get('enable_chat', True),
            enable_screen_share=data.get('enable_screen_share', True),
            require_password=data.get('require_password', False),
            enable_authentication=data.get('enable_authentication', True),
            one_time_link=data.get('one_time_link', False),
            link_expires_at=datetime.fromisoformat(data['link_expires_at']) if data.get('link_expires_at') else None
        )
        
        # Generate secure password if required but not provided
        if data.get('require_password') and not data.get('password'):
            meeting.generate_secure_password()
        
        # Generate host key
        meeting.generate_host_key()
        
        db.session.add(meeting)
        db.session.commit()
        
        # Add host as participant
        meeting.add_participant(current_user.id, 'Host')
        
        # Create analytics record
        analytics = MeetingAnalytics(meeting_id=meeting.id)
        db.session.add(analytics)
        db.session.commit()
        
        return jsonify(meeting.to_dict()), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@meeting_api.route('/meetings/<int:id>', methods=['PUT'])
@login_required
def update_meeting(id):
    """Update meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Update allowed fields
        updatable_fields = [
            'title', 'description', 'meeting_type', 'scheduled_time',
            'duration_minutes', 'timezone', 'platform', 'meeting_url',
            'meeting_id', 'password', 'max_participants', 'enable_recording',
            'enable_waiting_room', 'enable_participant_video', 'enable_participant_audio',
            'enable_chat', 'enable_screen_share', 'require_password',
            'enable_authentication', 'one_time_link', 'link_expires_at'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field in ['scheduled_time', 'link_expires_at'] and data[field]:
                    setattr(meeting, field, datetime.fromisoformat(data[field]))
                else:
                    setattr(meeting, field, data[field])
        
        db.session.commit()
        return jsonify(meeting.to_dict())
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@meeting_api.route('/meetings/<int:id>', methods=['DELETE'])
@login_required
def delete_meeting(id):
    """Delete meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        return jsonify({'error': 'Permission denied'}), 403
    
    db.session.delete(meeting)
    db.session.commit()
    
    return jsonify({'message': 'Meeting deleted successfully'})


@meeting_api.route('/meetings/<int:id>/join', methods=['POST'])
@login_required
def join_meeting(id):
    """Join meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check if user can join
    if not _can_join_meeting(meeting):
        return jsonify({'error': 'Cannot join this meeting'}), 403
    
    # Check if meeting is expired
    if meeting.is_expired:
        return jsonify({'error': 'Meeting link has expired'}), 403
    
    # Add participant if not already added
    participant = MeetingParticipant.query.filter_by(
        meeting_id=id, user_id=current_user.id
    ).first()
    
    if not participant:
        participant = meeting.add_participant(current_user.id, 'Participant')
        participant.joined_at = datetime.utcnow()
        participant.status = 'Joined'
        db.session.commit()
    elif participant.status == 'Invited':
        participant.joined_at = datetime.utcnow()
        participant.status = 'Joined'
        db.session.commit()
    
    return jsonify({
        'meeting_url': meeting.meeting_url,
        'password': meeting.password,
        'meeting_id': meeting.meeting_id
    })


@meeting_api.route('/meetings/<int:id>/start', methods=['POST'])
@login_required
def start_meeting(id):
    """Start meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        return jsonify({'error': 'Permission denied'}), 403
    
    meeting.start_meeting()
    
    return jsonify({'message': 'Meeting started', 'status': meeting.status})


@meeting_api.route('/meetings/<int:id>/end', methods=['POST'])
@login_required
def end_meeting(id):
    """End meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        return jsonify({'error': 'Permission denied'}), 403
    
    meeting.end_meeting()
    
    return jsonify({'message': 'Meeting ended', 'status': meeting.status})


@meeting_api.route('/meetings/<int:id>/participants', methods=['GET'])
@login_required
def get_participants(id):
    """Get meeting participants"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_view_meeting(meeting):
        return jsonify({'error': 'Permission denied'}), 403
    
    participants = MeetingParticipant.query.filter_by(meeting_id=id).all()
    
    return jsonify([participant.to_dict() for participant in participants])


@meeting_api.route('/meetings/<int:id>/participants', methods=['POST'])
@login_required
def add_participant(id):
    """Add participant to meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    if not data or 'user_id' not in data:
        return jsonify({'error': 'user_id is required'}), 400
    
    # Check if user exists
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user is already a participant
    existing = MeetingParticipant.query.filter_by(
        meeting_id=id, user_id=data['user_id']
    ).first()
    
    if existing:
        return jsonify({'error': 'User is already a participant'}), 400
    
    participant = meeting.add_participant(
        data['user_id'], data.get('role', 'Participant')
    )
    participant.can_share_screen = data.get('can_share_screen', False)
    participant.can_record = data.get('can_record', False)
    participant.can_mute_participants = data.get('can_mute_participants', False)
    
    db.session.commit()
    
    return jsonify(participant.to_dict()), 201


@meeting_api.route('/meetings/<int:id>/participants/<int:participant_id>', methods=['DELETE'])
@login_required
def remove_participant(id, participant_id):
    """Remove participant from meeting"""
    meeting = Meeting.query.get_or_404(id)
    participant = MeetingParticipant.query.get_or_404(participant_id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        return jsonify({'error': 'Permission denied'}), 403
    
    if participant.meeting_id != meeting.id:
        return jsonify({'error': 'Participant not found in this meeting'}), 404
    
    db.session.delete(participant)
    db.session.commit()
    
    return jsonify({'message': 'Participant removed successfully'})


@meeting_api.route('/meetings/<int:id>/recordings', methods=['GET'])
@login_required
def get_recordings(id):
    """Get meeting recordings"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_view_meeting(meeting):
        return jsonify({'error': 'Permission denied'}), 403
    
    recordings = MeetingRecording.query.filter_by(meeting_id=id).all()
    
    return jsonify([recording.to_dict() for recording in recordings])


@meeting_api.route('/recordings/<int:id>', methods=['PUT'])
@login_required
def update_recording(id):
    """Update recording settings"""
    recording = MeetingRecording.query.get_or_404(id)
    meeting = Meeting.query.get(recording.meeting_id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Update allowed fields
        updatable_fields = [
            'file_name', 'password', 'download_enabled', 'share_enabled', 'expires_at'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'expires_at' and data[field]:
                    setattr(recording, field, datetime.fromisoformat(data[field]))
                else:
                    setattr(recording, field, data[field])
        
        db.session.commit()
        return jsonify(recording.to_dict())
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@meeting_api.route('/templates', methods=['GET'])
@login_required
def get_templates():
    """Get meeting templates"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    query = MeetingTemplate.query
    
    # Show user's templates and public templates
    query = query.filter(
        or_(MeetingTemplate.created_by == current_user.id,
             MeetingTemplate.is_public == True)
    )
    
    templates = query.order_by(MeetingTemplate.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'templates': [template.to_dict() for template in templates.items],
        'pagination': {
            'page': templates.page,
            'pages': templates.pages,
            'per_page': templates.per_page,
            'total': templates.total,
            'has_next': templates.has_next,
            'has_prev': templates.has_prev
        }
    })


@meeting_api.route('/templates', methods=['POST'])
@login_required
def create_template():
    """Create meeting template"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    if 'name' not in data:
        return jsonify({'error': 'Template name is required'}), 400
    
    try:
        template = MeetingTemplate(
            name=data['name'],
            description=data.get('description', ''),
            meeting_type=data.get('meeting_type', 'Regular'),
            platform=data.get('platform', 'Zoom'),
            default_duration=data.get('default_duration', 60),
            enable_recording=data.get('enable_recording', False),
            enable_waiting_room=data.get('enable_waiting_room', True),
            enable_participant_video=data.get('enable_participant_video', True),
            enable_participant_audio=data.get('enable_participant_audio', True),
            enable_chat=data.get('enable_chat', True),
            enable_screen_share=data.get('enable_screen_share', True),
            require_password=data.get('require_password', False),
            enable_authentication=data.get('enable_authentication', True),
            created_by=current_user.id,
            is_public=data.get('is_public', False)
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify(template.to_dict()), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@meeting_api.route('/webhooks/zoom', methods=['POST'], endpoint='zoom_webhook')
@require_api_key
def zoom_webhook():
    """Handle Zoom webhooks"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    event = data.get('event')
    payload = data.get('payload', {})
    
    if event == 'meeting.started':
        meeting_id = payload.get('object', {}).get('id')
        meeting = Meeting.query.filter_by(meeting_id=meeting_id).first()
        
        if meeting:
            meeting.start_meeting()
    
    elif event == 'meeting.ended':
        meeting_id = payload.get('object', {}).get('id')
        meeting = Meeting.query.filter_by(meeting_id=meeting_id).first()
        
        if meeting:
            meeting.end_meeting()
    
    elif event == 'recording.completed':
        meeting_id = payload.get('object', {}).get('id')
        recording_files = payload.get('object', {}).get('recording_files', [])
        
        meeting = Meeting.query.filter_by(meeting_id=meeting_id).first()
        if meeting:
            for file_info in recording_files:
                if file_info.get('file_type') == 'MP4':
                    recording = MeetingRecording(
                        meeting_id=meeting.id,
                        recording_url=file_info.get('download_url'),
                        file_name=file_info.get('file_name'),
                        file_size=file_info.get('file_size'),
                        duration_minutes=file_info.get('play_url', '').split('start=')[1] if 'start=' in file_info.get('play_url', '') else 0,
                        status='Ready'
                    )
                    db.session.add(recording)
            
            db.session.commit()
    
    return jsonify({'message': 'Webhook processed successfully'})


@meeting_api.route('/webhooks/google-meet', methods=['POST'], endpoint='google_meet_webhook')
@require_api_key
def google_meet_webhook():
    """Handle Google Meet webhooks"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Process Google Meet webhook events
    # Implementation depends on Google Meet webhook structure
    
    return jsonify({'message': 'Webhook processed successfully'})


# Helper functions
def _can_view_meeting(meeting):
    """Check if current user can view meeting"""
    if current_user.is_admin():
        return True
    
    if meeting.host_id == current_user.id:
        return True
    
    # Check if user is a participant
    participant = MeetingParticipant.query.filter_by(
        meeting_id=meeting.id, user_id=current_user.id
    ).first()
    
    return participant is not None


def _can_edit_meeting(meeting):
    """Check if current user can edit meeting"""
    if current_user.is_admin():
        return True
    
    return meeting.host_id == current_user.id


def _can_join_meeting(meeting):
    """Check if current user can join meeting"""
    if meeting.status not in ['Scheduled', 'Ongoing']:
        return False
    
    if meeting.host_id == current_user.id:
        return True
    
    # Check if user is a participant
    participant = MeetingParticipant.query.filter_by(
        meeting_id=meeting.id, user_id=current_user.id
    ).first()
    
    return participant is not None


# Add to_dict methods to models for JSON serialization
def add_to_dict_methods():
    """Add to_dict methods to models for API responses"""
    
    def meeting_to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'meeting_type': self.meeting_type,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'duration_minutes': self.duration_minutes,
            'timezone': self.timezone,
            'status': self.status,
            'host_id': self.host_id,
            'host_type': self.host_type,
            'platform': self.platform,
            'meeting_url': self.meeting_url,
            'meeting_id': self.meeting_id,
            'password': self.password,
            'max_participants': self.max_participants,
            'enable_recording': self.enable_recording,
            'enable_waiting_room': self.enable_waiting_room,
            'enable_participant_video': self.enable_participant_video,
            'enable_participant_audio': self.enable_participant_audio,
            'enable_chat': self.enable_chat,
            'enable_screen_share': self.enable_screen_share,
            'require_password': self.require_password,
            'enable_authentication': self.enable_authentication,
            'one_time_link': self.one_time_link,
            'link_expires_at': self.link_expires_at.isoformat() if self.link_expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def participant_to_dict(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'user_id': self.user_id,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'left_at': self.left_at.isoformat() if self.left_at else None,
            'duration_minutes': self.duration_minutes,
            'can_share_screen': self.can_share_screen,
            'can_record': self.can_record,
            'can_mute_participants': self.can_mute_participants,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def recording_to_dict(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'recording_url': self.recording_url,
            'recording_id': self.recording_id,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'duration_minutes': self.duration_minutes,
            'file_format': self.file_format,
            'password': self.password,
            'download_enabled': self.download_enabled,
            'share_enabled': self.share_enabled,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'status': self.status,
            'thumbnail_url': self.thumbnail_url,
            'transcript_url': self.transcript_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def template_to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'meeting_type': self.meeting_type,
            'platform': self.platform,
            'default_duration': self.default_duration,
            'enable_recording': self.enable_recording,
            'enable_waiting_room': self.enable_waiting_room,
            'enable_participant_video': self.enable_participant_video,
            'enable_participant_audio': self.enable_participant_audio,
            'enable_chat': self.enable_chat,
            'enable_screen_share': self.enable_screen_share,
            'require_password': self.require_password,
            'enable_authentication': self.enable_authentication,
            'created_by': self.created_by,
            'is_public': self.is_public,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    # Add methods to models
    Meeting.to_dict = meeting_to_dict
    MeetingParticipant.to_dict = participant_to_dict
    MeetingRecording.to_dict = recording_to_dict
    MeetingTemplate.to_dict = template_to_dict


# Initialize to_dict methods
add_to_dict_methods()