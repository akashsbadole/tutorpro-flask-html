import requests
import json
import jwt
import time
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models.meeting import Meeting, MeetingRecording


class ZoomIntegration:
    """Zoom SDK integration for meeting management"""
    
    def __init__(self):
        self.api_key = current_app.config.get('ZOOM_API_KEY')
        self.api_secret = current_app.config.get('ZOOM_API_SECRET')
        self.base_url = 'https://api.zoom.us/v2'
        self.webhook_secret = current_app.config.get('ZOOM_WEBHOOK_SECRET')
    
    def generate_jwt_token(self):
        """Generate JWT token for Zoom API authentication"""
        payload = {
            'iss': self.api_key,
            'exp': int(time.time() + 3600)  # Token expires in 1 hour
        }
        
        token = jwt.encode(
            payload,
            self.api_secret,
            algorithm='HS256'
        )
        
        return token
    
    def get_headers(self):
        """Get headers for API requests"""
        token = self.generate_jwt_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def create_meeting(self, meeting_data):
        """Create a Zoom meeting"""
        try:
            url = f'{self.base_url}/users/me/meetings'
            headers = self.get_headers()
            
            # Prepare meeting data for Zoom API
            zoom_data = {
                'topic': meeting_data.get('title', 'Meeting'),
                'type': 2,  # Scheduled meeting
                'start_time': meeting_data.get('scheduled_time').strftime('%Y-%m-%dT%H:%M:%SZ'),
                'duration': meeting_data.get('duration_minutes', 60),
                'timezone': meeting_data.get('timezone', 'UTC'),
                'agenda': meeting_data.get('description', ''),
                'settings': {
                    'host_video': meeting_data.get('enable_host_video', True),
                    'participant_video': meeting_data.get('enable_participant_video', True),
                    'cn_meeting': False,  # Disable personal meeting ID
                    'in_meeting': False,  # Disable in-meeting chat
                    'join_before_host': meeting_data.get('allow_join_before_host', False),
                    'mute_upon_entry': meeting_data.get('mute_on_entry', False),
                    'watermark': False,
                    'use_pmi': False,
                    'approval_type': 0,  # Automatically approve
                    'audio': meeting_data.get('audio_type', 'both'),  # both telephony and voip
                    'auto_recording': meeting_data.get('enable_recording', False),
                    'enforce_login': meeting_data.get('require_authentication', False),
                    'waiting_room': meeting_data.get('enable_waiting_room', True),
                    'registrants_email_notification': False,
                    'meeting_authentication': meeting_data.get('require_authentication', False),
                    'encryption_type': 'enhanced_encryption'
                }
            }
            
            # Add password if required
            if meeting_data.get('require_password'):
                zoom_data['password'] = meeting_data.get('password', '')
            
            response = requests.post(url, json=zoom_data, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Zoom API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Zoom meeting creation error: {str(e)}")
            return {'error': str(e)}
    
    def update_meeting(self, meeting_id, meeting_data):
        """Update an existing Zoom meeting"""
        try:
            url = f'{self.base_url}/meetings/{meeting_id}'
            headers = self.get_headers()
            
            # Prepare update data
            update_data = {
                'topic': meeting_data.get('title'),
                'start_time': meeting_data.get('scheduled_time').strftime('%Y-%m-%dT%H:%M:%SZ'),
                'duration': meeting_data.get('duration_minutes'),
                'timezone': meeting_data.get('timezone'),
                'agenda': meeting_data.get('description', ''),
                'settings': {
                    'host_video': meeting_data.get('enable_host_video', True),
                    'participant_video': meeting_data.get('enable_participant_video', True),
                    'waiting_room': meeting_data.get('enable_waiting_room', True),
                    'auto_recording': meeting_data.get('enable_recording', False)
                }
            }
            
            response = requests.patch(url, json=update_data, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Zoom API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Zoom meeting update error: {str(e)}")
            return {'error': str(e)}
    
    def delete_meeting(self, meeting_id):
        """Delete a Zoom meeting"""
        try:
            url = f'{self.base_url}/meetings/{meeting_id}'
            headers = self.get_headers()
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            return {'success': True}
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Zoom API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Zoom meeting deletion error: {str(e)}")
            return {'error': str(e)}
    
    def get_meeting(self, meeting_id):
        """Get meeting details"""
        try:
            url = f'{self.base_url}/meetings/{meeting_id}'
            headers = self.get_headers()
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Zoom API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Zoom meeting retrieval error: {str(e)}")
            return {'error': str(e)}
    
    def list_meetings(self, user_id='me', from_date=None, to_date=None):
        """List meetings"""
        try:
            url = f'{self.base_url}/users/{user_id}/meetings'
            headers = self.get_headers()
            
            params = {}
            if from_date:
                params['from'] = from_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            if to_date:
                params['to'] = to_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Zoom API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Zoom meeting list error: {str(e)}")
            return {'error': str(e)}
    
    def get_recordings(self, meeting_id):
        """Get meeting recordings"""
        try:
            url = f'{self.base_url}/meetings/{meeting_id}/recordings'
            headers = self.get_headers()
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Zoom API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Zoom recordings retrieval error: {str(e)}")
            return {'error': str(e)}
    
    def create_registrant(self, meeting_id, registrant_data):
        """Add a meeting registrant"""
        try:
            url = f'{self.base_url}/meetings/{meeting_id}/registrants'
            headers = self.get_headers()
            
            response = requests.post(url, json=registrant_data, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Zoom API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Zoom registrant creation error: {str(e)}")
            return {'error': str(e)}
    
    def get_meeting_participants(self, meeting_id):
        """Get meeting participants"""
        try:
            url = f'{self.base_url}/meetings/{meeting_id}/participants'
            headers = self.get_headers()
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Zoom API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Zoom participants retrieval error: {str(e)}")
            return {'error': str(e)}
    
    def verify_webhook(self, request):
        """Verify Zoom webhook signature"""
        signature = request.headers.get('x-zm-signature')
        timestamp = request.headers.get('x-zm-request-timestamp')
        token = request.headers.get('x-zm-signature-token')
        
        if not all([signature, timestamp, token]):
            return False
        
        # Create message to verify
        message = f"v0:{timestamp}:{token}"
        
        # Generate expected signature
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def process_webhook_event(self, event_data):
        """Process Zoom webhook events"""
        event = event_data.get('event')
        payload = event_data.get('payload', {})
        meeting_object = payload.get('object', {})
        
        if event == 'meeting.started':
            meeting_id = meeting_object.get('id')
            meeting = Meeting.query.filter_by(meeting_id=meeting_id).first()
            if meeting:
                meeting.start_meeting()
                db.session.commit()
                
        elif event == 'meeting.ended':
            meeting_id = meeting_object.get('id')
            meeting = Meeting.query.filter_by(meeting_id=meeting_id).first()
            if meeting:
                meeting.end_meeting()
                db.session.commit()
                
        elif event == 'recording.completed':
            meeting_id = meeting_object.get('id')
            meeting = Meeting.query.filter_by(meeting_id=meeting_id).first()
            if meeting:
                recording_files = meeting_object.get('recording_files', [])
                
                for file_info in recording_files:
                    if file_info.get('file_type') == 'MP4':
                        recording = MeetingRecording(
                            meeting_id=meeting.id,
                            recording_url=file_info.get('download_url'),
                            recording_id=meeting_id,
                            file_name=file_info.get('file_name'),
                            file_size=file_info.get('file_size'),
                            duration_minutes=int(file_info.get('play_url', '').split('start=')[1]) if 'start=' in file_info.get('play_url', '') else 0,
                            file_format='MP4',
                            status='Ready'
                        )
                        db.session.add(recording)
                
                db.session.commit()
        
        return {'status': 'processed'}


# Helper functions for meeting integration
def create_zoom_meeting(meeting):
    """Create a Zoom meeting from a Meeting object"""
    zoom = ZoomIntegration()
    
    meeting_data = {
        'title': meeting.title,
        'description': meeting.description,
        'scheduled_time': meeting.scheduled_time,
        'duration_minutes': meeting.duration_minutes,
        'timezone': meeting.timezone,
        'enable_recording': meeting.enable_recording,
        'enable_waiting_room': meeting.enable_waiting_room,
        'enable_participant_video': meeting.enable_participant_video,
        'require_authentication': meeting.enable_authentication,
        'require_password': meeting.require_password,
        'password': meeting.password
    }
    
    result = zoom.create_meeting(meeting_data)
    
    if 'error' in result:
        return {'success': False, 'error': result['error']}
    
    # Update meeting with Zoom details
    meeting.meeting_id = result.get('id')
    meeting.meeting_url = result.get('join_url')
    
    db.session.commit()
    
    return {'success': True, 'meeting': result}


def update_zoom_meeting(meeting):
    """Update a Zoom meeting"""
    zoom = ZoomIntegration()
    
    meeting_data = {
        'title': meeting.title,
        'description': meeting.description,
        'scheduled_time': meeting.scheduled_time,
        'duration_minutes': meeting.duration_minutes,
        'timezone': meeting.timezone,
        'enable_recording': meeting.enable_recording,
        'enable_waiting_room': meeting.enable_waiting_room,
        'enable_participant_video': meeting.enable_participant_video,
        'require_authentication': meeting.enable_authentication,
        'require_password': meeting.require_password,
        'password': meeting.password
    }
    
    result = zoom.update_meeting(meeting.meeting_id, meeting_data)
    
    if 'error' in result:
        return {'success': False, 'error': result['error']}
    
    return {'success': True, 'meeting': result}


def delete_zoom_meeting(meeting):
    """Delete a Zoom meeting"""
    zoom = ZoomIntegration()
    
    result = zoom.delete_meeting(meeting.meeting_id)
    
    if 'error' in result:
        return {'success': False, 'error': result['error']}
    
    return {'success': True}


def get_zoom_recordings(meeting):
    """Get Zoom meeting recordings"""
    zoom = ZoomIntegration()
    
    result = zoom.get_recordings(meeting.meeting_id)
    
    if 'error' in result:
        return {'success': False, 'error': result['error']}
    
    return {'success': True, 'recordings': result.get('recording_files', [])}