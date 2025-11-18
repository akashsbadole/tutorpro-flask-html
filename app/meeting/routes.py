from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.meeting import bp
from app.meeting.forms import (MeetingForm, MeetingTemplateForm, MeetingParticipantForm, 
                             MeetingReminderForm, MeetingCalendarForm, MeetingRecordingForm,
                             MeetingLinkForm, MeetingSearchForm, MeetingFeedbackForm, MeetingRescheduleForm)
from app.models.meeting import (Meeting, MeetingParticipant, MeetingRecording, MeetingTemplate,
                               MeetingCalendar, MeetingReminder, MeetingAnalytics)
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.course import Course
from app.utils.decorators import tutor_required, admin_required
from app import db
from sqlalchemy import func, desc, or_
from datetime import datetime, timedelta
import secrets
import json


@bp.route('/')
@login_required
def index():
    """Meeting dashboard"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
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
    
    # Filter by status
    if status:
        query = query.filter_by(status=status)
    
    meetings = query.order_by(Meeting.scheduled_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('meeting/index.html', meetings=meetings, status=status)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new meeting"""
    form = MeetingForm()
    
    # Populate choices
    if current_user.is_tutor():
        form.host_id.data = current_user.id
        form.host_type.data = 'Tutor'
    elif current_user.is_admin():
        form.host_type.data = 'Admin'
    
    if form.validate_on_submit():
        meeting = Meeting(
            title=form.title.data,
            description=form.description.data,
            meeting_type=form.meeting_type.data,
            scheduled_time=form.scheduled_time.data,
            duration_minutes=form.duration_minutes.data,
            timezone=form.timezone.data,
            host_id=current_user.id,
            host_type=form.host_type.data,
            platform=form.platform.data,
            meeting_url=form.meeting_url.data,
            meeting_id=form.meeting_id.data,
            password=form.password.data,
            max_participants=form.max_participants.data,
            enable_recording=form.enable_recording.data,
            enable_waiting_room=form.enable_waiting_room.data,
            enable_participant_video=form.enable_participant_video.data,
            enable_participant_audio=form.enable_participant_audio.data,
            enable_chat=form.enable_chat.data,
            enable_screen_share=form.enable_screen_share.data,
            require_password=form.require_password.data,
            enable_authentication=form.enable_authentication.data,
            one_time_link=form.one_time_link.data,
            link_expires_at=form.link_expires_at.data
        )
        
        # Generate secure password if required but not provided
        if form.require_password.data and not form.password.data:
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
        
        flash('Meeting created successfully!', 'success')
        return redirect(url_for('meeting.details', id=meeting.id))
    
    return render_template('meeting/create.html', form=form)


@bp.route('/<int:id>')
@login_required
def details(id):
    """View meeting details"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_view_meeting(meeting):
        flash('You do not have permission to view this meeting', 'danger')
        return redirect(url_for('meeting.index'))
    
    # Get participants
    participants = MeetingParticipant.query.filter_by(meeting_id=id).all()
    
    # Get recordings
    recordings = MeetingRecording.query.filter_by(meeting_id=id).all()
    
    # Get reminders
    reminders = MeetingReminder.query.filter_by(meeting_id=id).all()
    
    # Get analytics
    analytics = MeetingAnalytics.query.filter_by(meeting_id=id).first()
    
    return render_template('meeting/details.html', 
                        meeting=meeting, 
                        participants=participants,
                        recordings=recordings,
                        reminders=reminders,
                        analytics=analytics)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        flash('You do not have permission to edit this meeting', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
    form = MeetingForm(obj=meeting)
    
    if form.validate_on_submit():
        # Update meeting details
        meeting.title = form.title.data
        meeting.description = form.description.data
        meeting.meeting_type = form.meeting_type.data
        meeting.scheduled_time = form.scheduled_time.data
        meeting.duration_minutes = form.duration_minutes.data
        meeting.timezone = form.timezone.data
        meeting.platform = form.platform.data
        meeting.meeting_url = form.meeting_url.data
        meeting.meeting_id = form.meeting_id.data
        meeting.password = form.password.data
        meeting.max_participants = form.max_participants.data
        meeting.enable_recording = form.enable_recording.data
        meeting.enable_waiting_room = form.enable_waiting_room.data
        meeting.enable_participant_video = form.enable_participant_video.data
        meeting.enable_participant_audio = form.enable_participant_audio.data
        meeting.enable_chat = form.enable_chat.data
        meeting.enable_screen_share = form.enable_screen_share.data
        meeting.require_password = form.require_password.data
        meeting.enable_authentication = form.enable_authentication.data
        meeting.one_time_link = form.one_time_link.data
        meeting.link_expires_at = form.link_expires_at.data
        
        db.session.commit()
        
        flash('Meeting updated successfully!', 'success')
        return redirect(url_for('meeting.details', id=meeting.id))
    
    return render_template('meeting/edit.html', form=form, meeting=meeting)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        flash('You do not have permission to delete this meeting', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
    db.session.delete(meeting)
    db.session.commit()
    
    flash('Meeting deleted successfully!', 'success')
    return redirect(url_for('meeting.index'))


@bp.route('/<int:id>/start', methods=['POST'])
@login_required
def start(id):
    """Start meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        flash('You do not have permission to start this meeting', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
    meeting.start_meeting()
    
    flash('Meeting started!', 'success')
    return redirect(url_for('meeting.details', id=id))


@bp.route('/<int:id>/end', methods=['POST'])
@login_required
def end(id):
    """End meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        flash('You do not have permission to end this meeting', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
    meeting.end_meeting()
    
    flash('Meeting ended!', 'success')
    return redirect(url_for('meeting.details', id=id))


@bp.route('/<int:id>/join')
@login_required
def join(id):
    """Join meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check if user can join
    if not _can_join_meeting(meeting):
        flash('You cannot join this meeting', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
    # Check if meeting is expired
    if meeting.is_expired:
        flash('This meeting link has expired', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
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
    
    # Redirect to meeting URL
    if meeting.meeting_url:
        return redirect(meeting.meeting_url)
    else:
        flash('Meeting URL not available', 'warning')
        return redirect(url_for('meeting.details', id=id))


@bp.route('/<int:id>/participants/add', methods=['GET', 'POST'])
@login_required
def add_participant(id):
    """Add participant to meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        flash('You do not have permission to add participants', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
    form = MeetingParticipantForm()
    
    # Populate user choices
    users = User.query.filter(User.id != current_user.id).all()
    form.user_id.choices = [(u.id, u.email) for u in users]
    
    if form.validate_on_submit():
        # Check if user is already a participant
        existing = MeetingParticipant.query.filter_by(
            meeting_id=id, user_id=form.user_id.data
        ).first()
        
        if existing:
            flash('User is already a participant', 'warning')
        else:
            participant = meeting.add_participant(
                form.user_id.data, form.role.data
            )
            participant.can_share_screen = form.can_share_screen.data
            participant.can_record = form.can_record.data
            participant.can_mute_participants = form.can_mute_participants.data
            
            db.session.commit()
            
            flash('Participant added successfully!', 'success')
            return redirect(url_for('meeting.details', id=id))
    
    return render_template('meeting/add_participant.html', form=form, meeting=meeting)


@bp.route('/<int:id>/participants/<int:participant_id>/remove', methods=['POST'])
@login_required
def remove_participant(id, participant_id):
    """Remove participant from meeting"""
    meeting = Meeting.query.get_or_404(id)
    participant = MeetingParticipant.query.get_or_404(participant_id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        flash('You do not have permission to remove participants', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
    if participant.meeting_id != meeting.id:
        flash('Participant not found in this meeting', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
    db.session.delete(participant)
    db.session.commit()
    
    flash('Participant removed successfully!', 'success')
    return redirect(url_for('meeting.details', id=id))


@bp.route('/<int:id>/reminders/add', methods=['GET', 'POST'])
@login_required
def add_reminder(id):
    """Add reminder for meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_view_meeting(meeting):
        flash('You do not have permission to add reminders', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
    form = MeetingReminderForm()
    
    if form.validate_on_submit():
        reminder = MeetingReminder(
            meeting_id=id,
            user_id=current_user.id,
            reminder_type=form.reminder_type.data,
            reminder_time=form.reminder_time.data
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        flash('Reminder added successfully!', 'success')
        return redirect(url_for('meeting.details', id=id))
    
    return render_template('meeting/add_reminder.html', form=form, meeting=meeting)


@bp.route('/templates')
@login_required
def templates():
    """Meeting templates"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = MeetingTemplate.query
    
    # Show user's templates and public templates
    query = query.filter(
        or_(MeetingTemplate.created_by == current_user.id,
             MeetingTemplate.is_public == True)
    )
    
    templates = query.order_by(MeetingTemplate.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('meeting/templates.html', templates=templates)


@bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
def create_template():
    """Create meeting template"""
    form = MeetingTemplateForm()
    
    if form.validate_on_submit():
        template = MeetingTemplate(
            name=form.name.data,
            description=form.description.data,
            meeting_type=form.meeting_type.data,
            platform=form.platform.data,
            default_duration=form.default_duration.data,
            enable_recording=form.enable_recording.data,
            enable_waiting_room=form.enable_waiting_room.data,
            enable_participant_video=form.enable_participant_video.data,
            enable_participant_audio=form.enable_participant_audio.data,
            enable_chat=form.enable_chat.data,
            enable_screen_share=form.enable_screen_share.data,
            require_password=form.require_password.data,
            enable_authentication=form.enable_authentication.data,
            created_by=current_user.id,
            is_public=form.is_public.data
        )
        
        db.session.add(template)
        db.session.commit()
        
        flash('Template created successfully!', 'success')
        return redirect(url_for('meeting.templates'))
    
    return render_template('meeting/create_template.html', form=form)


@bp.route('/templates/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(id):
    """Edit meeting template"""
    template = MeetingTemplate.query.get_or_404(id)
    
    # Check permissions
    if template.created_by != current_user.id and not current_user.is_admin():
        flash('You do not have permission to edit this template', 'danger')
        return redirect(url_for('meeting.templates'))
    
    form = MeetingTemplateForm(obj=template)
    
    if form.validate_on_submit():
        template.name = form.name.data
        template.description = form.description.data
        template.meeting_type = form.meeting_type.data
        template.platform = form.platform.data
        template.default_duration = form.default_duration.data
        template.enable_recording = form.enable_recording.data
        template.enable_waiting_room = form.enable_waiting_room.data
        template.enable_participant_video = form.enable_participant_video.data
        template.enable_participant_audio = form.enable_participant_audio.data
        template.enable_chat = form.enable_chat.data
        template.enable_screen_share = form.enable_screen_share.data
        template.require_password = form.require_password.data
        template.enable_authentication = form.enable_authentication.data
        template.is_public = form.is_public.data
        
        db.session.commit()
        
        flash('Template updated successfully!', 'success')
        return redirect(url_for('meeting.templates'))
    
    return render_template('meeting/edit_template.html', form=form, template=template)


@bp.route('/calendar')
@login_required
def calendar():
    """Meeting calendar view"""
    # Get meetings for current month
    start_date = request.args.get('start', datetime.utcnow().replace(day=1).strftime('%Y-%m-%d'))
    end_date = request.args.get('end', (datetime.utcnow().replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d'))
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    query = Meeting.query.filter(
        Meeting.scheduled_time >= start_date,
        Meeting.scheduled_time <= end_date
    )
    
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
    
    meetings = query.order_by(Meeting.scheduled_time.asc()).all()
    
    return render_template('meeting/calendar.html', meetings=meetings)


@bp.route('/search')
@login_required
def search():
    """Search meetings"""
    form = MeetingSearchForm()
    meetings = []
    
    if request.args.get('query'):
        form = MeetingSearchForm(request.args)
        
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
        if form.query.data:
            query = query.filter(
                or_(Meeting.title.contains(form.query.data),
                     Meeting.description.contains(form.query.data))
            )
        
        if form.status.data:
            query = query.filter_by(status=form.status.data)
        
        if form.meeting_type.data:
            query = query.filter_by(meeting_type=form.meeting_type.data)
        
        if form.platform.data:
            query = query.filter_by(platform=form.platform.data)
        
        if form.date_from.data:
            query = query.filter(Meeting.scheduled_time >= form.date_from.data)
        
        if form.date_to.data:
            query = query.filter(Meeting.scheduled_time <= form.date_to.data)
        
        meetings = query.order_by(Meeting.scheduled_time.desc()).limit(50).all()
    
    return render_template('meeting/search.html', form=form, meetings=meetings)


@bp.route('/<int:id>/reschedule', methods=['GET', 'POST'])
@login_required
def reschedule(id):
    """Reschedule meeting"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_meeting(meeting):
        flash('You do not have permission to reschedule this meeting', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
    form = MeetingRescheduleForm()
    
    if form.validate_on_submit():
        old_time = meeting.scheduled_time
        old_duration = meeting.duration_minutes
        
        meeting.scheduled_time = form.new_scheduled_time.data
        meeting.duration_minutes = form.new_duration_minutes.data
        
        db.session.commit()
        
        # Notify participants if requested
        if form.notify_participants.data:
            _notify_reschedule(meeting, old_time, old_duration, form.reason.data)
        
        flash('Meeting rescheduled successfully!', 'success')
        return redirect(url_for('meeting.details', id=id))
    
    return render_template('meeting/reschedule.html', form=form, meeting=meeting)


@bp.route('/<int:id>/feedback', methods=['GET', 'POST'])
@login_required
def feedback(id):
    """Submit meeting feedback"""
    meeting = Meeting.query.get_or_404(id)
    
    # Check if user can provide feedback
    if not _can_provide_feedback(meeting):
        flash('You cannot provide feedback for this meeting', 'danger')
        return redirect(url_for('meeting.details', id=id))
    
    form = MeetingFeedbackForm()
    
    if form.validate_on_submit():
        # Update analytics with feedback
        analytics = MeetingAnalytics.query.filter_by(meeting_id=id).first()
        if analytics:
            analytics.overall_rating = form.overall_rating.data
            analytics.audio_quality_rating = form.audio_quality.data
            analytics.video_quality_rating = form.video_quality.data
        
        db.session.commit()
        
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('meeting.details', id=id))
    
    return render_template('meeting/feedback.html', form=form, meeting=meeting)


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


def _can_provide_feedback(meeting):
    """Check if current user can provide feedback"""
    if meeting.status != 'Completed':
        return False
    
    if meeting.host_id == current_user.id:
        return True
    
    # Check if user was a participant
    participant = MeetingParticipant.query.filter_by(
        meeting_id=meeting.id, user_id=current_user.id
    ).first()
    
    return participant is not None


def _notify_reschedule(meeting, old_time, old_duration, reason):
    """Notify participants about reschedule"""
    participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id).all()
    
    for participant in participants:
        if participant.user.email:
            # Send email notification (implementation depends on email service)
            pass