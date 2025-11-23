"""
Notification utilities for TutorPro Marketplace
Basic notification creation and management
"""

from datetime import datetime, timezone
from typing import Dict, Optional
import logging

from app import db
from app.models.notification import Notification

logger = logging.getLogger(__name__)

def create_notification(user_id: int, title: str, message: str, 
                      notification_type: str = 'info', related_id: Optional[int] = None,
                      action_url: Optional[str] = None, scheduled_for: Optional[datetime] = None) -> bool:
    """
    Create a notification for a user
    
    Args:
        user_id: User ID to create notification for
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info, success, warning, error)
        related_id: Optional related object ID
        action_url: Optional action URL for the notification
        scheduled_for: Optional scheduled time for the notification
        
    Returns:
        bool: True if notification was created successfully, False otherwise
    """
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            related_id=related_id,
            action_url=action_url,
            scheduled_for=scheduled_for or datetime.now(timezone.utc),
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(notification)
        db.session.commit()
        
        logger.info(f"Created notification for user {user_id}: {title}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        db.session.rollback()
        return False

def mark_notification_read(notification_id: int, user_id: int) -> bool:
    """
    Mark a notification as read
    
    Args:
        notification_id: Notification ID
        user_id: User ID (for verification)
        
    Returns:
        bool: True if notification was marked as read, False otherwise
    """
    try:
        notification = Notification.query.filter_by(
            id=notification_id, user_id=user_id
        ).first()
        
        if not notification:
            return False
        
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        db.session.rollback()
        return False

def mark_all_notifications_read(user_id: int) -> bool:
    """
    Mark all notifications for a user as read
    
    Args:
        user_id: User ID
        
    Returns:
        bool: True if notifications were marked as read, False otherwise
    """
    try:
        notifications = Notification.query.filter_by(
            user_id=user_id, is_read=False
        ).all()
        
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
        
        db.session.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        db.session.rollback()
        return False

def get_user_notifications(user_id: int, unread_only: bool = False, 
                        limit: int = 50) -> list:
    """
    Get notifications for a user
    
    Args:
        user_id: User ID
        unread_only: Whether to get only unread notifications
        limit: Maximum number of notifications to return
        
    Returns:
        list: List of Notification objects
    """
    try:
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).all()
        
    except Exception as e:
        logger.error(f"Error getting user notifications: {str(e)}")
        return []

def delete_notification(notification_id: int, user_id: int) -> bool:
    """
    Delete a notification
    
    Args:
        notification_id: Notification ID
        user_id: User ID (for verification)
        
    Returns:
        bool: True if notification was deleted, False otherwise
    """
    try:
        notification = Notification.query.filter_by(
            id=notification_id, user_id=user_id
        ).first()
        
        if not notification:
            return False
        
        db.session.delete(notification)
        db.session.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        db.session.rollback()
        return False

def get_unread_notification_count(user_id: int) -> int:
    """
    Get count of unread notifications for a user
    
    Args:
        user_id: User ID
        
    Returns:
        int: Number of unread notifications
    """
    try:
        return Notification.query.filter_by(
            user_id=user_id, is_read=False
        ).count()
        
    except Exception as e:
        logger.error(f"Error getting unread notification count: {str(e)}")
        return 0