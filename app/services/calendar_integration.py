import requests
import json
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models.meeting import Meeting, MeetingCalendar


class CalendarIntegration:
    """Calendar integration for meeting synchronization"""
    
    def __init__(self):
        self.google_client_id = current_app.config.get('GOOGLE_CLIENT_ID')
        self.google_client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
        self.microsoft_client_id = current_app.config.get('MICROSOFT_CLIENT_ID')
        self.microsoft_client_secret = current_app.config.get('MICROSOFT_CLIENT_SECRET')
        self.redirect_uri = current_app.config.get('CALENDAR_REDIRECT_URI')
    
    def sync_meeting_to_calendar(self, meeting, calendar):
        """Sync a meeting to external calendar"""
        try:
            if calendar.calendar_type == 'Google':
                return self._sync_to_google_calendar(meeting, calendar)
            elif calendar.calendar_type == 'Outlook':
                return self._sync_to_outlook_calendar(meeting, calendar)
            elif calendar.calendar_type == 'Apple':
                return self._sync_to_apple_calendar(meeting, calendar)
            else:
                return {'success': False, 'error': 'Unsupported calendar type'}
                
        except Exception as e:
            current_app.logger.error(f"Calendar sync error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_to_google_calendar(self, meeting, calendar):
        """Sync meeting to Google Calendar"""
        try:
            url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
            headers = {
                'Authorization': f'Bearer {calendar.access_token}',
                'Content-Type': 'application/json'
            }
            
            event_data = {
                'summary': meeting.title,
                'description': meeting.description,
                'start': {
                    'dateTime': meeting.scheduled_time.isoformat(),
                    'timeZone': meeting.timezone
                },
                'end': {
                    'dateTime': (meeting.scheduled_time + timedelta(minutes=meeting.duration_minutes)).isoformat(),
                    'timeZone': meeting.timezone
                },
                'location': meeting.meeting_url if meeting.meeting_url else 'Online Meeting',
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 15},
                        {'method': 'popup', 'minutes': 10}
                    ]
                }
            }
            
            # Add conference data if meeting URL exists
            if meeting.meeting_url:
                event_data['conferenceData'] = {
                    'createRequest': {
                        'conferenceSolutionKey': 'hangoutsMeet'
                    }
                }
            
            response = requests.post(url, json=event_data, headers=headers)
            response.raise_for_status()
            
            return {'success': True, 'event_id': response.json().get('id')}
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Google Calendar sync error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_to_outlook_calendar(self, meeting, calendar):
        """Sync meeting to Outlook Calendar"""
        try:
            url = 'https://graph.microsoft.com/v1.0/me/events'
            headers = {
                'Authorization': f'Bearer {calendar.access_token}',
                'Content-Type': 'application/json'
            }
            
            event_data = {
                'subject': meeting.title,
                'body': {
                    'contentType': 'HTML',
                    'content': meeting.description
                },
                'start': {
                    'dateTime': meeting.scheduled_time.isoformat(),
                    'timeZone': meeting.timezone
                },
                'end': {
                    'dateTime': (meeting.scheduled_time + timedelta(minutes=meeting.duration_minutes)).isoformat(),
                    'timeZone': meeting.timezone
                },
                'location': {
                    'displayName': meeting.meeting_url if meeting.meeting_url else 'Online Meeting'
                },
                'isOnlineMeeting': True if meeting.meeting_url else False,
                'onlineMeetingProvider': 'TeamsForBusiness' if 'teams' in meeting.meeting_url.lower() else None
            }
            
            # Add online meeting details
            if meeting.meeting_url:
                event_data['onlineMeeting'] = {
                    'joinUrl': meeting.meeting_url,
                    'conferenceId': meeting.meeting_id
                }
            
            response = requests.post(url, json=event_data, headers=headers)
            response.raise_for_status()
            
            return {'success': True, 'event_id': response.json().get('id')}
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Outlook Calendar sync error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_to_apple_calendar(self, meeting, calendar):
        """Sync meeting to Apple Calendar (CalDAV)"""
        # Apple Calendar integration would require CalDAV protocol
        # This is a simplified implementation
        try:
            # Create iCal format event
            ical_data = self._create_ical_event(meeting)
            
            # Upload to CalDAV server (implementation depends on server)
            # For now, return success
            return {'success': True, 'ical_data': ical_data}
            
        except Exception as e:
            current_app.logger.error(f"Apple Calendar sync error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_ical_event(self, meeting):
        """Create iCal format event for Apple Calendar"""
        start_time = meeting.scheduled_time.strftime('%Y%m%dT%H%M%SZ')
        end_time = (meeting.scheduled_time + timedelta(minutes=meeting.duration_minutes)).strftime('%Y%m%dT%H%M%SZ')
        
        ical = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//TutorPro//Meeting//EN
BEGIN:VEVENT
UID:{meeting.id}@tutorpro.com
DTSTART:{start_time}
DTEND:{end_time}
SUMMARY:{meeting.title}
DESCRIPTION:{meeting.description or ''}
LOCATION:{meeting.meeting_url or 'Online Meeting'}
STATUS:CONFIRMED
BEGIN:VALARM
TRIGGER:-PT15M
ACTION:DISPLAY
DESCRIPTION:Meeting reminder
END:VALARM
END:VEVENT
END:VCALENDAR"""
        
        return ical
    
    def import_calendar_events(self, calendar, from_date=None, to_date=None):
        """Import events from external calendar"""
        try:
            if calendar.calendar_type == 'Google':
                return self._import_google_events(calendar, from_date, to_date)
            elif calendar.calendar_type == 'Outlook':
                return self._import_outlook_events(calendar, from_date, to_date)
            elif calendar.calendar_type == 'Apple':
                return self._import_apple_events(calendar, from_date, to_date)
            else:
                return {'success': False, 'error': 'Unsupported calendar type'}
                
        except Exception as e:
            current_app.logger.error(f"Calendar import error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _import_google_events(self, calendar, from_date, to_date):
        """Import events from Google Calendar"""
        try:
            url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
            headers = {
                'Authorization': f'Bearer {calendar.access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {}
            if from_date:
                params['timeMin'] = from_date.isoformat()
            if to_date:
                params['timeMax'] = to_date.isoformat()
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return {'success': True, 'events': response.json().get('items', [])}
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Google Calendar import error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _import_outlook_events(self, calendar, from_date, to_date):
        """Import events from Outlook Calendar"""
        try:
            url = 'https://graph.microsoft.com/v1.0/me/events'
            headers = {
                'Authorization': f'Bearer {calendar.access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {}
            if from_date:
                params['$filter'] = f"start/dateTime ge '{from_date.isoformat()}'"
            if to_date:
                params['$filter'] += f" and end/dateTime le '{to_date.isoformat()}'"
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return {'success': True, 'events': response.json().get('value', [])}
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Outlook Calendar import error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _import_apple_events(self, calendar, from_date, to_date):
        """Import events from Apple Calendar (CalDAV)"""
        # Apple Calendar import would require CalDAV protocol
        # This is a simplified implementation
        try:
            # For now, return empty events
            return {'success': True, 'events': []}
            
        except Exception as e:
            current_app.logger.error(f"Apple Calendar import error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def delete_calendar_event(self, calendar, event_id):
        """Delete event from external calendar"""
        try:
            if calendar.calendar_type == 'Google':
                return self._delete_google_event(calendar, event_id)
            elif calendar.calendar_type == 'Outlook':
                return self._delete_outlook_event(calendar, event_id)
            elif calendar.calendar_type == 'Apple':
                return self._delete_apple_event(calendar, event_id)
            else:
                return {'success': False, 'error': 'Unsupported calendar type'}
                
        except Exception as e:
            current_app.logger.error(f"Calendar delete error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _delete_google_event(self, calendar, event_id):
        """Delete event from Google Calendar"""
        try:
            url = f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}'
            headers = {
                'Authorization': f'Bearer {calendar.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            return {'success': True}
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Google Calendar delete error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _delete_outlook_event(self, calendar, event_id):
        """Delete event from Outlook Calendar"""
        try:
            url = f'https://graph.microsoft.com/v1.0/me/events/{event_id}'
            headers = {
                'Authorization': f'Bearer {calendar.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            return {'success': True}
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Outlook Calendar delete error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _delete_apple_event(self, calendar, event_id):
        """Delete event from Apple Calendar (CalDAV)"""
        # Apple Calendar deletion would require CalDAV protocol
        # This is a simplified implementation
        try:
            return {'success': True}
            
        except Exception as e:
            current_app.logger.error(f"Apple Calendar delete error: {str(e)}")
            return {'success': False, 'error': str(e)}


# Helper functions for calendar integration
def sync_meeting_to_calendars(meeting):
    """Sync meeting to all connected calendars"""
    calendars = MeetingCalendar.query.filter_by(
        user_id=meeting.host_id,
        sync_enabled=True
    ).all()
    
    results = []
    for calendar in calendars:
        if calendar.sync_direction in ['Export', 'Bidirectional']:
            calendar_integration = CalendarIntegration()
            result = calendar_integration.sync_meeting_to_calendar(meeting, calendar)
            results.append({
                'calendar_id': calendar.id,
                'calendar_type': calendar.calendar_type,
                'result': result
            })
    
    return results


def import_calendar_events_to_meetings(user_id):
    """Import events from all connected calendars and create meetings"""
    calendars = MeetingCalendar.query.filter_by(
        user_id=user_id,
        sync_enabled=True
    ).all()
    
    results = []
    for calendar in calendars:
        if calendar.sync_direction in ['Import', 'Bidirectional']:
            calendar_integration = CalendarIntegration()
            result = calendar_integration.import_calendar_events(calendar)
            results.append({
                'calendar_id': calendar.id,
                'calendar_type': calendar.calendar_type,
                'result': result
            })
    
    return results


def get_calendar_auth_url(calendar_type):
    """Get authorization URL for calendar type"""
    calendar_integration = CalendarIntegration()
    
    if calendar_type == 'Google':
        return calendar_integration.get_google_auth_url()
    elif calendar_type == 'Outlook':
        return calendar_integration.get_outlook_auth_url()
    elif calendar_type == 'Apple':
        return calendar_integration.get_apple_auth_url()
    else:
        return None


def get_outlook_auth_url():
    """Get Microsoft OAuth authorization URL for Outlook"""
    client_id = current_app.config.get('MICROSOFT_CLIENT_ID')
    redirect_uri = current_app.config.get('CALENDAR_REDIRECT_URI')
    
    auth_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
    scope = 'https://graph.microsoft.com/calendars.readwrite'
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'response_type': 'code',
        'response_mode': 'query'
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    return f"{auth_url}?{query_string}"