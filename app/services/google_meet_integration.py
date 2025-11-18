import requests
import json
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models.meeting import Meeting, MeetingRecording


class GoogleMeetIntegration:
    """Google Meet integration for meeting management"""
    
    def __init__(self):
        self.client_id = current_app.config.get('GOOGLE_CLIENT_ID')
        self.client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI')
        self.scope = 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/meetings'
        self.base_url = 'https://meet.googleapis.com/v2'
        self.calendar_base_url = 'https://www.googleapis.com/calendar/v3'
    
    def get_auth_url(self):
        """Get Google OAuth authorization URL"""
        auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_url}?{query_string}"
    
    def exchange_code_for_tokens(self, code):
        """Exchange authorization code for access tokens"""
        token_url = 'https://oauth2.googleapis.com/token'
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Google OAuth error: {str(e)}")
            return {'error': str(e)}
    
    def refresh_access_token(self, refresh_token):
        """Refresh access token using refresh token"""
        token_url = 'https://oauth2.googleapis.com/token'
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Google token refresh error: {str(e)}")
            return {'error': str(e)}
    
    def create_meeting(self, meeting_data, access_token):
        """Create a Google Meet meeting"""
        try:
            # First create a calendar event with Google Meet conference
            calendar_url = f'{self.calendar_base_url}/calendars/primary/events'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            event_data = {
                'summary': meeting_data.get('title', 'Meeting'),
                'description': meeting_data.get('description', ''),
                'start': {
                    'dateTime': meeting_data.get('scheduled_time').isoformat(),
                    'timeZone': meeting_data.get('timezone', 'UTC')
                },
                'end': {
                    'dateTime': (meeting_data.get('scheduled_time') + timedelta(minutes=meeting_data.get('duration_minutes', 60))).isoformat(),
                    'timeZone': meeting_data.get('timezone', 'UTC')
                },
                'conferenceData': {
                    'createRequest': {
                        'conferenceSolutionKey': 'hangoutsMeet'
                    }
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 15},
                        {'method': 'popup', 'minutes': 10}
                    ]
                }
            }
            
            response = requests.post(calendar_url, json=event_data, headers=headers)
            response.raise_for_status()
            
            event = response.json()
            
            # Extract Google Meet details
            conference_data = event.get('conferenceData', {})
            conference_solution = conference_data.get('conferenceSolution', {})
            entry_points = conference_solution.get('entryPoints', [])
            
            meet_url = None
            meeting_id = None
            
            for entry_point in entry_points:
                if entry_point.get('entryPointType') == 'video':
                    meet_url = entry_point.get('uri')
                elif entry_point.get('entryPointType') == 'phone':
                    meeting_id = entry_point.get('label')
            
            return {
                'id': event.get('id'),
                'meet_url': meet_url,
                'meeting_id': meeting_id,
                'event': event
            }
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Google Meet API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Google Meet creation error: {str(e)}")
            return {'error': str(e)}
    
    def update_meeting(self, event_id, meeting_data, access_token):
        """Update an existing Google Meet meeting"""
        try:
            url = f'{self.calendar_base_url}/calendars/primary/events/{event_id}'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            event_data = {
                'summary': meeting_data.get('title'),
                'description': meeting_data.get('description', ''),
                'start': {
                    'dateTime': meeting_data.get('scheduled_time').isoformat(),
                    'timeZone': meeting_data.get('timezone', 'UTC')
                },
                'end': {
                    'dateTime': (meeting_data.get('scheduled_time') + timedelta(minutes=meeting_data.get('duration_minutes', 60))).isoformat(),
                    'timeZone': meeting_data.get('timezone', 'UTC')
                }
            }
            
            response = requests.patch(url, json=event_data, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Google Meet API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Google Meet update error: {str(e)}")
            return {'error': str(e)}
    
    def delete_meeting(self, event_id, access_token):
        """Delete a Google Meet meeting"""
        try:
            url = f'{self.calendar_base_url}/calendars/primary/events/{event_id}'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            return {'success': True}
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Google Meet API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Google Meet deletion error: {str(e)}")
            return {'error': str(e)}
    
    def get_meeting(self, event_id, access_token):
        """Get meeting details"""
        try:
            url = f'{self.calendar_base_url}/calendars/primary/events/{event_id}'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Google Meet API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Google Meet retrieval error: {str(e)}")
            return {'error': str(e)}
    
    def list_meetings(self, access_token, from_date=None, to_date=None):
        """List Google Meet meetings"""
        try:
            url = f'{self.calendar_base_url}/calendars/primary/events'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {}
            if from_date:
                params['timeMin'] = from_date.isoformat()
            if to_date:
                params['timeMax'] = to_date.isoformat()
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Google Meet API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Google Meet list error: {str(e)}")
            return {'error': str(e)}
    
    def create_space(self, space_name, access_token):
        """Create a Google Meet space"""
        try:
            url = f'{self.base_url}/spaces'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            space_data = {
                'displayName': space_name,
                'spaceType': 'MEET_SPACE'
            }
            
            response = requests.post(url, json=space_data, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Google Meet API error: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            current_app.logger.error(f"Google Meet space creation error: {str(e)}")
            return {'error': str(e)}
    
    def generate_meeting_link(self, space_name):
        """Generate a Google Meet link for a space"""
        # Generate a random meeting code
        import random
        import string
        
        meeting_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        meet_link = f'https://meet.google.com/{meeting_code}'
        
        return {
            'meeting_code': meeting_code,
            'meet_link': meet_link,
            'space_name': space_name
        }


# Helper functions for Google Meet integration
def create_google_meet_meeting(meeting):
    """Create a Google Meet meeting from a Meeting object"""
    # Get user's Google tokens (this would be stored in the database)
    # For now, we'll use a placeholder access token
    access_token = get_user_google_token(meeting.host_id)
    
    if not access_token:
        return {'success': False, 'error': 'Google account not connected'}
    
    google_meet = GoogleMeetIntegration()
    
    meeting_data = {
        'title': meeting.title,
        'description': meeting.description,
        'scheduled_time': meeting.scheduled_time,
        'duration_minutes': meeting.duration_minutes,
        'timezone': meeting.timezone
    }
    
    result = google_meet.create_meeting(meeting_data, access_token)
    
    if 'error' in result:
        return {'success': False, 'error': result['error']}
    
    # Update meeting with Google Meet details
    meeting.meeting_url = result.get('meet_url')
    meeting.meeting_id = result.get('meeting_id')
    
    db.session.commit()
    
    return {'success': True, 'meeting': result}


def update_google_meet_meeting(meeting):
    """Update a Google Meet meeting"""
    access_token = get_user_google_token(meeting.host_id)
    
    if not access_token:
        return {'success': False, 'error': 'Google account not connected'}
    
    google_meet = GoogleMeetIntegration()
    
    meeting_data = {
        'title': meeting.title,
        'description': meeting.description,
        'scheduled_time': meeting.scheduled_time,
        'duration_minutes': meeting.duration_minutes,
        'timezone': meeting.timezone
    }
    
    result = google_meet.update_meeting(meeting.google_event_id, meeting_data, access_token)
    
    if 'error' in result:
        return {'success': False, 'error': result['error']}
    
    return {'success': True, 'meeting': result}


def delete_google_meet_meeting(meeting):
    """Delete a Google Meet meeting"""
    access_token = get_user_google_token(meeting.host_id)
    
    if not access_token:
        return {'success': False, 'error': 'Google account not connected'}
    
    google_meet = GoogleMeetIntegration()
    
    result = google_meet.delete_meeting(meeting.google_event_id, access_token)
    
    if 'error' in result:
        return {'success': False, 'error': result['error']}
    
    return {'success': True}


def get_user_google_token(user_id):
    """Get user's Google access token from database"""
    # This would typically be stored in a user integrations table
    # For now, return None as placeholder
    from app.models.meeting import MeetingCalendar
    calendar = MeetingCalendar.query.filter_by(user_id=user_id, calendar_type='Google').first()
    
    if calendar and calendar.access_token:
        return calendar.access_token
    
    return None


def generate_google_meet_link():
    """Generate a simple Google Meet link"""
    import random
    import string
    
    meeting_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    meet_link = f'https://meet.google.com/{meeting_code}'
    
    return {
        'meeting_code': meeting_code,
        'meet_link': meet_link
    }