"""
Video Classroom API endpoints for TutorPro Marketplace
Provides RESTful API for enhanced video calling features
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.video_classroom_service import VideoClassroomService
from app.utils.decorators import rate_limit
from datetime import datetime
import json

# Create blueprint
video_classroom_bp = Blueprint('video_classroom_api', __name__, url_prefix='/api/video-classroom')

# Initialize video classroom service (lazy initialization)
video_service = None

def get_video_service():
    """Get video classroom service instance with app context"""
    global video_service
    if video_service is None:
        video_service = VideoClassroomService()
    return video_service

@video_classroom_bp.route('/session/create/<int:meeting_id>', methods=['POST'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def create_meeting_session(meeting_id):
    """
    Create video meeting session with enhanced features
    
    Path Parameters:
    - meeting_id: Meeting ID to create session for
    """
    try:
        user_id = get_jwt_identity()
        
        # Verify user is host of the meeting
        from app.models.meeting import Meeting
        meeting = Meeting.query.get(meeting_id)
        if not meeting or meeting.host_id != user_id:
            return jsonify({
                'success': False,
                'error': 'Meeting not found or access denied'
            }), 404
        
        result = video_service.create_meeting_session(meeting_id, user_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['session']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error creating meeting session: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create meeting session'
        }), 500

@video_classroom_bp.route('/screen-share/token', methods=['POST'])
@jwt_required()
@rate_limit(limit=30, period=3600)  # 30 requests per hour
def generate_screen_share_token():
    """
    Generate token for screen sharing
    
    Request Body:
    - session_id: Video session ID
    - permission_level: Permission level (view, share, control)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('session_id'):
            return jsonify({
                'success': False,
                'error': 'Session ID is required'
            }), 400
        
        session_id = data['session_id']
        permission_level = data.get('permission_level', 'view')
        
        result = video_service.generate_screen_share_token(session_id, user_id, permission_level)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'token': result['token'],
                    'permission_level': result['permission_level'],
                    'expires_at': result['expires_at']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error generating screen share token: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate screen sharing token'
        }), 500

@video_classroom_bp.route('/screen-share/start', methods=['POST'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def start_screen_sharing():
    """
    Start screen sharing session
    
    Request Body:
    - session_id: Video session ID
    - config: Screen sharing configuration (optional)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('session_id'):
            return jsonify({
                'success': False,
                'error': 'Session ID is required'
            }), 400
        
        session_id = data['session_id']
        screen_config = data.get('config')
        
        result = video_service.start_screen_sharing(session_id, user_id, screen_config)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['screen_session']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error starting screen sharing: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to start screen sharing'
        }), 500

@video_classroom_bp.route('/screen-share/stop', methods=['POST'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def stop_screen_sharing():
    """
    Stop screen sharing session
    
    Request Body:
    - session_id: Video session ID
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('session_id'):
            return jsonify({
                'success': False,
                'error': 'Session ID is required'
            }), 400
        
        session_id = data['session_id']
        
        result = video_service.stop_screen_sharing(session_id, user_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'stopped_at': result['stopped_at'],
                    'message': result['message']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error stopping screen sharing: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to stop screen sharing'
        }), 500

@video_classroom_bp.route('/whiteboard/<session_id>', methods=['GET'])
@jwt_required()
@rate_limit(limit=50, period=3600)  # 50 requests per hour
def get_whiteboard_data(session_id):
    """
    Get whiteboard data for collaboration
    
    Path Parameters:
    - session_id: Video session ID
    """
    try:
        user_id = get_jwt_identity()
        
        # Verify user is part of the session
        # In production, you would check session participants
        
        result = video_service.get_whiteboard_data(session_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['whiteboard']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error getting whiteboard data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get whiteboard data'
        }), 500

@video_classroom_bp.route('/whiteboard/element', methods=['POST'])
@jwt_required()
@rate_limit(limit=100, period=3600)  # 100 requests per hour
def save_whiteboard_element():
    """
    Save whiteboard element
    
    Request Body:
    - session_id: Video session ID
    - element_data: Element data (type, coordinates, content, etc.)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('session_id') or not data.get('element_data'):
            return jsonify({
                'success': False,
                'error': 'Session ID and element data are required'
            }), 400
        
        session_id = data['session_id']
        element_data = data['element_data']
        
        result = video_service.save_whiteboard_element(session_id, user_id, element_data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['element']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error saving whiteboard element: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to save whiteboard element'
        }), 500

@video_classroom_bp.route('/file/share', methods=['POST'])
@jwt_required()
@rate_limit(limit=30, period=3600)  # 30 requests per hour
def handle_file_share():
    """
    Handle file sharing in video session
    
    Request Body:
    - session_id: Video session ID
    - file_data: File information
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('session_id') or not data.get('file_data'):
            return jsonify({
                'success': False,
                'error': 'Session ID and file data are required'
            }), 400
        
        session_id = data['session_id']
        file_data = data['file_data']
        
        result = video_service.handle_file_share(session_id, user_id, file_data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['file_share']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error handling file share: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to share file'
        }), 500

@video_classroom_bp.route('/breakout-room/create', methods=['POST'])
@jwt_required()
@rate_limit(limit=10, period=3600)  # 10 requests per hour
def create_breakout_room():
    """
    Create breakout room for group activities
    
    Request Body:
    - session_id: Main session ID
    - room_config: Breakout room configuration
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('session_id') or not data.get('room_config'):
            return jsonify({
                'success': False,
                'error': 'Session ID and room configuration are required'
            }), 400
        
        session_id = data['session_id']
        room_config = data['room_config']
        
        result = video_service.create_breakout_room(session_id, room_config)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['breakout_room']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error creating breakout room: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create breakout room'
        }), 500

@video_classroom_bp.route('/poll/create', methods=['POST'])
@jwt_required()
@rate_limit(limit=15, period=3600)  # 15 requests per hour
def create_poll():
    """
    Create interactive poll for session
    
    Request Body:
    - session_id: Video session ID
    - poll_data: Poll configuration
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('session_id') or not data.get('poll_data'):
            return jsonify({
                'success': False,
                'error': 'Session ID and poll data are required'
            }), 400
        
        session_id = data['session_id']
        poll_data = data['poll_data']
        
        result = video_service.create_poll(session_id, user_id, poll_data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['poll']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error creating poll: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create poll'
        }), 500

@video_classroom_bp.route('/analytics/<session_id>', methods=['GET'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def get_session_analytics(session_id):
    """
    Get analytics data for video session
    
    Path Parameters:
    - session_id: Video session ID
    """
    try:
        user_id = get_jwt_identity()
        
        # Verify user has permission to view analytics
        # In production, you would check if user is host or admin
        
        result = video_service.get_session_analytics(session_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['analytics']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error getting session analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get session analytics'
        }), 500

@video_classroom_bp.route('/session/end', methods=['POST'])
@jwt_required()
@rate_limit(limit=10, period=3600)  # 10 requests per hour
def end_session():
    """
    End video session and clean up resources
    
    Request Body:
    - session_id: Video session ID
    - end_reason: Reason for ending session (optional)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('session_id'):
            return jsonify({
                'success': False,
                'error': 'Session ID is required'
            }), 400
        
        session_id = data['session_id']
        end_reason = data.get('end_reason')
        
        result = video_service.end_session(session_id, end_reason)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['session_end']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error ending session: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to end session'
        }), 500

@video_classroom_bp.route('/features/status', methods=['GET'])
@jwt_required()
def get_video_features_status():
    """
    Get status of video classroom features
    """
    try:
        features_status = {
            'screen_sharing': {
                'available': video_service.screen_sharing_enabled,
                'description': 'Real-time screen sharing with quality controls'
            },
            'whiteboard': {
                'available': True,
                'description': 'Collaborative whiteboard with drawing tools'
            },
            'file_sharing': {
                'available': True,
                'description': 'Secure file sharing during sessions'
            },
            'breakout_rooms': {
                'available': True,
                'description': 'Create breakout rooms for group activities'
            },
            'polls': {
                'available': True,
                'description': 'Interactive polls and surveys'
            },
            'hand_raising': {
                'available': True,
                'description': 'Virtual hand raising for attention management'
            },
            'emoji_reactions': {
                'available': True,
                'description': 'Emoji reactions for engagement'
            },
            'recording': {
                'available': True,
                'description': 'Session recording capability'
            },
            'analytics': {
                'available': True,
                'description': 'Real-time session analytics'
            }
        }
        
        overall_available = all(feature['available'] for feature in features_status.values())
        
        return jsonify({
            'success': True,
            'data': {
                'overall_available': overall_available,
                'features': features_status,
                'limits': {
                    'max_participants': video_service.max_participants,
                    'session_timeout_hours': video_service.session_timeout // 3600,
                    'max_file_size_mb': 100,
                    'screen_sharing_duration_limit': 3600
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting video features status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Unable to get video features status'
        }), 500

# Error handlers
@video_classroom_bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limiting"""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@video_classroom_bp.errorhandler(400)
def bad_request_handler(e):
    """Handle bad requests"""
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'Invalid request parameters'
    }), 400

@video_classroom_bp.errorhandler(401)
def unauthorized_handler(e):
    """Handle unauthorized requests"""
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication required'
    }), 401

@video_classroom_bp.errorhandler(404)
def not_found_handler(e):
    """Handle not found requests"""
    return jsonify({
        'success': False,
        'error': 'Not found',
        'message': 'Resource not found'
    }), 404

@video_classroom_bp.errorhandler(500)
def internal_error_handler(e):
    """Handle internal server errors"""
    current_app.logger.error(f"Video Classroom API internal server error: {str(e)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'Something went wrong. Please try again later.'
    }), 500
