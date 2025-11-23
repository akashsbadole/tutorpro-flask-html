"""
Notification Service for TutorPro Marketplace
Comprehensive notification system for students and tutors
"""

from flask import current_app, url_for
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import json
from enum import Enum

from app import db
from app.models.user import User
from app.models.notification import Notification
from app.models.student import LearnerProfile
from app.models.tutor import TutorProfile
from app.models.booking import Booking
from app.models.demo import DemoSession
from app.utils.email import send_email
from app.utils.sms import send_sms  # Assuming SMS utility exists

class NotificationType(Enum):
    """Notification types"""
    DEMO_REQUEST = "demo_request"
    DEMO_ACCEPTED = "demo_accepted"
    DEMO_CONFIRMED = "demo_confirmed"
    DEMO_CANCELLED = "demo_cancelled"
    DEMO_RESCHEDULED = "demo_rescheduled"
    DEMO_REMINDER = "demo_reminder"
    DEMO_COMPLETED = "demo_completed"
    FEEDBACK_REQUEST = "feedback_request"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_REMINDER = "booking_reminder"
    SESSION_STARTING = "session_starting"
    TUTOR_MATCH_FOUND = "tutor_match_found"
    PRICE_DROP_ALERT = "price_drop_alert"
    NEW_TUTOR_AVAILABLE = "new_tutor_available"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    LEARNING_GOAL_REMINDER = "learning_goal_reminder"
    PAYMENT_SUCCESSFUL = "payment_successful"
    PAYMENT_FAILED = "payment_failed"
    PROFILE_VIEWED = "profile_viewed"
    MESSAGE_RECEIVED = "message_received"
    REVIEW_RECEIVED = "review_received"
    SYSTEM_ANNOUNCEMENT = "system_announcement"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationService:
    """Comprehensive notification service"""
    
    def __init__(self):
        self.default_preferences = {
            'email': {
                'demo_request': True,
                'demo_accepted': True,
                'demo_confirmed': True,
                'demo_cancelled': True,
                'demo_rescheduled': True,
                'demo_reminder': True,
                'demo_completed': True,
                'feedback_request': True,
                'booking_confirmed': True,
                'booking_cancelled': True,
                'booking_reminder': True,
                'session_starting': True,
                'tutor_match_found': True,
                'price_drop_alert': False,
                'new_tutor_available': False,
                'achievement_unlocked': True,
                'learning_goal_reminder': True,
                'payment_successful': True,
                'payment_failed': True,
                'profile_viewed': False,
                'message_received': True,
                'review_received': True,
                'system_announcement': True
            },
            'push': {
                'demo_request': True,
                'demo_accepted': True,
                'demo_confirmed': True,
                'demo_cancelled': True,
                'demo_rescheduled': True,
                'demo_reminder': True,
                'demo_completed': False,
                'feedback_request': True,
                'booking_confirmed': True,
                'booking_cancelled': True,
                'booking_reminder': True,
                'session_starting': True,
                'tutor_match_found': True,
                'price_drop_alert': True,
                'new_tutor_available': True,
                'achievement_unlocked': True,
                'learning_goal_reminder': True,
                'payment_successful': False,
                'payment_failed': True,
                'profile_viewed': False,
                'message_received': True,
                'review_received': True,
                'system_announcement': True
            },
            'sms': {
                'demo_request': False,
                'demo_accepted': False,
                'demo_confirmed': False,
                'demo_cancelled': False,
                'demo_rescheduled': False,
                'demo_reminder': True,
                'demo_completed': False,
                'feedback_request': False,
                'booking_confirmed': False,
                'booking_cancelled': False,
                'booking_reminder': True,
                'session_starting': True,
                'tutor_match_found': False,
                'price_drop_alert': False,
                'new_tutor_available': False,
                'achievement_unlocked': False,
                'learning_goal_reminder': False,
                'payment_successful': False,
                'payment_failed': True,
                'profile_viewed': False,
                'message_received': False,
                'review_received': False,
                'system_announcement': False
            }
        }
    
    def create_notification(self, user_id: int, title: str, message: str, 
                          notification_type: str, related_id: int = None,
                          action_url: str = None, priority: str = 'medium',
                          scheduled_for: datetime = None, data: Dict = None) -> Notification:
        """
        Create a new notification
        
        Args:
            user_id: User ID to receive notification
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            related_id: Related object ID (booking, demo, etc.)
            action_url: URL for action button
            priority: Priority level (low, medium, high, urgent)
            scheduled_for: When to send notification (None for immediate)
            data: Additional data payload
            
        Returns:
            Created notification object
        """
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                related_id=related_id,
                action_url=action_url,
                priority=priority,
                scheduled_for=scheduled_for,
                data=data or {}
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # If immediate, process notification
            if not scheduled_for or scheduled_for <= datetime.now(timezone.utc):
                self._process_notification(notification)
            
            return notification
            
        except Exception as e:
            current_app.logger.error(f"Error creating notification: {str(e)}")
            db.session.rollback()
            return None
    
    def _process_notification(self, notification: Notification):
        """Process notification based on user preferences"""
        try:
            # Get user preferences
            user = User.query.filter_by(id=notification.user_id).first()
            if not user:
                return
            
            preferences = self._get_user_notification_preferences(notification.user_id)
            
            # Send email notification
            if self._should_send_email(notification.type, preferences):
                self._send_email_notification(notification, user)
            
            # Send push notification
            if self._should_send_push(notification.type, preferences):
                self._send_push_notification(notification, user)
            
            # Send SMS notification
            if self._should_send_sms(notification.type, preferences):
                self._send_sms_notification(notification, user)
            
            # Mark as sent
            notification.is_sent = True
            notification.sent_at = datetime.now(timezone.utc)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error processing notification: {str(e)}")
    
    def _get_user_notification_preferences(self, user_id: int) -> Dict:
        """Get user's notification preferences"""
        try:
            # Get user profile based on role
            user = User.query.filter_by(id=user_id).first()
            if not user:
                return self.default_preferences
            
            preferences = self.default_preferences.copy()
            
            if user.is_learner():
                learner_profile = LearnerProfile.query.filter_by(user_id=user_id).first()
                if learner_profile and learner_profile.notification_preferences:
                    # Merge with default preferences
                    user_prefs = learner_profile.notification_preferences
                    for channel in preferences:
                        if channel in user_prefs:
                            preferences[channel].update(user_prefs[channel])
            
            elif user.is_tutor():
                tutor_profile = TutorProfile.query.filter_by(user_id=user_id).first()
                if tutor_profile and tutor_profile.notification_preferences:
                    # Merge with default preferences
                    user_prefs = tutor_profile.notification_preferences
                    for channel in preferences:
                        if channel in user_prefs:
                            preferences[channel].update(user_prefs[channel])
            
            return preferences
            
        except Exception as e:
            current_app.logger.error(f"Error getting notification preferences: {str(e)}")
            return self.default_preferences
    
    def _should_send_email(self, notification_type: str, preferences: Dict) -> bool:
        """Check if email should be sent for notification type"""
        return preferences.get('email', {}).get(notification_type, False)
    
    def _should_send_push(self, notification_type: str, preferences: Dict) -> bool:
        """Check if push notification should be sent"""
        return preferences.get('push', {}).get(notification_type, False)
    
    def _should_send_sms(self, notification_type: str, preferences: Dict) -> bool:
        """Check if SMS should be sent"""
        return preferences.get('sms', {}).get(notification_type, False)
    
    def _send_email_notification(self, notification: Notification, user: User):
        """Send email notification"""
        try:
            # Get email template based on notification type
            template_data = self._get_email_template_data(notification, user)
            
            if template_data:
                email_data = {
                    'to': user.email,
                    'subject': notification.title,
                    'template': template_data['template'],
                    **template_data['context']
                }
                send_email(**email_data)
                
        except Exception as e:
            current_app.logger.error(f"Error sending email notification: {str(e)}")
    
    def _send_push_notification(self, notification: Notification, user: User):
        """Send push notification"""
        try:
            # This would integrate with a push notification service
            # For now, we'll just log it
            current_app.logger.info(f"Push notification for {user.email}: {notification.title}")
            
            # In production, this would use Firebase Cloud Messaging, Apple Push Notification Service, etc.
            
        except Exception as e:
            current_app.logger.error(f"Error sending push notification: {str(e)}")
    
    def _send_sms_notification(self, notification: Notification, user: User):
        """Send SMS notification"""
        try:
            # Get user's phone number
            phone_number = user.phone_number
            if not phone_number:
                return
            
            # Get SMS message
            sms_message = self._get_sms_message(notification)
            
            if sms_message:
                send_sms(phone_number, sms_message)
                
        except Exception as e:
            current_app.logger.error(f"Error sending SMS notification: {str(e)}")
    
    def _get_email_template_data(self, notification: Notification, user: User) -> Optional[Dict]:
        """Get email template data for notification type"""
        template_mapping = {
            NotificationType.DEMO_REQUEST.value: {
                'template': 'notifications/demo_request.html',
                'context': {
                    'user': user,
                    'notification': notification,
                    'demo_session': DemoSession.query.filter_by(id=notification.related_id).first()
                }
            },
            NotificationType.DEMO_ACCEPTED.value: {
                'template': 'notifications/demo_accepted.html',
                'context': {
                    'user': user,
                    'notification': notification,
                    'demo_session': DemoSession.query.filter_by(id=notification.related_id).first()
                }
            },
            NotificationType.DEMO_CONFIRMED.value: {
                'template': 'notifications/demo_confirmed.html',
                'context': {
                    'user': user,
                    'notification': notification,
                    'demo_session': DemoSession.query.filter_by(id=notification.related_id).first()
                }
            },
            NotificationType.BOOKING_CONFIRMED.value: {
                'template': 'notifications/booking_confirmed.html',
                'context': {
                    'user': user,
                    'notification': notification,
                    'booking': Booking.query.filter_by(id=notification.related_id).first()
                }
            },
            NotificationType.SESSION_STARTING.value: {
                'template': 'notifications/session_starting.html',
                'context': {
                    'user': user,
                    'notification': notification,
                    'booking': Booking.query.filter_by(id=notification.related_id).first()
                }
            },
            NotificationType.ACHIEVEMENT_UNLOCKED.value: {
                'template': 'notifications/achievement_unlocked.html',
                'context': {
                    'user': user,
                    'notification': notification,
                    'achievement': notification.data.get('achievement', {})
                }
            }
        }
        
        return template_mapping.get(notification.type)
    
    def _get_sms_message(self, notification: Notification) -> Optional[str]:
        """Get SMS message for notification type"""
        message_mapping = {
            NotificationType.DEMO_REMINDER.value: f"Reminder: Your demo session is starting soon. {notification.action_url or ''}",
            NotificationType.BOOKING_REMINDER.value: f"Reminder: Your tutoring session is starting soon. {notification.action_url or ''}",
            NotificationType.SESSION_STARTING.value: f"Your tutoring session is starting now! {notification.action_url or ''}",
            NotificationType.PAYMENT_FAILED.value: f"Payment failed. Please update your payment method. {notification.action_url or ''}",
            NotificationType.DEMO_CANCELLED.value: f"Demo session cancelled: {notification.message}",
            NotificationType.BOOKING_CANCELLED.value: f"Booking cancelled: {notification.message}"
        }
        
        return message_mapping.get(notification.type)
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False, 
                            limit: int = 50, offset: int = 0) -> List[Notification]:
        """
        Get notifications for a user
        
        Args:
            user_id: User ID
            unread_only: Get only unread notifications
            limit: Maximum number of notifications
            offset: Offset for pagination
            
        Returns:
            List of notifications
        """
        try:
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            notifications = query.order_by(desc(Notification.created_at)).offset(offset).limit(limit).all()
            
            return notifications
            
        except Exception as e:
            current_app.logger.error(f"Error getting user notifications: {str(e)}")
            return []
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        try:
            notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
            if notification:
                notification.is_read = True
                notification.read_at = datetime.now(timezone.utc)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            current_app.logger.error(f"Error marking notification as read: {str(e)}")
            return False
    
    def mark_all_notifications_read(self, user_id: int) -> bool:
        """Mark all notifications as read for user"""
        try:
            Notification.query.filter_by(user_id=user_id, is_read=False).update({
                'is_read': True,
                'read_at': datetime.now(timezone.utc)
            })
            db.session.commit()
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error marking all notifications as read: {str(e)}")
            return False
    
    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        try:
            notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
            if notification:
                db.session.delete(notification)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            current_app.logger.error(f"Error deleting notification: {str(e)}")
            return False
    
    def get_unread_count(self, user_id: int) -> int:
        """Get unread notification count for user"""
        try:
            return Notification.query.filter_by(user_id=user_id, is_read=False).count()
        except Exception as e:
            current_app.logger.error(f"Error getting unread count: {str(e)}")
            return 0
    
    def schedule_session_reminders(self, session_type: str, session_id: int):
        """Schedule reminders for demo or booking sessions"""
        try:
            if session_type == 'demo':
                session = DemoSession.query.filter_by(id=session_id).first()
                if not session or not session.scheduled_date_time:
                    return
                session_time = session.scheduled_date_time
                user_id = session.student_id
                related_id = session.id
                base_url = url_for('demo.view_demo', demo_id=session_id)
                
            elif session_type == 'booking':
                session = Booking.query.filter_by(id=session_id).first()
                if not session or not session.scheduled_start_time:
                    return
                session_time = session.scheduled_start_time
                user_id = session.student_id
                related_id = session.id
                base_url = url_for('student.view_booking', booking_id=session_id)
                
            else:
                return
            
            # Schedule 24-hour reminder
            reminder_24h = session_time - timedelta(hours=24)
            if reminder_24h > datetime.now(timezone.utc):
                self.create_notification(
                    user_id=user_id,
                    title="Session Tomorrow",
                    message=f"Reminder: You have a {session_type} session scheduled for tomorrow at {session_time.strftime('%I:%M %p')}",
                    notification_type=f"{session_type}_reminder",
                    related_id=related_id,
                    action_url=base_url,
                    priority='medium',
                    scheduled_for=reminder_24h
                )
            
            # Schedule 1-hour reminder
            reminder_1h = session_time - timedelta(hours=1)
            if reminder_1h > datetime.now(timezone.utc):
                self.create_notification(
                    user_id=user_id,
                    title="Session Starting Soon",
                    message=f"Your {session_type} session starts in 1 hour!",
                    notification_type=f"{session_type}_reminder",
                    related_id=related_id,
                    action_url=base_url,
                    priority='high',
                    scheduled_for=reminder_1h
                )
            
            # Schedule session starting notification
            self.create_notification(
                user_id=user_id,
                title="Session Starting Now",
                message=f"Your {session_type} session is starting now!",
                notification_type="session_starting",
                related_id=related_id,
                action_url=base_url,
                priority='urgent',
                scheduled_for=session_time
            )
            
        except Exception as e:
            current_app.logger.error(f"Error scheduling session reminders: {str(e)}")
    
    def send_learning_goal_reminders(self):
        """Send reminders for learning goals"""
        try:
            # Get learning goals that need reminders
            from app.models.student import StudentLearningGoal
            
            # Goals due in next 7 days
            upcoming_goals = StudentLearningGoal.query.filter(
                and_(
                    StudentLearningGoal.is_active == True,
                    StudentLearningGoal.target_date <= datetime.now(timezone.utc) + timedelta(days=7),
                    StudentLearningGoal.target_date >= datetime.now(timezone.utc)
                )
            ).all()
            
            for goal in upcoming_goals:
                # Send reminder to student
                self.create_notification(
                    user_id=goal.learner_profile.user_id,
                    title="Learning Goal Deadline Approaching",
                    message=f"Your learning goal '{goal.title}' is due on {goal.target_date.strftime('%B %d, %Y')}",
                    notification_type="learning_goal_reminder",
                    related_id=goal.id,
                    action_url=url_for('student.learning_goals'),
                    priority='medium'
                )
            
        except Exception as e:
            current_app.logger.error(f"Error sending learning goal reminders: {str(e)}")
    
    def send_tutor_match_notifications(self, student_id: int, matched_tutors: List[Dict]):
        """Send notifications when new tutor matches are found"""
        try:
            if not matched_tutors:
                return
            
            # Get top matches
            top_matches = matched_tutors[:3]
            
            tutor_names = [match['tutor']['user']['first_name'] + ' ' + match['tutor']['user']['last_name'] 
                          for match in top_matches]
            
            self.create_notification(
                user_id=student_id,
                title="New Tutor Matches Found",
                message=f"We found {len(matched_tutors)} new tutors matching your preferences. Top matches: {', '.join(tutor_names)}",
                notification_type="tutor_match_found",
                action_url=url_for('search.tutor_discovery'),
                priority='medium',
                data={'matched_tutors': [match['tutor']['id'] for match in top_matches]}
            )
            
        except Exception as e:
            current_app.logger.error(f"Error sending tutor match notifications: {str(e)}")
    
    def send_price_drop_alerts(self, student_id: int, price_drops: List[Dict]):
        """Send notifications for price drops"""
        try:
            if not price_drops:
                return
            
            for drop in price_drops:
                self.create_notification(
                    user_id=student_id,
                    title="Price Drop Alert",
                    message=f"{drop['tutor_name']} has reduced their hourly rate to ${drop['new_rate']} for {drop['subject']}",
                    notification_type="price_drop_alert",
                    action_url=url_for('tutor.profile', user_id=drop['tutor_id']),
                    priority='low',
                    data=drop
                )
            
        except Exception as e:
            current_app.logger.error(f"Error sending price drop alerts: {str(e)}")
    
    def send_achievement_notifications(self, student_id: int, achievements: List[Dict]):
        """Send notifications for unlocked achievements"""
        try:
            for achievement in achievements:
                self.create_notification(
                    user_id=student_id,
                    title="Achievement Unlocked! 🏆",
                    message=f"Congratulations! You've unlocked the '{achievement['title']}' achievement",
                    notification_type="achievement_unlocked",
                    action_url=url_for('student.achievements'),
                    priority='medium',
                    data={'achievement': achievement}
                )
            
        except Exception as e:
            current_app.logger.error(f"Error sending achievement notifications: {str(e)}")
    
    def send_system_announcement(self, title: str, message: str, 
                              target_roles: List[str] = None, priority: str = 'medium'):
        """Send system announcement to users"""
        try:
            # Get target users
            query = User.query.filter_by(is_active=True)
            
            if target_roles:
                query = query.filter(User.role.in_(target_roles))
            
            users = query.all()
            
            for user in users:
                self.create_notification(
                    user_id=user.id,
                    title=title,
                    message=message,
                    notification_type="system_announcement",
                    priority=priority
                )
            
        except Exception as e:
            current_app.logger.error(f"Error sending system announcement: {str(e)}")
    
    def process_scheduled_notifications(self):
        """Process scheduled notifications (to be called by cron job)"""
        try:
            # Get notifications scheduled for now or past
            scheduled_notifications = Notification.query.filter(
                and_(
                    Notification.scheduled_for <= datetime.now(timezone.utc),
                    Notification.is_sent == False
                )
            ).all()
            
            for notification in scheduled_notifications:
                self._process_notification(notification)
            
            current_app.logger.info(f"Processed {len(scheduled_notifications)} scheduled notifications")
            
        except Exception as e:
            current_app.logger.error(f"Error processing scheduled notifications: {str(e)}")
    
    def cleanup_old_notifications(self, days: int = 30):
        """Clean up old read notifications"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Delete old read notifications
            deleted_count = Notification.query.filter(
                and_(
                    Notification.is_read == True,
                    Notification.read_at < cutoff_date
                )
            ).delete()
            
            db.session.commit()
            
            current_app.logger.info(f"Cleaned up {deleted_count} old notifications")
            
        except Exception as e:
            current_app.logger.error(f"Error cleaning up notifications: {str(e)}")

# Singleton instance
notification_service = NotificationService()

# Convenience functions
def create_notification(user_id: int, title: str, message: str, 
                     notification_type: str, related_id: int = None,
                     action_url: str = None, priority: str = 'medium',
                     scheduled_for: datetime = None, data: Dict = None) -> Notification:
    """Convenience function to create notification"""
    return notification_service.create_notification(
        user_id, title, message, notification_type, related_id, 
        action_url, priority, scheduled_for, data
    )

def get_user_notifications(user_id: int, unread_only: bool = False, 
                        limit: int = 50, offset: int = 0) -> List[Notification]:
    """Convenience function to get user notifications"""
    return notification_service.get_user_notifications(user_id, unread_only, limit, offset)

def mark_notification_read(notification_id: int, user_id: int) -> bool:
    """Convenience function to mark notification as read"""
    return notification_service.mark_notification_read(notification_id, user_id)

def get_unread_count(user_id: int) -> int:
    """Convenience function to get unread count"""
    return notification_service.get_unread_count(user_id)