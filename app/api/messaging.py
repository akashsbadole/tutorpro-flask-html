"""
Messaging API endpoints for TutorPro Marketplace
Provides RESTful API for real-time messaging with advanced features
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.messaging_service import MessagingService
from app.utils.decorators import rate_limit
from datetime import datetime
import json

# Create blueprint
messaging_bp = Blueprint('messaging_api', __name__, url_prefix='/api/messaging')

# Initialize messaging service (lazy initialization)
messaging_service = None

def get_messaging_service():
    """Get messaging service instance with app context"""
    global messaging_service
    if messaging_service is None:
        messaging_service = MessagingService()
    return messaging_service

@messaging_bp.route('/send', methods=['POST'])
@jwt_required()
@rate_limit(limit=30, period=3600)  # 30 requests per hour
def send_message():
    """
    Send a message to another user
    
    Request Body:
    - recipient_id: Recipient user ID
    - content: Message content
    - message_type: Type of message (text, image, file)
    - attachments: List of file attachments (optional)
    """
    try:
        sender_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('recipient_id') or not data.get('content'):
            return jsonify({
                'success': False,
                'error': 'Recipient ID and content are required'
            }), 400
        
        recipient_id = data['recipient_id']
        content = data['content']
        message_type = data.get('message_type', 'text')
        attachments = data.get('attachments')
        
        messaging_service = get_messaging_service()
        result = messaging_service.send_message(sender_id, recipient_id, content, message_type, attachments)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error sending message: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to send message'
        }), 500

@messaging_bp.route('/read', methods=['POST'])
@jwt_required()
@rate_limit(limit=50, period=3600)  # 50 requests per hour
def mark_message_read():
    """
    Mark a message as read
    
    Request Body:
    - message_id: Message ID to mark as read
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('message_id'):
            return jsonify({
                'success': False,
                'error': 'Message ID is required'
            }), 400
        
        message_id = data['message_id']
        
        messaging_service = get_messaging_service()
        result = messaging_service.mark_message_read(message_id, user_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'read_at': result['read_at'],
                    'message_id': message_id
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error marking message as read: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to mark message as read'
        }), 500

@messaging_bp.route('/edit', methods=['POST'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def edit_message():
    """
    Edit an existing message
    
    Request Body:
    - message_id: Message ID to edit
    - new_content: New message content
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('message_id') or not data.get('new_content'):
            return jsonify({
                'success': False,
                'error': 'Message ID and new content are required'
            }), 400
        
        message_id = data['message_id']
        new_content = data['new_content']
        
        messaging_service = get_messaging_service()
        result = messaging_service.edit_message(message_id, user_id, new_content)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['edit']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error editing message: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to edit message'
        }), 500

@messaging_bp.route('/delete', methods=['POST'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def delete_message():
    """
    Delete a message
    
    Request Body:
    - message_id: Message ID to delete
    - delete_type: 'self' or 'everyone' (optional)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('message_id'):
            return jsonify({
                'success': False,
                'error': 'Message ID is required'
            }), 400
        
        message_id = data['message_id']
        delete_type = data.get('delete_type', 'self')
        
        messaging_service = get_messaging_service()
        result = messaging_service.delete_message(message_id, user_id, delete_type)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['delete']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error deleting message: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete message'
        }), 500

@messaging_bp.route('/conversation/<int:user1_id>/<int:user2_id>', methods=['GET'])
@jwt_required()
@rate_limit(limit=40, period=3600)  # 40 requests per hour
def get_conversation(user1_id, user2_id):
    """
    Get conversation between two users
    
    Path Parameters:
    - user1_id: First user ID
    - user2_id: Second user ID
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Messages per page (default: 50)
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Verify current user is part of the conversation
        if current_user_id not in [user1_id, user2_id]:
            return jsonify({
                'success': False,
                'error': 'Access denied to this conversation'
            }), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = min(100, max(1, int(request.args.get('per_page', 50))))
        
        messaging_service = get_messaging_service()
        result = messaging_service.get_conversation(user1_id, user2_id, page, per_page)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['conversation']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error getting conversation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get conversation'
        }), 500

@messaging_bp.route('/conversations', methods=['GET'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def get_user_conversations():
    """
    Get all conversations for the current user
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Conversations per page (default: 20)
    - search: Search term to filter conversations (optional)
    """
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = min(50, max(1, int(request.args.get('per_page', 20))))
        search = request.args.get('search')
        
        messaging_service = get_messaging_service()
        result = messaging_service.get_user_conversations(user_id, page, per_page, search)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['conversations']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error getting user conversations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get conversations'
        }), 500

@messaging_bp.route('/block', methods=['POST'])
@jwt_required()
@rate_limit(limit=10, period=3600)  # 10 requests per hour
def block_user():
    """
    Block a user from sending messages
    
    Request Body:
    - blocked_id: User ID to block
    - reason: Reason for blocking (optional)
    """
    try:
        blocker_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('blocked_id'):
            return jsonify({
                'success': False,
                'error': 'User ID to block is required'
            }), 400
        
        blocked_id = data['blocked_id']
        reason = data.get('reason')
        
        messaging_service = get_messaging_service()
        result = messaging_service.block_user(blocker_id, blocked_id, reason)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['block']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error blocking user: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to block user'
        }), 500

@messaging_bp.route('/unblock', methods=['POST'])
@jwt_required()
@rate_limit(limit=10, period=3600)  # 10 requests per hour
def unblock_user():
    """
    Unblock a user
    
    Request Body:
    - blocked_id: User ID to unblock
    """
    try:
        blocker_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('blocked_id'):
            return jsonify({
                'success': False,
                'error': 'User ID to unblock is required'
            }), 400
        
        blocked_id = data['blocked_id']
        
        messaging_service = get_messaging_service()
        result = messaging_service.unblock_user(blocker_id, blocked_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['unblock']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error unblocking user: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to unblock user'
        }), 500

@messaging_bp.route('/blocked', methods=['GET'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def get_blocked_users():
    """
    Get list of blocked users for the current user
    """
    try:
        user_id = get_jwt_identity()
        
        messaging_service = get_messaging_service()
        result = messaging_service.get_blocked_users(user_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['blocked_users']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error getting blocked users: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get blocked users'
        }), 500

@messaging_bp.route('/broadcast', methods=['POST'])
@jwt_required()
@rate_limit(limit=5, period=3600)  # 5 requests per hour (admin only)
def send_broadcast_message():
    """
    Send broadcast message to multiple users
    
    Request Body:
    - recipient_type: Type ('all', 'tutors', 'students', 'verified')
    - content: Message content
    - recipient_filter: Additional filters (optional)
    """
    try:
        sender_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('recipient_type') or not data.get('content'):
            return jsonify({
                'success': False,
                'error': 'Recipient type and content are required'
            }), 400
        
        recipient_type = data['recipient_type']
        content = data['content']
        recipient_filter = data.get('recipient_filter')
        
        messaging_service = get_messaging_service()
        result = messaging_service.send_broadcast_message(sender_id, recipient_type, content, recipient_filter)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['broadcast']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error sending broadcast: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to send broadcast message'
        }), 500

@messaging_bp.route('/attachments/<message_id>', methods=['GET'])
@jwt_required()
@rate_limit(limit=30, period=3600)  # 30 requests per hour
def get_message_attachments(message_id):
    """
    Get attachments for a message
    
    Path Parameters:
    - message_id: Message ID
    """
    try:
        user_id = get_jwt_identity()
        
        messaging_service = get_messaging_service()
        result = messaging_service.get_message_attachments(message_id, user_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['attachments']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error getting message attachments: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get message attachments'
        }), 500

@messaging_bp.route('/search', methods=['GET'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def search_messages():
    """
    Search messages for the current user
    
    Query Parameters:
    - q: Search query
    - page: Page number (default: 1)
    - per_page: Results per page (default: 20)
    """
    try:
        user_id = get_jwt_identity()
        query = request.args.get('q')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        page = request.args.get('page', 1, type=int)
        per_page = min(50, max(1, int(request.args.get('per_page', 20))))
        
        messaging_service = get_messaging_service()
        result = messaging_service.search_messages(user_id, query, page, per_page)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['results']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error searching messages: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to search messages'
        }), 500

@messaging_bp.route('/stats', methods=['GET'])
@jwt_required()
@rate_limit(limit=10, period=3600)  # 10 requests per hour
def get_messaging_stats():
    """
    Get messaging statistics for the current user
    
    Query Parameters:
    - days: Number of days to analyze (default: 30)
    """
    try:
        user_id = get_jwt_identity()
        days = min(365, max(1, int(request.args.get('days', 30))))
        
        messaging_service = get_messaging_service()
        result = messaging_service.get_messaging_stats(user_id, days)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['stats']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error getting messaging stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get messaging statistics'
        }), 500

@messaging_bp.route('/features/status', methods=['GET'])
@jwt_required()
def get_messaging_features_status():
    """
    Get status of messaging features
    """
    try:
        features_status = {
            'real_time_messaging': {
                'available': True,
                'description': 'Real-time messaging with WebSocket support'
            },
            'message_types': {
                'available': True,
                'types': ['text', 'image', 'file', 'system'],
                'description': 'Support for multiple message types'
            },
            'attachments': {
                'available': True,
                'max_size_mb': get_messaging_service().max_file_size,
                'description': f'File attachments up to {messaging_service.max_file_size}MB'
            },
            'editing': {
                'available': True,
                'time_limit_minutes': 15,
                'description': 'Edit messages within 15 minutes of sending'
            },
            'deletion': {
                'available': True,
                'types': ['self', 'everyone'],
                'description': 'Delete for sender or all participants'
            },
            'read_receipts': {
                'available': True,
                'description': 'Message read receipts and tracking'
            },
            'blocking': {
                'available': True,
                'description': 'Block/unblock users from messaging'
            },
            'broadcast': {
                'available': True,
                'admin_only': True,
                'description': 'Broadcast messages to multiple users'
            },
            'search': {
                'available': True,
                'description': 'Search messages and conversations'
            },
            'rate_limiting': {
                'available': True,
                'limit_per_minute': get_messaging_service().rate_limit_per_minute,
                'description': f'Rate limiting: {messaging_service.rate_limit_per_minute} messages per minute'
            },
            'encryption': {
                'available': True,
                'description': 'End-to-end message encryption'
            }
        }
        
        overall_available = all(feature['available'] for feature in features_status.values())
        
        return jsonify({
            'success': True,
            'data': {
                'overall_available': overall_available,
                'features': features_status,
                'limits': {
                    'max_message_length': get_messaging_service().max_message_length,
                    'max_file_size_mb': get_messaging_service().max_file_size,
                    'message_retention_days': get_messaging_service().message_retention_days,
                    'rate_limit_per_minute': get_messaging_service().rate_limit_per_minute
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting messaging features status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Unable to get messaging features status'
        }), 500

# Error handlers
@messaging_bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limiting"""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@messaging_bp.errorhandler(400)
def bad_request_handler(e):
    """Handle bad requests"""
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'Invalid request parameters'
    }), 400

@messaging_bp.errorhandler(401)
def unauthorized_handler(e):
    """Handle unauthorized requests"""
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication required'
    }), 401

@messaging_bp.errorhandler(403)
def forbidden_handler(e):
    """Handle forbidden requests"""
    return jsonify({
        'success': False,
        'error': 'Forbidden',
        'message': 'Access denied to this resource'
    }), 403

@messaging_bp.errorhandler(404)
def not_found_handler(e):
    """Handle not found requests"""
    return jsonify({
        'success': False,
        'error': 'Not found',
        'message': 'Resource not found'
    }), 404

@messaging_bp.errorhandler(500)
def internal_error_handler(e):
    """Handle internal server errors"""
    current_app.logger.error(f"Messaging API internal server error: {str(e)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'Something went wrong. Please try again later.'
    }), 500
