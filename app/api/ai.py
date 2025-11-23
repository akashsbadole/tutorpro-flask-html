"""
AI API endpoints for TutorPro Marketplace
Provides RESTful API for AI-powered features
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.ai_service import AIService
from app.utils.decorators import rate_limit
import json
from datetime import datetime

# Create blueprint
ai_bp = Blueprint('ai_api', __name__, url_prefix='/api/ai')

# Initialize AI service (lazy initialization)
ai_service = None

def get_ai_service():
    """Get AI service instance with app context"""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service

@ai_bp.route('/recommendations/tutors', methods=['GET'])
@jwt_required()
@rate_limit(limit=10, period=3600)  # 10 requests per hour
def get_tutor_recommendations():
    """
    Get AI-powered tutor recommendations for the current student
    
    Query Parameters:
    - limit: Maximum number of recommendations (default: 10)
    """
    try:
        user_id = get_jwt_identity()
        limit = min(20, max(1, int(request.args.get('limit', 10))))
        
        ai_service = get_ai_service()
        recommendations = ai_service.get_tutor_recommendations(user_id, limit)
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'message': f"Found {len(recommendations)} personalized tutor recommendations"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting tutor recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Unable to get recommendations'
        }), 500

@ai_bp.route('/translate', methods=['POST'])
@jwt_required()
@rate_limit(limit=50, period=3600)  # 50 requests per hour
def translate_text():
    """
    Translate text using AI translation service
    
    Request Body:
    - text: Text to translate
    - target_language: Target language code (e.g., 'es', 'hi', 'fr')
    - source_language: Source language code (optional, default: auto-detect)
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('text'):
            return jsonify({
                'success': False,
                'error': 'Text is required for translation'
            }), 400
        
        if not data.get('target_language'):
            return jsonify({
                'success': False,
                'error': 'Target language is required'
            }), 400
        
        text = data['text']
        target_language = data['target_language']
        source_language = data.get('source_language', 'auto')
        
        # Validate text length
        if len(text) > 5000:
            return jsonify({
                'success': False,
                'error': 'Text too long. Maximum 5000 characters allowed.'
            }), 400
        
        ai_service = get_ai_service()
        result = ai_service.translate_text(text, target_language, source_language)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'original_text': text,
                    'translated_text': result['translated_text'],
                    'detected_language': result.get('detected_language'),
                    'source_language': result.get('source_language'),
                    'target_language': target_language
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error translating text: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Translation service unavailable'
        }), 500

@ai_bp.route('/summary/lesson', methods=['POST'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def generate_lesson_summary():
    """
    Generate AI-powered lesson summary
    
    Request Body:
    - session_content: Transcript or content of the tutoring session
    - subject: Subject area for context (optional)
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('session_content'):
            return jsonify({
                'success': False,
                'error': 'Session content is required'
            }), 400
        
        session_content = data['session_content']
        subject = data.get('subject')
        
        # Validate content length
        if len(session_content) < 50:
            return jsonify({
                'success': False,
                'error': 'Session content too short. Minimum 50 characters required.'
            }), 400
        
        if len(session_content) > 10000:
            return jsonify({
                'success': False,
                'error': 'Session content too long. Maximum 10000 characters allowed.'
            }), 400
        
        ai_service = get_ai_service()
        result = ai_service.generate_lesson_summary(session_content, subject)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'summary': result['summary'],
                    'key_topics': result.get('key_topics', []),
                    'main_concepts': result.get('main_concepts', []),
                    'practice_exercises': result.get('practice_exercises', []),
                    'homework': result.get('homework', []),
                    'next_steps': result.get('next_steps', []),
                    'generated_at': datetime.utcnow().isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error generating lesson summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Lesson summary generation failed'
        }), 500

@ai_bp.route('/plagiarism/check', methods=['POST'])
@jwt_required()
@rate_limit(limit=10, period=3600)  # 10 requests per hour
def check_plagiarism():
    """
    Check text for plagiarism using AI analysis
    
    Request Body:
    - text: Text to check for plagiarism
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('text'):
            return jsonify({
                'success': False,
                'error': 'Text is required for plagiarism check'
            }), 400
        
        text = data['text']
        
        # Validate text length
        if len(text) < 100:
            return jsonify({
                'success': False,
                'error': 'Text too short. Minimum 100 characters required.'
            }), 400
        
        if len(text) > 5000:
            return jsonify({
                'success': False,
                'error': 'Text too long. Maximum 5000 characters allowed.'
            }), 400
        
        ai_service = get_ai_service()
        result = ai_service.check_plagiarism(text)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'plagiarism_score': result['plagiarism_score'],
                    'uniqueness_score': result['uniqueness_score'],
                    'is_suspicious': result['is_suspicious'],
                    'suspicious_phrases_found': result['suspicious_phrases_found'],
                    'recommendation': result['recommendation'],
                    'checked_at': datetime.utcnow().isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error checking plagiarism: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Plagiarism check failed'
        }), 500
    

@ai_bp.route('/transcribe', methods=['POST'])
@jwt_required()
@rate_limit(limit=5, period=3600)  # 5 requests per hour
def transcribe_audio():
    """
    Generate transcript from audio file (placeholder implementation)
    
    Request Body:
    - audio_file_path: Path to audio file to transcribe
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('audio_file_path'):
            return jsonify({
                'success': False,
                'error': 'Audio file path is required'
            }), 400
        
        audio_file_path = data['audio_file_path']
        
        ai_service = get_ai_service()
        result = ai_service.generate_session_transcript(audio_file_path)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'transcript': result['transcript'],
                    'audio_file_path': audio_file_path,
                    'transcribed_at': datetime.utcnow().isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Transcription failed')
            }), 501  # Service not implemented
            
    except Exception as e:
        current_app.logger.error(f"Error transcribing audio: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Audio transcription failed'
        }), 500

@ai_bp.route('/match/score', methods=['POST'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def calculate_match_score():
    """
    Calculate AI-powered match score between student and tutor
    
    Request Body:
    - tutor_id: Tutor ID to calculate match score with
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('tutor_id'):
            return jsonify({
                'success': False,
                'error': 'Tutor ID is required'
            }), 400
        
        tutor_id = data['tutor_id']
        
        # Get AI recommendations and find the specific tutor
        ai_service = get_ai_service()
        recommendations = ai_service.get_tutor_recommendations(user_id, 50)
        
        target_recommendation = None
        for rec in recommendations:
            if rec['tutor_id'] == tutor_id:
                target_recommendation = rec
                break
        
        if target_recommendation:
            return jsonify({
                'success': True,
                'data': {
                    'tutor_id': tutor_id,
                    'match_score': target_recommendation['score'],
                    'match_reasons': target_recommendation['reasons'],
                    'calculated_at': datetime.utcnow().isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Tutor not found or not eligible for matching'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Error calculating match score: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Match score calculation failed'
        }), 500

@ai_bp.route('/languages/supported', methods=['GET'])
@jwt_required()
def get_supported_languages():
    """
    Get list of supported languages for translation
    """
    try:
        # Return common supported languages
        supported_languages = {
            'auto': {'name': 'Auto-detect', 'code': 'auto'},
            'en': {'name': 'English', 'code': 'en'},
            'es': {'name': 'Spanish', 'code': 'es'},
            'fr': {'name': 'French', 'code': 'fr'},
            'de': {'name': 'German', 'code': 'de'},
            'it': {'name': 'Italian', 'code': 'it'},
            'pt': {'name': 'Portuguese', 'code': 'pt'},
            'ru': {'name': 'Russian', 'code': 'ru'},
            'ja': {'name': 'Japanese', 'code': 'ja'},
            'ko': {'name': 'Korean', 'code': 'ko'},
            'zh': {'name': 'Chinese', 'code': 'zh'},
            'hi': {'name': 'Hindi', 'code': 'hi'},
            'ar': {'name': 'Arabic', 'code': 'ar'},
            'bn': {'name': 'Bengali', 'code': 'bn'},
            'ta': {'name': 'Tamil', 'code': 'ta'},
            'te': {'name': 'Telugu', 'code': 'te'},
            'mr': {'name': 'Marathi', 'code': 'mr'}
        }
        
        return jsonify({
            'success': True,
            'data': supported_languages
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting supported languages: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Unable to get supported languages'
        }), 500

@ai_bp.route('/features/status', methods=['GET'])
@jwt_required()
def get_ai_features_status():
    """
    Get status of AI features and services
    """
    try:
        # Check configuration status of AI services
        openai_configured = bool(current_app.config.get('OPENAI_API_KEY'))
        translate_configured = bool(current_app.config.get('GOOGLE_TRANSLATE_API_KEY'))
        
        features_status = {
            'tutor_recommendations': {
                'available': True,
                'description': 'AI-powered tutor matching based on learning goals, schedule, and preferences'
            },
            'translation': {
                'available': translate_configured,
                'description': 'Real-time text translation between multiple languages',
                'configured': translate_configured
            },
            'lesson_summary': {
                'available': openai_configured,
                'description': 'AI-generated lesson summaries and key points',
                'configured': openai_configured
            },
            'plagiarism_detection': {
                'available': True,
                'description': 'Basic plagiarism detection for assignments and content'
            },
            'audio_transcription': {
                'available': False,
                'description': 'Audio-to-text transcription for sessions (requires configuration)',
                'configured': False
            }
        }
        
        overall_available = any(feature['available'] for feature in features_status.values())
        
        return jsonify({
            'success': True,
            'data': {
                'overall_available': overall_available,
                'features': features_status,
                'api_keys_configured': {
                    'openai': openai_configured,
                    'google_translate': translate_configured
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting AI features status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Unable to get AI features status'
        }), 500

# Error handlers
@ai_bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limiting"""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@ai_bp.errorhandler(400)
def bad_request_handler(e):
    """Handle bad requests"""
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'Invalid request parameters'
    }), 400

@ai_bp.errorhandler(401)
def unauthorized_handler(e):
    """Handle unauthorized requests"""
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication required'
    }), 401

@ai_bp.errorhandler(500)
def internal_error_handler(e):
    """Handle internal server errors"""
    current_app.logger.error(f"AI API internal server error: {str(e)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'Something went wrong. Please try again later.'
    }), 500
