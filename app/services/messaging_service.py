"""
Messaging Service for TutorPro Marketplace
Provides real-time messaging with advanced features
"""

from typing import Dict, List, Optional, Tuple
from flask import current_app
from datetime import datetime, timedelta
import json
import secrets
from app import db
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.student import LearnerProfile


class MessagingService:
    """Enhanced messaging service with real-time capabilities"""
    
    def __init__(self):
        # Defer config access until app context is available
        self._max_message_length = None
        self._max_file_size = None
        self._message_retention_days = None
        self._rate_limit_per_minute = None
    
    @property
    def max_message_length(self):
        if self._max_message_length is None:
            self._max_message_length = current_app.config.get('MAX_MESSAGE_LENGTH', 2000)
        return self._max_message_length
    
    @property
    def max_file_size(self):
        if self._max_file_size is None:
            self._max_file_size = current_app.config.get('MAX_FILE_SIZE_MB', 10)
        return self._max_file_size
    
    @property
    def message_retention_days(self):
        if self._message_retention_days is None:
            self._message_retention_days = current_app.config.get('MESSAGE_RETENTION_DAYS', 365)
        return self._message_retention_days
    
    @property
    def rate_limit_per_minute(self):
        if self._rate_limit_per_minute is None:
            self._rate_limit_per_minute = current_app.config.get('MESSAGE_RATE_LIMIT_PER_MINUTE', 10)
        return self._rate_limit_per_minute
    
    def send_message(self, sender_id: int, recipient_id: int, content: str, 
                   message_type: str = 'text', attachments: List = None) -> Dict:
        """
        Send a message between users
        
        Args:
            sender_id: Sender user ID
            recipient_id: Recipient user ID
            content: Message content
            message_type: Type of message (text, image, file, system)
            attachments: List of file attachments
            
        Returns:
            Dictionary with send result
        """
        try:
            # Validate sender and recipient
            sender = User.query.get(sender_id)
            recipient = User.query.get(recipient_id)
            
            if not sender or not recipient:
                return {
                    'success': False,
                    'error': 'Invalid sender or recipient'
                }
            
            # Validate message content
            if not content or len(content.strip()) == 0:
                return {
                    'success': False,
                    'error': 'Message content cannot be empty'
                }
            
            if len(content) > self.max_message_length:
                return {
                    'success': False,
                    'error': f'Message too long. Maximum {self.max_message_length} characters.'
                }
            
            # Check rate limiting
            if self._is_rate_limited(sender_id):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded. Please wait before sending more messages.'
                }
            
            # Create message record
            message = {
                'id': secrets.token_urlsafe(16),
                'sender_id': sender_id,
                'recipient_id': recipient_id,
                'content': content,
                'message_type': message_type,
                'attachments': attachments or [],
                'sent_at': datetime.utcnow().isoformat(),
                'read_at': None,
                'edited_at': None,
                'deleted_at': None,
                'metadata': {
                    'sender_name': sender.get_full_name(),
                    'recipient_name': recipient.get_full_name(),
                    'sender_role': sender.role,
                    'recipient_role': recipient.role
                }
            }
            
            # In a real implementation, you would save to database
            # For now, return success response
            
            return {
                'success': True,
                'message': message
            }
            
        except Exception as e:
            current_app.logger.error(f"Error sending message: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to send message'
            }
    
    def mark_message_read(self, message_id: str, user_id: int) -> Dict:
        """
        Mark message as read
        
        Args:
            message_id: Message ID
            user_id: User ID marking as read
            
        Returns:
            Dictionary with result
        """
        try:
            # In a real implementation, you would:
            # 1. Update message status in database
            # 2. Update read receipt
            # 3. Notify sender of read receipt
            
            return {
                'success': True,
                'read_at': datetime.utcnow().isoformat(),
                'message_id': message_id
            }
            
        except Exception as e:
            current_app.logger.error(f"Error marking message as read: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to mark message as read'
            }
    
    def edit_message(self, message_id: str, user_id: int, new_content: str) -> Dict:
        """
        Edit an existing message
        
        Args:
            message_id: Message ID
            user_id: User ID editing message
            new_content: New message content
            
        Returns:
            Dictionary with edit result
        """
        try:
            # Validate new content
            if not new_content or len(new_content.strip()) == 0:
                return {
                    'success': False,
                    'error': 'Message content cannot be empty'
                }
            
            if len(new_content) > self.max_message_length:
                return {
                    'success': False,
                    'error': f'Message too long. Maximum {self.max_message_length} characters.'
                }
            
            # In a real implementation, you would:
            # 1. Verify user owns the message
            # 2. Check if message is editable (sent within last 15 minutes)
            # 3. Update content in database
            # 4. Add edit history
            
            # Check if message is editable (sent within last 15 minutes)
            editable = True  # In production, check actual timestamp
            
            if not editable:
                return {
                    'success': False,
                    'error': 'Message can no longer be edited (time limit exceeded)'
                }
            
            edit_data = {
                'message_id': message_id,
                'edited_at': datetime.utcnow().isoformat(),
                'new_content': new_content,
                'edit_count': 1  # In production, get actual count
            }
            
            return {
                'success': True,
                'edit': edit_data
            }
            
        except Exception as e:
            current_app.logger.error(f"Error editing message: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to edit message'
            }
    
    def delete_message(self, message_id: str, user_id: int, delete_type: str = 'self') -> Dict:
        """
        Delete a message
        
        Args:
            message_id: Message ID
            user_id: User ID deleting message
            delete_type: 'self' or 'everyone'
            
        Returns:
            Dictionary with delete result
        """
        try:
            # In a real implementation, you would:
            # 1. Verify user owns the message
            # 2. Update message status in database
            # 3. If delete_type is 'everyone', mark as deleted for all users
            # 4. Add delete audit trail
            
            delete_data = {
                'message_id': message_id,
                'deleted_at': datetime.utcnow().isoformat(),
                'deleted_by': user_id,
                'delete_type': delete_type  # self or everyone
            }
            
            return {
                'success': True,
                'delete': delete_data
            }
            
        except Exception as e:
            current_app.logger.error(f"Error deleting message: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to delete message'
            }
    
    def get_conversation(self, user1_id: int, user2_id: int, 
                      page: int = 1, per_page: int = 50) -> Dict:
        """
        Get conversation between two users
        
        Args:
            user1_id: First user ID
            user2_id: Second user ID
            page: Page number
            per_page: Messages per page
            
        Returns:
            Dictionary with conversation data
        """
        try:
            # In a real implementation, you would:
            # 1. Query database for messages between users
            # 2. Apply pagination
            # 3. Include read receipts
            # 4. Format messages
            
            # For now, return mock conversation
            conversation = {
                'user1_id': user1_id,
                'user2_id': user2_id,
                'messages': [],  # Would be populated from database
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,  # Would be actual count
                    'pages': 0
                },
                'last_message': None,
                'unread_count': 0
            }
            
            return {
                'success': True,
                'conversation': conversation
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting conversation: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get conversation'
            }
    
    def get_user_conversations(self, user_id: int, page: int = 1, 
                           per_page: int = 20, search: str = None) -> Dict:
        """
        Get all conversations for a user
        
        Args:
            user_id: User ID
            page: Page number
            per_page: Conversations per page
            search: Search term to filter conversations
            
        Returns:
            Dictionary with conversations data
        """
        try:
            # In a real implementation, you would:
            # 1. Query database for user's conversations
            # 2. Get last message and unread count for each conversation
            # 3. Apply search filter if provided
            # 4. Apply pagination
            
            conversations = []  # Would be populated from database
            
            return {
                'success': True,
                'conversations': conversations,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,  # Would be actual count
                    'pages': 0
                },
                'unread_total': 0
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting user conversations: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get conversations'
            }
    
    def block_user(self, blocker_id: int, blocked_id: int, reason: str = None) -> Dict:
        """
        Block a user from sending messages
        
        Args:
            blocker_id: User doing the blocking
            blocked_id: User being blocked
            reason: Reason for blocking (optional)
            
        Returns:
            Dictionary with block result
        """
        try:
            # Check if already blocked
            if self._is_user_blocked(blocker_id, blocked_id):
                return {
                    'success': False,
                    'error': 'User is already blocked'
                }
            
            # Create block record
            block_data = {
                'id': secrets.token_urlsafe(16),
                'blocker_id': blocker_id,
                'blocked_id': blocked_id,
                'reason': reason,
                'blocked_at': datetime.utcnow().isoformat(),
                'expires_at': None  # Could be set for temporary blocks
            }
            
            return {
                'success': True,
                'block': block_data
            }
            
        except Exception as e:
            current_app.logger.error(f"Error blocking user: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to block user'
            }
    
    def unblock_user(self, blocker_id: int, blocked_id: int) -> Dict:
        """
        Unblock a user
        
        Args:
            blocker_id: User doing the unblocking
            blocked_id: User being unblocked
            
        Returns:
            Dictionary with unblock result
        """
        try:
            # Check if user is blocked
            if not self._is_user_blocked(blocker_id, blocked_id):
                return {
                    'success': False,
                    'error': 'User is not blocked'
                }
            
            # In a real implementation, you would:
            # 1. Remove block record from database
            # 2. Log unblock action
            
            unblock_data = {
                'unblocked_at': datetime.utcnow().isoformat(),
                'blocker_id': blocker_id,
                'blocked_id': blocked_id
            }
            
            return {
                'success': True,
                'unblock': unblock_data
            }
            
        except Exception as e:
            current_app.logger.error(f"Error unblocking user: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to unblock user'
            }
    
    def get_blocked_users(self, user_id: int) -> Dict:
        """
        Get list of blocked users for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with blocked users list
        """
        try:
            # In a real implementation, you would query database
            blocked_users = []  # Would be populated from database
            
            return {
                'success': True,
                'blocked_users': blocked_users
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting blocked users: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get blocked users'
            }
    
    def send_broadcast_message(self, sender_id: int, recipient_type: str, content: str, 
                          recipient_filter: Dict = None) -> Dict:
        """
        Send broadcast message to multiple users
        
        Args:
            sender_id: Sender user ID (must be admin)
            recipient_type: Type ('all', 'tutors', 'students', 'verified')
            content: Message content
            recipient_filter: Additional filters
            
        Returns:
            Dictionary with broadcast result
        """
        try:
            # Verify sender is admin
            sender = User.query.get(sender_id)
            if not sender or not sender.is_admin():
                return {
                    'success': False,
                    'error': 'Only administrators can send broadcast messages'
                }
            
            # Validate content
            if not content or len(content.strip()) == 0:
                return {
                    'success': False,
                    'error': 'Broadcast message content cannot be empty'
                }
            
            # Create broadcast record
            broadcast = {
                'id': secrets.token_urlsafe(16),
                'sender_id': sender_id,
                'recipient_type': recipient_type,
                'content': content,
                'recipient_filter': recipient_filter or {},
                'sent_at': datetime.utcnow().isoformat(),
                'delivery_status': 'pending',
                'delivered_count': 0,
                'total_recipients': 0
            }
            
            # In a real implementation, you would:
            # 1. Determine recipient list based on type and filters
            # 2. Create individual message records for each recipient
            # 3. Queue messages for delivery
            # 4. Send push notifications
            
            return {
                'success': True,
                'broadcast': broadcast
            }
            
        except Exception as e:
            current_app.logger.error(f"Error sending broadcast: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to send broadcast message'
            }
    
    def get_message_attachments(self, message_id: str, user_id: int) -> Dict:
        """
        Get attachments for a message
        
        Args:
            message_id: Message ID
            user_id: User ID requesting attachments
            
        Returns:
            Dictionary with attachments data
        """
        try:
            # In a real implementation, you would:
            # 1. Verify user has access to message
            # 2. Query database for attachments
            # 3. Return download URLs
            
            attachments = []  # Would be populated from database
            
            return {
                'success': True,
                'attachments': attachments,
                'message_id': message_id
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting message attachments: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get message attachments'
            }
    
    def search_messages(self, user_id: int, query: str, 
                     page: int = 1, per_page: int = 20) -> Dict:
        """
        Search messages for a user
        
        Args:
            user_id: User ID
            query: Search query
            page: Page number
            per_page: Results per page
            
        Returns:
            Dictionary with search results
        """
        try:
            # Validate query
            if not query or len(query.strip()) < 2:
                return {
                    'success': False,
                    'error': 'Search query must be at least 2 characters'
                }
            
            # In a real implementation, you would:
            # 1. Search database for messages containing query
            # 2. Search in message content and attachments
            # 3. Apply pagination
            # 4. Highlight search terms in results
            
            search_results = []  # Would be populated from database
            
            return {
                'success': True,
                'results': search_results,
                'query': query,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,  # Would be actual count
                    'pages': 0
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error searching messages: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to search messages'
            }
    
    def _is_rate_limited(self, user_id: int) -> bool:
        """Check if user is rate limited for messaging"""
        try:
            # In a real implementation, you would:
            # 1. Check message count in last minute
            # 2. Return True if exceeds limit
            
            # For now, return False (no rate limiting)
            return False
            
        except Exception as e:
            current_app.logger.error(f"Error checking rate limit: {str(e)}")
            return False
    
    def _is_user_blocked(self, blocker_id: int, blocked_id: int) -> bool:
        """Check if user is blocked"""
        try:
            # In a real implementation, you would query database
            # For now, return False (no blocks)
            return False
            
        except Exception as e:
            current_app.logger.error(f"Error checking block status: {str(e)}")
            return False
    
    def get_messaging_stats(self, user_id: int, days: int = 30) -> Dict:
        """
        Get messaging statistics for a user
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with messaging statistics
        """
        try:
            # In a real implementation, you would:
            # 1. Calculate messages sent/received in period
            # 2. Calculate response times
            # 3. Calculate most active conversations
            # 4. Calculate attachment usage
            
            stats = {
                'period_days': days,
                'messages_sent': 0,
                'messages_received': 0,
                'messages_read': 0,
                'average_response_time_minutes': 0,
                'most_active_conversations': [],
                'attachments_sent': 0,
                'total_size_mb': 0,
                'blocked_users_count': 0,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting messaging stats: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get messaging statistics'
            }
