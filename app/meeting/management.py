from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.meeting import bp
from app.meeting.forms import MeetingCalendarForm, MeetingRecordingForm
from app.models.meeting import (Meeting, MeetingParticipant, MeetingRecording, MeetingCalendar,
                               MeetingReminder, MeetingAnalytics)
from app.models.user import User
from app.utils.decorators import admin_required
from app import db
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import requests
import json


@bp.route('/management')
@login_required
@admin_required
def management():
    """Meeting management dashboard for admins"""
    # Get statistics
    total_meetings = Meeting.query.count()
    upcoming_meetings = Meeting.query.filter(
        Meeting.scheduled_time > datetime.utcnow(),
        Meeting.status.in_(['Scheduled', 'Ongoing'])
    ).count()
    
    completed_meetings = Meeting.query.filter_by(status='Completed').count()
    cancelled_meetings = Meeting.query.filter_by(status='Cancelled').count()
    
    # Get platform usage
    platform_stats = db.session.query(
        Meeting.platform, func.count(Meeting.id)
    ).group_by(Meeting.platform).all()
    
    # Get recent meetings
    recent_meetings = Meeting.query.order_by(Meeting.created_at.desc()).limit(10).all()
    
    # Get meetings needing attention
    attention_meetings = Meeting.query.filter(
        or_(
            Meeting.scheduled_time < datetime.utcnow() - timedelta(hours=1),
            Meeting.status == 'No-Show'
        )
    ).limit(5).all()
    
    return render_template('meeting/management/dashboard.html',
                        total_meetings=total_meetings,
                        upcoming_meetings=upcoming_meetings,
                        completed_meetings=completed_meetings,
                        cancelled_meetings=cancelled_meetings,
                        platform_stats=platform_stats,
                        recent_meetings=recent_meetings,
                        attention_meetings=attention_meetings)


@bp.route('/management/calendar')
@login_required
@admin_required
def calendar_management():
    """Calendar integration management"""
    calendars = MeetingCalendar.query.all()
    
    return render_template('meeting/management/calendar.html', calendars=calendars)


@bp.route('/management/calendar/connect', methods=['GET', 'POST'])
@login_required
@admin_required
def connect_calendar():
    """Connect calendar integration"""
    form = MeetingCalendarForm()
    
    if form.validate_on_submit():
        calendar = MeetingCalendar(
            user_id=current_user.id,
            calendar_type=form.calendar_type.data,
            calendar_name=form.calendar_name.data,
            sync_enabled=form.sync_enabled.data,
            sync_direction=form.sync_direction.data
        )
        
        db.session.add(calendar)
        db.session.commit()
        
        # Initiate OAuth flow based on calendar type
        if form.calendar_type.data == 'Google':
            return redirect(url_for('meeting.google_oauth'))
        elif form.calendar_type.data == 'Outlook':
            return redirect(url_for('meeting.outlook_oauth'))
        
        flash('Calendar connected successfully!', 'success')
        return redirect(url_for('meeting.calendar_management'))
    
    return render_template('meeting/management/connect_calendar.html', form=form)


@bp.route('/management/calendar/<int:id>/sync', methods=['POST'])
@login_required
@admin_required
def sync_calendar(id):
    """Sync calendar"""
    calendar = MeetingCalendar.query.get_or_404(id)
    
    try:
        # Implement calendar sync logic based on type
        if calendar.calendar_type == 'Google':
            _sync_google_calendar(calendar)
        elif calendar.calendar_type == 'Outlook':
            _sync_outlook_calendar(calendar)
        
        calendar.last_sync_at = datetime.utcnow()
        db.session.commit()
        
        flash('Calendar synced successfully!', 'success')
    except Exception as e:
        flash(f'Calendar sync failed: {str(e)}', 'danger')
    
    return redirect(url_for('meeting.calendar_management'))


@bp.route('/management/recordings')
@login_required
@admin_required
def recordings_management():
    """Meeting recordings management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
    query = MeetingRecording.query
    
    if status:
        query = query.filter_by(status=status)
    
    recordings = query.order_by(MeetingRecording.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('meeting/management/recordings.html', recordings=recordings, status=status)


@bp.route('/management/recordings/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_recording(id):
    """Edit recording settings"""
    recording = MeetingRecording.query.get_or_404(id)
    form = MeetingRecordingForm(obj=recording)
    
    if form.validate_on_submit():
        recording.file_name = form.file_name.data
        recording.file_format = form.file_format.data
        recording.password = form.password.data
        recording.download_enabled = form.download_enabled.data
        recording.share_enabled = form.share_enabled.data
        recording.expires_at = form.expires_at.data
        
        db.session.commit()
        
        flash('Recording settings updated!', 'success')
        return redirect(url_for('meeting.recordings_management'))
    
    return render_template('meeting/management/edit_recording.html', form=form, recording=recording)


@bp.route('/management/recordings/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_recording(id):
    """Delete recording"""
    recording = MeetingRecording.query.get_or_404(id)
    
    # Delete from cloud storage if applicable
    if recording.recording_url:
        try:
            # Implement cloud storage deletion
            pass
        except Exception as e:
            current_app.logger.error(f"Failed to delete recording from storage: {str(e)}")
    
    db.session.delete(recording)
    db.session.commit()
    
    flash('Recording deleted successfully!', 'success')
    return redirect(url_for('meeting.recordings_management'))


@bp.route('/management/analytics')
@login_required
@admin_required
def analytics():
    """Meeting analytics dashboard"""
    # Get date range from request
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Meeting statistics
    total_meetings = Meeting.query.filter(
        Meeting.scheduled_time >= start_date
    ).count()
    
    completed_meetings = Meeting.query.filter(
        Meeting.scheduled_time >= start_date,
        Meeting.status == 'Completed'
    ).count()
    
    cancelled_meetings = Meeting.query.filter(
        Meeting.scheduled_time >= start_date,
        Meeting.status == 'Cancelled'
    ).count()
    
    # Average duration
    avg_duration = db.session.query(
        func.avg(Meeting.duration_minutes)
    ).filter(
        Meeting.scheduled_time >= start_date,
        Meeting.status == 'Completed'
    ).scalar() or 0
    
    # Platform usage
    platform_usage = db.session.query(
        Meeting.platform, func.count(Meeting.id)
    ).filter(
        Meeting.scheduled_time >= start_date
    ).group_by(Meeting.platform).all()
    
    # Meeting types
    meeting_types = db.session.query(
        Meeting.meeting_type, func.count(Meeting.id)
    ).filter(
        Meeting.scheduled_time >= start_date
    ).group_by(Meeting.meeting_type).all()
    
    # Daily meeting counts
    daily_meetings = db.session.query(
        func.date(Meeting.scheduled_time).label('date'),
        func.count(Meeting.id).label('count')
    ).filter(
        Meeting.scheduled_time >= start_date
    ).group_by(func.date(Meeting.scheduled_time)).all()
    
    # Top hosts
    top_hosts = db.session.query(
        User.email, func.count(Meeting.id).label('meeting_count')
    ).join(
        Meeting, User.id == Meeting.host_id
    ).filter(
        Meeting.scheduled_time >= start_date
    ).group_by(User.id).order_by(desc('meeting_count')).limit(10).all()
    
    return render_template('meeting/management/analytics.html',
                        total_meetings=total_meetings,
                        completed_meetings=completed_meetings,
                        cancelled_meetings=cancelled_meetings,
                        avg_duration=avg_duration,
                        platform_usage=platform_usage,
                        meeting_types=meeting_types,
                        daily_meetings=daily_meetings,
                        top_hosts=top_hosts,
                        days=days)


@bp.route('/management/reminders')
@login_required
@admin_required
def reminders_management():
    """Meeting reminders management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get upcoming reminders
    reminders = MeetingReminder.query.filter(
        MeetingReminder.is_sent == False,
        MeetingReminder.reminder_time <= 1440  # Within 24 hours
    ).join(Meeting).filter(
        Meeting.scheduled_time > datetime.utcnow()
    ).order_by(MeetingReminder.reminder_time.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('meeting/management/reminders.html', reminders=reminders)


@bp.route('/management/reminders/<int:id>/send', methods=['POST'])
@login_required
@admin_required
def send_reminder(id):
    """Send meeting reminder"""
    reminder = MeetingReminder.query.get_or_404(id)
    
    try:
        # Send reminder based on type
        if reminder.reminder_type == 'Email':
            _send_email_reminder(reminder)
        elif reminder.reminder_type == 'SMS':
            _send_sms_reminder(reminder)
        elif reminder.reminder_type == 'Push':
            _send_push_reminder(reminder)
        
        reminder.is_sent = True
        reminder.sent_at = datetime.utcnow()
        db.session.commit()
        
        flash('Reminder sent successfully!', 'success')
    except Exception as e:
        flash(f'Failed to send reminder: {str(e)}', 'danger')
    
    return redirect(url_for('meeting.reminders_management'))


@bp.route('/management/security')
@login_required
@admin_required
def security_management():
    """Meeting security management"""
    # Get meetings with security issues
    meetings_without_password = Meeting.query.filter(
        Meeting.require_password == True,
        or_(Meeting.password.is_(None), Meeting.password == '')
    ).all()
    
    expired_links = Meeting.query.filter(
        Meeting.link_expires_at < datetime.utcnow(),
        Meeting.link_expires_at.isnot(None)
    ).all()
    
    meetings_without_auth = Meeting.query.filter(
        Meeting.enable_authentication == False
    ).all()
    
    return render_template('meeting/management/security.html',
                        meetings_without_password=meetings_without_password,
                        expired_links=expired_links,
                        meetings_without_auth=meetings_without_auth)


@bp.route('/management/bulk-operations', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_operations():
    """Bulk meeting operations"""
    if request.method == 'POST':
        operation = request.form.get('operation')
        meeting_ids = request.form.getlist('meeting_ids')
        
        if not meeting_ids:
            flash('Please select at least one meeting', 'warning')
            return redirect(url_for('meeting.bulk_operations'))
        
        meetings = Meeting.query.filter(Meeting.id.in_(meeting_ids)).all()
        
        if operation == 'cancel':
            for meeting in meetings:
                meeting.status = 'Cancelled'
            flash(f'{len(meetings)} meetings cancelled', 'success')
        
        elif operation == 'reschedule':
            # Redirect to reschedule page with selected meetings
            session['selected_meetings'] = meeting_ids
            return redirect(url_for('meeting.bulk_reschedule'))
        
        elif operation == 'send_reminders':
            for meeting in meetings:
                # Create reminders for each meeting
                reminder = MeetingReminder(
                    meeting_id=meeting.id,
                    user_id=current_user.id,
                    reminder_type='Email',
                    reminder_time=60  # 1 hour before
                )
                db.session.add(reminder)
            flash(f'Reminders created for {len(meetings)} meetings', 'success')
        
        db.session.commit()
        return redirect(url_for('meeting.bulk_operations'))
    
    # Get meetings for selection
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    meetings = Meeting.query.order_by(Meeting.scheduled_time.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('meeting/management/bulk_operations.html', meetings=meetings)


@bp.route('/management/integrations')
@login_required
@admin_required
def integrations():
    """Meeting platform integrations"""
    integrations = {
        'zoom': {
            'name': 'Zoom',
            'connected': _check_zoom_integration(),
            'features': ['Meeting Creation', 'Recording', 'Webhooks']
        },
        'google_meet': {
            'name': 'Google Meet',
            'connected': _check_google_meet_integration(),
            'features': ['Meeting Creation', 'Calendar Sync']
        },
        'teams': {
            'name': 'Microsoft Teams',
            'connected': _check_teams_integration(),
            'features': ['Meeting Creation', 'Recording']
        }
    }
    
    return render_template('meeting/management/integrations.html', integrations=integrations)


# Helper functions for calendar integration
def _sync_google_calendar(calendar):
    """Sync Google Calendar"""
    # Implement Google Calendar API sync
    pass


def _sync_outlook_calendar(calendar):
    """Sync Outlook Calendar"""
    # Implement Outlook Calendar API sync
    pass


# Helper functions for reminders
def _send_email_reminder(reminder):
    """Send email reminder"""
    # Implement email sending
    pass


def _send_sms_reminder(reminder):
    """Send SMS reminder"""
    # Implement SMS sending
    pass


def _send_push_reminder(reminder):
    """Send push notification"""
    # Implement push notification
    pass


# Helper functions for integrations
def _check_zoom_integration():
    """Check if Zoom is integrated"""
    # Check Zoom API credentials
    return False


def _check_google_meet_integration():
    """Check if Google Meet is integrated"""
    # Check Google API credentials
    return False


def _check_teams_integration():
    """Check if Microsoft Teams is integrated"""
    # Check Microsoft API credentials
    return False