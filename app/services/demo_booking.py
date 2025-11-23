"""
Demo Booking Service for TutorPro Marketplace
Comprehensive demo session booking and management
"""

from flask import current_app, url_for
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import joinedload, contains_eager
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import json
import uuid

from app import db
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.category import Subject
from app.models.demo import (
    DemoSession, DemoAvailability, DemoTemplate, DemoFeedback, DemoAnalytics,
    DemoSessionStatus, DemoSessionType
)
from app.models.booking import Booking
from app.utils.email import send_email
from app.utils.notifications import create_notification

class DemoBookingService:
    """Service for managing demo session bookings"""
    
    def __init__(self):
        self.default_demo_duration = 30  # minutes
        self.max_demos_per_tutor_per_day = 5
        self.min_hours_notice = 2
        self.max_days_ahead = 14
    
    def request_demo_session(self, student_id: int, tutor_id: int, subject_id: int, 
                           requested_datetime: datetime, session_data: Dict) -> Tuple[bool, str, Optional[DemoSession]]:
        """
        Request a demo session
        
        Args:
            student_id: Student user ID
            tutor_id: Tutor user ID
            subject_id: Subject ID
            requested_datetime: Requested session time
            session_data: Additional session data
            
        Returns:
            Tuple of (success, message, demo_session)
        """
        try:
            # Validate inputs
            validation_result = self._validate_demo_request(
                student_id, tutor_id, subject_id, requested_datetime
            )
            if not validation_result[0]:
                return validation_result
            
            # Check tutor availability
            availability_check = self._check_tutor_availability(tutor_id, requested_datetime)
            if not availability_check[0]:
                return False, availability_check[1], None
            
            # Create demo session
            demo_session = DemoSession(
                student_id=student_id,
                tutor_id=tutor_id,
                subject_id=subject_id,
                session_title=session_data.get('session_title', f'Demo Session for {Subject.query.get(subject_id).name}'),
                session_description=session_data.get('session_description', ''),
                session_type=DemoSessionType(session_data.get('session_type', 'One-on-One')),
                duration_minutes=session_data.get('duration_minutes', self.default_demo_duration),
                requested_date_time=requested_datetime,
                timezone=session_data.get('timezone', 'UTC'),
                location_type=session_data.get('location_type', 'online'),
                topics_to_cover=session_data.get('topics_to_cover', []),
                learning_objectives=session_data.get('learning_objectives', ''),
                materials_needed=session_data.get('materials_needed', []),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=48)  # 48 hours to accept
            )
            
            db.session.add(demo_session)
            db.session.commit()
            
            # Send notifications
            self._send_demo_request_notifications(demo_session)
            
            # Update analytics
            self._update_demo_analytics(tutor_id, 'demo_requested')
            
            return True, "Demo session requested successfully", demo_session
            
        except Exception as e:
            current_app.logger.error(f"Error requesting demo session: {str(e)}")
            db.session.rollback()
            return False, f"Error requesting demo session: {str(e)}", None
    
    def accept_demo_session(self, demo_session_id: int, tutor_id: int, 
                          scheduled_datetime: datetime, meeting_data: Dict) -> Tuple[bool, str]:
        """
        Accept a demo session request
        
        Args:
            demo_session_id: Demo session ID
            tutor_id: Tutor user ID accepting
            scheduled_datetime: Scheduled session time
            meeting_data: Meeting details (link, password, etc.)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get demo session
            demo_session = DemoSession.query.filter_by(id=demo_session_id, tutor_id=tutor_id).first()
            if not demo_session:
                return False, "Demo session not found"
            
            # Validate status
            if demo_session.status != DemoSessionStatus.REQUESTED:
                return False, f"Cannot accept demo in {demo_session.status.value} status"
            
            # Check if expired
            if demo_session.expires_at and demo_session.expires_at < datetime.now(timezone.utc):
                return False, "Demo request has expired"
            
            # Validate scheduled time
            if not self._validate_scheduled_time(scheduled_datetime):
                return False, "Invalid scheduled time"
            
            # Update demo session
            demo_session.scheduled_date_time = scheduled_datetime
            demo_session.status = DemoSessionStatus.ACCEPTED
            demo_session.meeting_link = meeting_data.get('meeting_link')
            demo_session.meeting_password = meeting_data.get('meeting_password')
            demo_session.physical_address = meeting_data.get('physical_address')
            demo_session.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            # Send notifications
            self._send_demo_acceptance_notifications(demo_session)
            
            # Update analytics
            self._update_demo_analytics(tutor_id, 'demo_accepted')
            
            return True, "Demo session accepted successfully"
            
        except Exception as e:
            current_app.logger.error(f"Error accepting demo session: {str(e)}")
            db.session.rollback()
            return False, f"Error accepting demo session: {str(e)}"
    
    def confirm_demo_session(self, demo_session_id: int, student_id: int) -> Tuple[bool, str]:
        """
        Confirm a demo session (student confirmation)
        
        Args:
            demo_session_id: Demo session ID
            student_id: Student user ID confirming
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get demo session
            demo_session = DemoSession.query.filter_by(id=demo_session_id, student_id=student_id).first()
            if not demo_session:
                return False, "Demo session not found"
            
            # Validate status
            if demo_session.status != DemoSessionStatus.ACCEPTED:
                return False, f"Cannot confirm demo in {demo_session.status.value} status"
            
            # Update status
            demo_session.status = DemoSessionStatus.SCHEDULED
            demo_session.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            # Send notifications
            self._send_demo_confirmation_notifications(demo_session)
            
            # Schedule reminders
            self._schedule_demo_reminders(demo_session)
            
            # Update analytics
            self._update_demo_analytics(demo_session.tutor_id, 'demo_scheduled')
            
            return True, "Demo session confirmed successfully"
            
        except Exception as e:
            current_app.logger.error(f"Error confirming demo session: {str(e)}")
            db.session.rollback()
            return False, f"Error confirming demo session: {str(e)}"
    
    def complete_demo_session(self, demo_session_id: int, user_id: int, 
                            completion_data: Dict) -> Tuple[bool, str]:
        """
        Complete a demo session
        
        Args:
            demo_session_id: Demo session ID
            user_id: User ID completing (tutor or student)
            completion_data: Completion details
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get demo session
            demo_session = DemoSession.query.filter_by(id=demo_session_id).first()
            if not demo_session:
                return False, "Demo session not found"
            
            # Validate user is tutor or student
            if user_id not in [demo_session.tutor_id, demo_session.student_id]:
                return False, "Unauthorized to complete this demo session"
            
            # Validate status
            if demo_session.status not in [DemoSessionStatus.SCHEDULED, DemoSessionStatus.IN_PROGRESS]:
                return False, f"Cannot complete demo in {demo_session.status.value} status"
            
            # Update session
            demo_session.status = DemoSessionStatus.COMPLETED
            demo_session.tutor_feedback = completion_data.get('tutor_feedback')
            demo_session.student_feedback = completion_data.get('student_feedback')
            demo_session.conversion_potential = completion_data.get('conversion_potential', 'unknown')
            demo_session.follow_up_actions = completion_data.get('follow_up_actions', [])
            demo_session.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            # Send completion notifications
            self._send_demo_completion_notifications(demo_session)
            
            # Request feedback
            self._request_demo_feedback(demo_session)
            
            # Update analytics
            self._update_demo_analytics(demo_session.tutor_id, 'demo_completed')
            
            return True, "Demo session completed successfully"
            
        except Exception as e:
            current_app.logger.error(f"Error completing demo session: {str(e)}")
            db.session.rollback()
            return False, f"Error completing demo session: {str(e)}"
    
    def cancel_demo_session(self, demo_session_id: int, user_id: int, 
                          cancellation_reason: str, initiated_by: str) -> Tuple[bool, str]:
        """
        Cancel a demo session
        
        Args:
            demo_session_id: Demo session ID
            user_id: User ID cancelling
            cancellation_reason: Reason for cancellation
            initiated_by: Who initiated cancellation (student, tutor, system)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get demo session
            demo_session = DemoSession.query.filter_by(id=demo_session_id).first()
            if not demo_session:
                return False, "Demo session not found"
            
            # Validate user is tutor or student
            if user_id not in [demo_session.tutor_id, demo_session.student_id]:
                return False, "Unauthorized to cancel this demo session"
            
            # Validate status
            if demo_session.status in [DemoSessionStatus.COMPLETED, DemoSessionStatus.CANCELLED]:
                return False, f"Cannot cancel demo in {demo_session.status.value} status"
            
            # Update session
            demo_session.status = DemoSessionStatus.CANCELLED
            demo_session.cancellation_reason = cancellation_reason
            demo_session.cancellation_initiated_by = initiated_by
            demo_session.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            # Send cancellation notifications
            self._send_demo_cancellation_notifications(demo_session)
            
            # Update analytics
            self._update_demo_analytics(demo_session.tutor_id, 'demo_cancelled')
            
            return True, "Demo session cancelled successfully"
            
        except Exception as e:
            current_app.logger.error(f"Error cancelling demo session: {str(e)}")
            db.session.rollback()
            return False, f"Error cancelling demo session: {str(e)}"
    
    def reschedule_demo_session(self, demo_session_id: int, user_id: int, 
                               new_datetime: datetime, reason: str) -> Tuple[bool, str]:
        """
        Reschedule a demo session
        
        Args:
            demo_session_id: Demo session ID
            user_id: User ID requesting reschedule
            new_datetime: New scheduled time
            reason: Reason for rescheduling
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get demo session
            demo_session = DemoSession.query.filter_by(id=demo_session_id).first()
            if not demo_session:
                return False, "Demo session not found"
            
            # Validate user is tutor or student
            if user_id not in [demo_session.tutor_id, demo_session.student_id]:
                return False, "Unauthorized to reschedule this demo session"
            
            # Validate status
            if not demo_session.can_be_rescheduled():
                return False, f"Cannot reschedule demo in {demo_session.status.value} status"
            
            # Validate new time
            if not self._validate_scheduled_time(new_datetime):
                return False, "Invalid rescheduled time"
            
            # Check availability if rescheduling by student
            if user_id == demo_session.student_id:
                availability_check = self._check_tutor_availability(demo_session.tutor_id, new_datetime)
                if not availability_check[0]:
                    return False, availability_check[1]
            
            # Create new demo session (rescheduled)
            new_demo = DemoSession(
                student_id=demo_session.student_id,
                tutor_id=demo_session.tutor_id,
                subject_id=demo_session.subject_id,
                session_title=demo_session.session_title,
                session_description=demo_session.session_description,
                session_type=demo_session.session_type,
                duration_minutes=demo_session.duration_minutes,
                requested_date_time=new_datetime,
                scheduled_date_time=new_datetime,
                timezone=demo_session.timezone,
                location_type=demo_session.location_type,
                topics_to_cover=demo_session.topics_to_cover,
                learning_objectives=demo_session.learning_objectives,
                materials_needed=demo_session.materials_needed,
                status=DemoSessionStatus.ACCEPTED,
                rescheduled_from=demo_session.id,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
            )
            
            # Update original session
            demo_session.status = DemoSessionStatus.RESCHEDULED
            demo_session.cancellation_reason = reason
            demo_session.cancellation_initiated_by = 'student' if user_id == demo_session.student_id else 'tutor'
            demo_session.updated_at = datetime.now(timezone.utc)
            
            db.session.add(new_demo)
            db.session.commit()
            
            # Send reschedule notifications
            self._send_demo_reschedule_notifications(demo_session, new_demo)
            
            # Update analytics
            self._update_demo_analytics(demo_session.tutor_id, 'demo_rescheduled')
            
            return True, "Demo session rescheduled successfully"
            
        except Exception as e:
            current_app.logger.error(f"Error rescheduling demo session: {str(e)}")
            db.session.rollback()
            return False, f"Error rescheduling demo session: {str(e)}"
    
    def get_tutor_demo_availability(self, tutor_id: int, start_date: datetime, 
                                   end_date: datetime) -> List[Dict]:
        """
        Get tutor's demo availability for a date range
        
        Args:
            tutor_id: Tutor user ID
            start_date: Start date for availability
            end_date: End date for availability
            
        Returns:
            List of available time slots
        """
        try:
            # Get tutor's demo availability patterns
            availability_patterns = DemoAvailability.query.filter_by(
                tutor_id=tutor_id, is_active=True
            ).all()
            
            available_slots = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                # Check each availability pattern for this day
                for pattern in availability_patterns:
                    if pattern.day_of_week == current_date.weekday():
                        # Get available slots for this date
                        slots = pattern.get_available_slots(current_date)
                        
                        for slot in slots:
                            # Check if slot is still available (no existing demos)
                            slot_datetime = datetime.fromisoformat(slot['start_time'].replace('Z', '+00:00'))
                            if self._is_slot_available(tutor_id, slot_datetime):
                                available_slots.append({
                                    'date': current_date.isoformat(),
                                    'start_time': slot['start_time'],
                                    'end_time': slot['end_time'],
                                    'duration_minutes': slot['duration_minutes'],
                                    'timezone': pattern.timezone
                                })
                
                current_date += timedelta(days=1)
            
            return available_slots
            
        except Exception as e:
            current_app.logger.error(f"Error getting tutor demo availability: {str(e)}")
            return []
    
    def get_student_demo_sessions(self, student_id: int, status: Optional[str] = None) -> List[Dict]:
        """
        Get student's demo sessions
        
        Args:
            student_id: Student user ID
            status: Filter by status (optional)
            
        Returns:
            List of demo sessions
        """
        try:
            query = DemoSession.query.filter_by(student_id=student_id)
            
            if status:
                query = query.filter_by(status=DemoSessionStatus(status))
            
            demo_sessions = query.options(
                joinedload(DemoSession.tutor),
                joinedload(DemoSession.subject)
            ).order_by(desc(DemoSession.created_at)).all()
            
            return [session.to_dict() for session in demo_sessions]
            
        except Exception as e:
            current_app.logger.error(f"Error getting student demo sessions: {str(e)}")
            return []
    
    def get_tutor_demo_sessions(self, tutor_id: int, status: Optional[str] = None) -> List[Dict]:
        """
        Get tutor's demo sessions
        
        Args:
            tutor_id: Tutor user ID
            status: Filter by status (optional)
            
        Returns:
            List of demo sessions
        """
        try:
            query = DemoSession.query.filter_by(tutor_id=tutor_id)
            
            if status:
                query = query.filter_by(status=DemoSessionStatus(status))
            
            demo_sessions = query.options(
                joinedload(DemoSession.student),
                joinedload(DemoSession.subject)
            ).order_by(desc(DemoSession.created_at)).all()
            
            return [session.to_dict() for session in demo_sessions]
            
        except Exception as e:
            current_app.logger.error(f"Error getting tutor demo sessions: {str(e)}")
            return []
    
    def get_demo_templates(self, tutor_id: int, subject_id: Optional[int] = None) -> List[Dict]:
        """
        Get demo templates for a tutor
        
        Args:
            tutor_id: Tutor user ID
            subject_id: Filter by subject (optional)
            
        Returns:
            List of demo templates
        """
        try:
            query = DemoTemplate.query.filter_by(is_active=True)
            
            # Get tutor's templates and public templates
            query = query.filter(
                or_(
                    DemoTemplate.tutor_id == tutor_id,
                    DemoTemplate.is_public == True
                )
            )
            
            if subject_id:
                query = query.filter_by(subject_id=subject_id)
            
            templates = query.options(
                joinedload(DemoTemplate.tutor),
                joinedload(DemoTemplate.subject)
            ).order_by(desc(DemoTemplate.usage_count)).all()
            
            return [template.to_dict() for template in templates]
            
        except Exception as e:
            current_app.logger.error(f"Error getting demo templates: {str(e)}")
            return []
    
    def submit_demo_feedback(self, demo_session_id: int, user_id: int, 
                           feedback_data: Dict) -> Tuple[bool, str]:
        """
        Submit feedback for a demo session
        
        Args:
            demo_session_id: Demo session ID
            user_id: User ID submitting feedback
            feedback_data: Feedback details
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get demo session
            demo_session = DemoSession.query.filter_by(id=demo_session_id).first()
            if not demo_session:
                return False, "Demo session not found"
            
            # Validate user participated in demo
            if user_id not in [demo_session.tutor_id, demo_session.student_id]:
                return False, "Did not participate in this demo session"
            
            # Validate demo is completed
            if demo_session.status != DemoSessionStatus.COMPLETED:
                return False, "Can only submit feedback for completed demos"
            
            # Check if feedback already exists
            existing_feedback = DemoFeedback.query.filter_by(
                demo_session_id=demo_session_id, provided_by=user_id
            ).first()
            if existing_feedback:
                return False, "Feedback already submitted for this demo"
            
            # Create feedback
            provider_role = 'student' if user_id == demo_session.student_id else 'tutor'
            feedback = DemoFeedback(
                demo_session_id=demo_session_id,
                provided_by=user_id,
                provider_role=provider_role,
                overall_rating=feedback_data.get('overall_rating'),
                would_recommend=feedback_data.get('would_recommend'),
                would_book_paid=feedback_data.get('would_book_paid'),
                content_quality=feedback_data.get('content_quality'),
                tutor_expertise=feedback_data.get('tutor_expertise'),
                session_pace=feedback_data.get('session_pace'),
                interaction_level=feedback_data.get('interaction_level'),
                technical_quality=feedback_data.get('technical_quality'),
                what_went_well=feedback_data.get('what_went_well'),
                what_could_improve=feedback_data.get('what_could_improve'),
                most_valuable_aspect=feedback_data.get('most_valuable_aspect'),
                suggestions_for_future=feedback_data.get('suggestions_for_future'),
                main_decision_factors=feedback_data.get('main_decision_factors'),
                concerns_raised=feedback_data.get('concerns_raised'),
                price_sensitivity=feedback_data.get('price_sensitivity'),
                preferred_follow_up_method=feedback_data.get('preferred_follow_up_method'),
                best_contact_time=feedback_data.get('best_contact_time'),
                additional_questions=feedback_data.get('additional_questions'),
                is_anonymous=feedback_data.get('is_anonymous', False)
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            # Update conversion tracking if student feedback
            if provider_role == 'student' and feedback.would_book_paid:
                self._track_conversion_potential(demo_session, 'high')
            
            # Update analytics
            self._update_feedback_analytics(demo_session.tutor_id, feedback)
            
            return True, "Feedback submitted successfully"
            
        except Exception as e:
            current_app.logger.error(f"Error submitting demo feedback: {str(e)}")
            db.session.rollback()
            return False, f"Error submitting feedback: {str(e)}"
    
    def _validate_demo_request(self, student_id: int, tutor_id: int, 
                             subject_id: int, requested_datetime: datetime) -> Tuple[bool, str]:
        """Validate demo request parameters"""
        try:
            # Check if users exist and have correct roles
            student = User.query.filter_by(id=student_id).first()
            if not student or not student.is_learner():
                return False, "Invalid student user"
            
            tutor = User.query.filter_by(id=tutor_id).first()
            if not tutor or not tutor.is_tutor():
                return False, "Invalid tutor user"
            
            # Check subject exists
            subject = Subject.query.filter_by(id=subject_id).first()
            if not subject:
                return False, "Invalid subject"
            
            # Validate requested time
            if not self._validate_requested_time(requested_datetime):
                return False, "Invalid requested time"
            
            # Check if student has too many pending demos with this tutor
            pending_count = DemoSession.query.filter_by(
                student_id=student_id, tutor_id=tutor_id, 
                status=DemoSessionStatus.REQUESTED
            ).count()
            if pending_count >= 2:
                return False, "Too many pending demo requests with this tutor"
            
            return True, "Validation passed"
            
        except Exception as e:
            current_app.logger.error(f"Error validating demo request: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def _validate_requested_time(self, requested_datetime: datetime) -> bool:
        """Validate requested demo time"""
        now = datetime.now(timezone.utc)
        
        # Check if time is in the future
        if requested_datetime <= now:
            return False
        
        # Check minimum notice
        min_notice_time = now + timedelta(hours=self.min_hours_notice)
        if requested_datetime < min_notice_time:
            return False
        
        # Check maximum advance booking
        max_advance_time = now + timedelta(days=self.max_days_ahead)
        if requested_datetime > max_advance_time:
            return False
        
        return True
    
    def _validate_scheduled_time(self, scheduled_datetime: datetime) -> bool:
        """Validate scheduled demo time"""
        now = datetime.now(timezone.utc)
        
        # Check if time is in the future
        if scheduled_datetime <= now:
            return False
        
        # Check minimum notice for scheduling
        min_notice_time = now + timedelta(hours=1)
        if scheduled_datetime < min_notice_time:
            return False
        
        return True
    
    def _check_tutor_availability(self, tutor_id: int, datetime_check: datetime) -> Tuple[bool, str]:
        """Check if tutor is available for demo at specified time"""
        try:
            # Check tutor's availability patterns
            day_of_week = datetime_check.weekday()
            time_str = datetime_check.strftime('%H:%M')
            
            availability = DemoAvailability.query.filter_by(
                tutor_id=tutor_id, day_of_week=day_of_week, is_active=True
            ).first()
            
            if not availability:
                return False, "Tutor not available on this day"
            
            # Check if time falls within availability window
            if not (availability.start_time <= time_str <= availability.end_time):
                return False, "Requested time outside tutor's availability"
            
            # Check for existing demos at that time
            existing_demo = DemoSession.query.filter(
                and_(
                    DemoSession.tutor_id == tutor_id,
                    DemoSession.scheduled_date_time == datetime_check,
                    DemoSession.status.in_([DemoSessionStatus.ACCEPTED, DemoSessionStatus.SCHEDULED])
                )
            ).first()
            
            if existing_demo:
                return False, "Tutor already has a demo scheduled at this time"
            
            # Check daily limit
            day_start = datetime_check.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            daily_demos = DemoSession.query.filter(
                and_(
                    DemoSession.tutor_id == tutor_id,
                    DemoSession.scheduled_date_time >= day_start,
                    DemoSession.scheduled_date_time < day_end,
                    DemoSession.status.in_([DemoSessionStatus.ACCEPTED, DemoSessionStatus.SCHEDULED])
                )
            ).count()
            
            if daily_demos >= availability.max_demo_sessions_per_day:
                return False, "Tutor has reached maximum demos for this day"
            
            return True, "Available"
            
        except Exception as e:
            current_app.logger.error(f"Error checking tutor availability: {str(e)}")
            return False, f"Error checking availability: {str(e)}"
    
    def _is_slot_available(self, tutor_id: int, slot_datetime: datetime) -> bool:
        """Check if a specific time slot is available"""
        existing_demo = DemoSession.query.filter(
            and_(
                DemoSession.tutor_id == tutor_id,
                DemoSession.scheduled_date_time == slot_datetime,
                DemoSession.status.in_([DemoSessionStatus.ACCEPTED, DemoSessionStatus.SCHEDULED])
            )
        ).first()
        
        return existing_demo is None
    
    def _send_demo_request_notifications(self, demo_session: DemoSession):
        """Send notifications for demo request"""
        try:
            # Notify tutor
            create_notification(
                user_id=demo_session.tutor_id,
                title="New Demo Session Request",
                message=f"You have a new demo session request from {demo_session.student.first_name}",
                type="demo_request",
                related_id=demo_session.id,
                action_url=url_for('demo.view_request', demo_id=demo_session.id)
            )
            
            # Send email to tutor
            tutor_email_data = {
                'to': demo_session.tutor.email,
                'subject': f"Demo Session Request - {demo_session.session_title}",
                'template': 'demo/request_notification.html',
                'demo_session': demo_session.to_dict()
            }
            send_email(**tutor_email_data)
            
            # Send confirmation to student
            create_notification(
                user_id=demo_session.student_id,
                title="Demo Session Requested",
                message=f"Your demo session request has been sent to {demo_session.tutor.first_name}",
                type="demo_requested",
                related_id=demo_session.id,
                action_url=url_for('demo.view_request', demo_id=demo_session.id)
            )
            
        except Exception as e:
            current_app.logger.error(f"Error sending demo request notifications: {str(e)}")
    
    def _send_demo_acceptance_notifications(self, demo_session: DemoSession):
        """Send notifications for demo acceptance"""
        try:
            # Notify student
            create_notification(
                user_id=demo_session.student_id,
                title="Demo Session Accepted",
                message=f"{demo_session.tutor.first_name} has accepted your demo session request",
                type="demo_accepted",
                related_id=demo_session.id,
                action_url=url_for('demo.confirm_session', demo_id=demo_session.id)
            )
            
            # Send email to student
            student_email_data = {
                'to': demo_session.student.email,
                'subject': f"Demo Session Accepted - {demo_session.session_title}",
                'template': 'demo/acceptance_notification.html',
                'demo_session': demo_session.to_dict()
            }
            send_email(**student_email_data)
            
        except Exception as e:
            current_app.logger.error(f"Error sending demo acceptance notifications: {str(e)}")
    
    def _send_demo_confirmation_notifications(self, demo_session: DemoSession):
        """Send notifications for demo confirmation"""
        try:
            # Notify tutor
            create_notification(
                user_id=demo_session.tutor_id,
                title="Demo Session Confirmed",
                message=f"Demo session with {demo_session.student.first_name} has been confirmed",
                type="demo_confirmed",
                related_id=demo_session.id,
                action_url=url_for('demo.view_session', demo_id=demo_session.id)
            )
            
            # Send email to both parties
            email_data = {
                'subject': f"Demo Session Confirmed - {demo_session.session_title}",
                'template': 'demo/confirmation_notification.html',
                'demo_session': demo_session.to_dict()
            }
            
            # Send to student
            email_data['to'] = demo_session.student.email
            send_email(**email_data)
            
            # Send to tutor
            email_data['to'] = demo_session.tutor.email
            send_email(**email_data)
            
        except Exception as e:
            current_app.logger.error(f"Error sending demo confirmation notifications: {str(e)}")
    
    def _send_demo_completion_notifications(self, demo_session: DemoSession):
        """Send notifications for demo completion"""
        try:
            # Notify both parties
            for user in [demo_session.student, demo_session.tutor]:
                create_notification(
                    user_id=user.id,
                    title="Demo Session Completed",
                    message=f"Demo session '{demo_session.session_title}' has been completed",
                    type="demo_completed",
                    related_id=demo_session.id,
                    action_url=url_for('demo.view_session', demo_id=demo_session.id)
                )
                
                # Send email
                email_data = {
                    'to': user.email,
                    'subject': f"Demo Session Completed - {demo_session.session_title}",
                    'template': 'demo/completion_notification.html',
                    'demo_session': demo_session.to_dict()
                }
                send_email(**email_data)
                
        except Exception as e:
            current_app.logger.error(f"Error sending demo completion notifications: {str(e)}")
    
    def _send_demo_cancellation_notifications(self, demo_session: DemoSession):
        """Send notifications for demo cancellation"""
        try:
            # Notify other party
            if demo_session.cancellation_initiated_by == 'student':
                recipient = demo_session.tutor
                initiator = demo_session.student
            else:
                recipient = demo_session.student
                initiator = demo_session.tutor
            
            create_notification(
                user_id=recipient.id,
                title="Demo Session Cancelled",
                message=f"Demo session has been cancelled by {initiator.first_name}",
                type="demo_cancelled",
                related_id=demo_session.id,
                action_url=url_for('demo.view_session', demo_session.id)
            )
            
            # Send email
            email_data = {
                'to': recipient.email,
                'subject': f"Demo Session Cancelled - {demo_session.session_title}",
                'template': 'demo/cancellation_notification.html',
                'demo_session': demo_session.to_dict(),
                'cancellation_reason': demo_session.cancellation_reason
            }
            send_email(**email_data)
            
        except Exception as e:
            current_app.logger.error(f"Error sending demo cancellation notifications: {str(e)}")
    
    def _send_demo_reschedule_notifications(self, old_session: DemoSession, new_session: DemoSession):
        """Send notifications for demo rescheduling"""
        try:
            # Notify both parties
            for user in [old_session.student, old_session.tutor]:
                create_notification(
                    user_id=user.id,
                    title="Demo Session Rescheduled",
                    message=f"Demo session has been rescheduled to {new_session.scheduled_date_time}",
                    type="demo_rescheduled",
                    related_id=new_session.id,
                    action_url=url_for('demo.view_session', demo_id=new_session.id)
                )
                
                # Send email
                email_data = {
                    'to': user.email,
                    'subject': f"Demo Session Rescheduled - {new_session.session_title}",
                    'template': 'demo/reschedule_notification.html',
                    'old_session': old_session.to_dict(),
                    'new_session': new_session.to_dict()
                }
                send_email(**email_data)
                
        except Exception as e:
            current_app.logger.error(f"Error sending demo reschedule notifications: {str(e)}")
    
    def _schedule_demo_reminders(self, demo_session: DemoSession):
        """Schedule reminders for demo session"""
        try:
            # Schedule 24-hour reminder
            reminder_time_24h = demo_session.scheduled_date_time - timedelta(hours=24)
            if reminder_time_24h > datetime.now(timezone.utc):
                create_notification(
                    user_id=demo_session.student_id,
                    title="Demo Session Tomorrow",
                    message=f"Reminder: Demo session with {demo_session.tutor.first_name} tomorrow at {demo_session.scheduled_date_time}",
                    type="demo_reminder",
                    related_id=demo_session.id,
                    action_url=url_for('demo.view_session', demo_id=demo_session.id),
                    scheduled_for=reminder_time_24h
                )
                
                create_notification(
                    user_id=demo_session.tutor_id,
                    title="Demo Session Tomorrow",
                    message=f"Reminder: Demo session with {demo_session.student.first_name} tomorrow at {demo_session.scheduled_date_time}",
                    type="demo_reminder",
                    related_id=demo_session.id,
                    action_url=url_for('demo.view_session', demo_id=demo_session.id),
                    scheduled_for=reminder_time_24h
                )
            
            # Schedule 1-hour reminder
            reminder_time_1h = demo_session.scheduled_date_time - timedelta(hours=1)
            if reminder_time_1h > datetime.now(timezone.utc):
                create_notification(
                    user_id=demo_session.student_id,
                    title="Demo Session Starting Soon",
                    message=f"Demo session with {demo_session.tutor.first_name} starts in 1 hour",
                    type="demo_reminder",
                    related_id=demo_session.id,
                    action_url=url_for('demo.view_session', demo_id=demo_session.id),
                    scheduled_for=reminder_time_1h
                )
                
        except Exception as e:
            current_app.logger.error(f"Error scheduling demo reminders: {str(e)}")
    
    def _request_demo_feedback(self, demo_session: DemoSession):
        """Request feedback from demo participants"""
        try:
            # Request feedback from student
            create_notification(
                user_id=demo_session.student_id,
                title="Share Your Demo Experience",
                message=f"How was your demo session with {demo_session.tutor.first_name}? Share your feedback!",
                type="feedback_request",
                related_id=demo_session.id,
                action_url=url_for('demo.submit_feedback', demo_id=demo_session.id)
            )
            
            # Request feedback from tutor
            create_notification(
                user_id=demo_session.tutor_id,
                title="Share Demo Session Feedback",
                message=f"Share your feedback about the demo session with {demo_session.student.first_name}",
                type="feedback_request",
                related_id=demo_session.id,
                action_url=url_for('demo.submit_feedback', demo_id=demo_session.id)
            )
            
        except Exception as e:
            current_app.logger.error(f"Error requesting demo feedback: {str(e)}")
    
    def _update_demo_analytics(self, tutor_id: int, event_type: str):
        """Update demo analytics for tutor"""
        try:
            today = datetime.now(timezone.utc).date()
            
            # Get or create analytics record for today
            analytics = DemoAnalytics.query.filter_by(
                tutor_id=tutor_id, analytics_date=today, period_type='daily'
            ).first()
            
            if not analytics:
                analytics = DemoAnalytics(
                    tutor_id=tutor_id,
                    analytics_date=today,
                    period_type='daily'
                )
                db.session.add(analytics)
            
            # Update metrics based on event type
            if event_type == 'demo_requested':
                analytics.total_demos_requested += 1
            elif event_type == 'demo_accepted':
                # No specific metric for acceptance
                pass
            elif event_type == 'demo_scheduled':
                # No specific metric for scheduling
                pass
            elif event_type == 'demo_completed':
                analytics.total_demos_completed += 1
            elif event_type == 'demo_cancelled':
                analytics.total_demos_cancelled += 1
            elif event_type == 'demo_rescheduled':
                # No specific metric for rescheduling
                pass
            
            analytics.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error updating demo analytics: {str(e)}")
    
    def _track_conversion_potential(self, demo_session: DemoSession, potential_level: str):
        """Track conversion potential from demo feedback"""
        try:
            demo_session.conversion_potential = potential_level
            db.session.commit()
            
            # If high potential, create follow-up task for tutor
            if potential_level == 'high':
                create_notification(
                    user_id=demo_session.tutor_id,
                    title="High Conversion Potential",
                    message=f"Student {demo_session.student.first_name} showed high interest in booking paid sessions",
                    type="conversion_opportunity",
                    related_id=demo_session.id,
                    action_url=url_for('demo.view_session', demo_id=demo_session.id)
                )
            
        except Exception as e:
            current_app.logger.error(f"Error tracking conversion potential: {str(e)}")
    
    def _update_feedback_analytics(self, tutor_id: int, feedback: DemoFeedback):
        """Update analytics based on demo feedback"""
        try:
            today = datetime.now(timezone.utc).date()
            
            # Get or create analytics record for today
            analytics = DemoAnalytics.query.filter_by(
                tutor_id=tutor_id, analytics_date=today, period_type='daily'
            ).first()
            
            if not analytics:
                analytics = DemoAnalytics(
                    tutor_id=tutor_id,
                    analytics_date=today,
                    period_type='daily'
                )
                db.session.add(analytics)
            
            # Update rating averages
            if feedback.overall_rating:
                if analytics.average_rating is None:
                    analytics.average_rating = feedback.overall_rating
                else:
                    # Simple average - in production would use weighted average
                    analytics.average_rating = (analytics.average_rating + feedback.overall_rating) / 2
            
            # Track conversion interest
            if feedback.provider_role == 'student' and feedback.would_book_paid:
                analytics.conversion_to_paid += 1
            
            analytics.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error updating feedback analytics: {str(e)}")