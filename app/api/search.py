"""
Search API endpoints for TutorPro Marketplace
Provides RESTful API for tutor discovery and search
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.search_service import SearchService
from app.models.category import SubjectCategory, Subject
from app.models.user import User
from app.utils.decorators import rate_limit
import json
from datetime import datetime

# Create blueprint
search_bp = Blueprint('search_api', __name__, url_prefix='/api/search')

# Initialize search service
search_service = SearchService()

@search_bp.route('/tutors', methods=['GET'])
@rate_limit(limit=100, period=3600)  # 100 requests per hour
def search_tutors():
    """
    Search tutors with advanced filtering
    
    Query Parameters:
    - query: Text search query
    - location: Location text or lat/lng coordinates
    - latitude: Latitude for location search
    - longitude: Longitude for location search
    - radius_km: Search radius in kilometers (default: 50)
    - category_ids: Comma-separated category IDs
    - subject_ids: Comma-separated subject IDs
    - price_min: Minimum hourly rate
    - price_max: Maximum hourly rate
    - min_rating: Minimum rating (1-5)
    - available_now: Filter tutors available now (true/false)
    - available_days: Comma-separated days (Monday, Tuesday, etc.)
    - teaching_modes: Comma-separated modes (Online, Offline, Hybrid)
    - age_groups: Comma-separated age groups
    - languages: Comma-separated languages
    - verified_only: Show only verified tutors (true/false)
    - background_checked_only: Show only background checked tutors (true/false)
    - min_experience_years: Minimum years of experience
    - offers_trial: Show tutors offering free trial (true/false)
    - accepts_group_sessions: Show tutors accepting groups (true/false)
    - sort_by: Sort by relevance, rating, price_low, price_high, experience, reviews, newest, availability
    - sort_order: Sort order asc/desc
    - page: Page number (default: 1)
    - per_page: Results per page (default: 20, max: 100)
    """
    try:
        # Get search parameters
        search_params = request.args.to_dict()
        
        # Convert boolean parameters
        bool_params = ['available_now', 'verified_only', 'background_checked_only', 
                      'offers_trial', 'accepts_group_sessions']
        for param in bool_params:
            if param in search_params:
                search_params[param] = search_params[param].lower() in ['true', '1', 'yes']
        
        # Convert list parameters
        list_params = ['category_ids', 'subject_ids', 'available_days', 'teaching_modes', 
                     'age_groups', 'languages']
        for param in list_params:
            if param in search_params:
                search_params[param] = [item.strip() for item in search_params[param].split(',') if item.strip()]
        
        # Perform search
        results = search_service.search_tutors(search_params)
        
        return jsonify({
            'success': True,
            'data': results,
            'message': f"Found {results['pagination']['total']} tutors matching your criteria"
        })
        
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Search service temporarily unavailable',
            'message': 'Please try again later'
        }), 500

@search_bp.route('/suggestions', methods=['GET'])
@rate_limit(limit=50, period=3600)  # 50 requests per hour
def search_suggestions():
    """
    Get search suggestions for autocomplete
    
    Query Parameters:
    - q: Search query
    - limit: Number of suggestions to return (default: 10)
    """
    try:
        query = request.args.get('q', '').strip()
        limit = min(20, max(1, int(request.args.get('limit', 10))))
        
        if not query or len(query) < 2:
            return jsonify({
                'success': True,
                'data': {'subjects': [], 'tutors': []}
            })
        
        suggestions = search_service.get_search_suggestions(query, limit)
        
        return jsonify({
            'success': True,
            'data': suggestions
        })
        
    except Exception as e:
        current_app.logger.error(f"Suggestions error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Suggestions temporarily unavailable'
        }), 500

@search_bp.route('/popular', methods=['GET'])
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def popular_searches():
    """
    Get popular search terms
    
    Query Parameters:
    - limit: Number of popular terms to return (default: 20)
    """
    try:
        limit = min(50, max(1, int(request.args.get('limit', 20))))
        
        popular_terms = search_service.get_popular_searches(limit)
        
        return jsonify({
            'success': True,
            'data': popular_terms
        })
        
    except Exception as e:
        current_app.logger.error(f"Popular searches error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Popular searches temporarily unavailable'
        }), 500

@search_bp.route('/categories', methods=['GET'])
@rate_limit(limit=30, period=3600)  # 30 requests per hour
def get_categories():
    """
    Get all subject categories with subjects
    
    Query Parameters:
    - featured_only: Return only featured categories (true/false)
    - parent_id: Filter by parent category ID
    """
    try:
        featured_only = request.args.get('featured_only', '').lower() in ['true', '1', 'yes']
        parent_id = request.args.get('parent_id')
        
        # Build query
        query = SubjectCategory.query.filter_by(is_active=True)
        
        if featured_only:
            query = query.filter_by(is_featured=True)
        
        if parent_id:
            query = query.filter_by(parent_id=int(parent_id))
        else:
            query = query.filter(SubjectCategory.parent_id.is_(None))
        
        # Order by sort order
        query = query.order_by(SubjectCategory.sort_order, SubjectCategory.name)
        
        categories = query.all()
        
        # Build response with subjects
        result = []
        for category in categories:
            category_data = category.to_dict()
            
            # Get child categories
            child_categories = SubjectCategory.query.filter_by(
                parent_id=category.id, is_active=True
            ).order_by(SubjectCategory.sort_order, SubjectCategory.name).all()
            
            if child_categories:
                category_data['children'] = [child.to_dict() for child in child_categories]
                
                # Get subjects for each child category
                for child in category_data['children']:
                    subjects = Subject.query.filter_by(
                        category_id=child['id'], is_active=True
                    ).order_by(Subject.sort_order, Subject.name).all()
                    child['subjects'] = [subject.to_dict() for subject in subjects]
                    child['subject_count'] = len(subjects)
            else:
                # Get subjects directly for this category
                subjects = Subject.query.filter_by(
                    category_id=category.id, is_active=True
                ).order_by(Subject.sort_order, Subject.name).all()
                category_data['subjects'] = [subject.to_dict() for subject in subjects]
                category_data['subject_count'] = len(subjects)
            
            result.append(category_data)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Categories error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Categories temporarily unavailable'
        }), 500

@search_bp.route('/subjects', methods=['GET'])
@rate_limit(limit=50, period=3600)  # 50 requests per hour
def get_subjects():
    """
    Get subjects with filtering options
    
    Query Parameters:
    - category_id: Filter by category ID
    - popular_only: Return only popular subjects (true/false)
    - difficulty_level: Filter by difficulty level
    - limit: Number of subjects to return
    """
    try:
        category_id = request.args.get('category_id')
        popular_only = request.args.get('popular_only', '').lower() in ['true', '1', 'yes']
        difficulty_level = request.args.get('difficulty_level')
        limit = request.args.get('limit')
        
        # Build query
        query = Subject.query.filter_by(is_active=True)
        
        if category_id:
            query = query.filter_by(category_id=int(category_id))
        
        if popular_only:
            query = query.filter_by(is_popular=True)
        
        if difficulty_level:
            query = query.filter_by(difficulty_level=difficulty_level)
        
        # Order by sort order and name
        query = query.order_by(Subject.sort_order, Subject.name)
        
        if limit:
            query = query.limit(min(100, max(1, int(limit))))
        
        subjects = query.all()
        
        return jsonify({
            'success': True,
            'data': [subject.to_dict() for subject in subjects]
        })
        
    except Exception as e:
        current_app.logger.error(f"Subjects error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Subjects temporarily unavailable'
        }), 500

@search_bp.route('/filters', methods=['GET'])
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def get_search_filters():
    """
    Get available search filter options
    Returns all possible filter values for search interface
    """
    try:
        # Get categories
        categories = SubjectCategory.query.filter_by(
            is_active=True, parent_id=None
        ).order_by(SubjectCategory.sort_order, SubjectCategory.name).all()
        
        # Get teaching modes
        teaching_modes = ['Online', 'Offline', 'Hybrid']
        
        # Get age groups
        age_groups = ['Elementary', 'Middle School', 'High School', 'College', 'Adult']
        
        # Get experience levels
        experience_levels = ['Beginner', 'Intermediate', 'Advanced', 'Expert']
        
        # Get price ranges
        price_ranges = [
            {'min': 0, 'max': 25, 'label': 'Under $25'},
            {'min': 25, 'max': 50, 'label': '$25 - $50'},
            {'min': 50, 'max': 75, 'label': '$50 - $75'},
            {'min': 75, 'max': 100, 'label': '$75 - $100'},
            {'min': 100, 'max': None, 'label': '$100+'}
        ]
        
        # Get days of week
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Get popular languages
        languages = [
            'English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese',
            'Hindi', 'Tamil', 'Telugu', 'Bengali', 'Marathi', 'Arabic'
        ]
        
        filters = {
            'categories': [cat.to_dict() for cat in categories],
            'teaching_modes': teaching_modes,
            'age_groups': age_groups,
            'experience_levels': experience_levels,
            'price_ranges': price_ranges,
            'days_of_week': days_of_week,
            'languages': languages,
            'rating_levels': [
                {'value': 4.5, 'label': '4.5+ Stars'},
                {'value': 4.0, 'label': '4.0+ Stars'},
                {'value': 3.5, 'label': '3.5+ Stars'},
                {'value': 3.0, 'label': '3.0+ Stars'}
            ]
        }
        
        return jsonify({
            'success': True,
            'data': filters
        })
        
    except Exception as e:
        current_app.logger.error(f"Filters error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Filters temporarily unavailable'
        }), 500

@search_bp.route('/save-search', methods=['POST'])
@jwt_required()
@rate_limit(limit=10, period=3600)  # 10 requests per hour
def save_search():
    """
    Save a search for the authenticated user
    
    Request Body:
    - name: Search name
    - query: Search parameters (JSON)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Search name is required'
            }), 400
        
        # This would save to a saved_searches table
        # For now, return success response
        
        return jsonify({
            'success': True,
            'message': 'Search saved successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Save search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to save search'
        }), 500

@search_bp.route('/saved-searches', methods=['GET'])
@jwt_required()
@rate_limit(limit=20, period=3600)  # 20 requests per hour
def get_saved_searches():
    """
    Get saved searches for the authenticated user
    """
    try:
        user_id = get_jwt_identity()
        
        # This would query saved_searches table
        # For now, return empty response
        
        return jsonify({
            'success': True,
            'data': []
        })
        
    except Exception as e:
        current_app.logger.error(f"Saved searches error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get saved searches'
        }), 500

@search_bp.route('/analytics', methods=['POST'])
@rate_limit(limit=5, period=3600)  # 5 requests per hour
def log_search_analytics():
    """
    Log search analytics (internal use)
    
    Request Body:
    - query: Search query
    - filters: Applied filters
    - results_count: Number of results
    - user_id: User ID (if authenticated)
    - session_id: Session identifier
    - timestamp: Search timestamp
    """
    try:
        data = request.get_json()
        
        # Log search analytics
        current_app.logger.info(f"Search analytics: {json.dumps(data)}")
        
        # This would save to search_analytics table
        # For now, just log the data
        
        return jsonify({
            'success': True,
            'message': 'Analytics logged'
        })
        
    except Exception as e:
        current_app.logger.error(f"Analytics error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to log analytics'
        }), 500

# Error handlers
@search_bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limiting"""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@search_bp.errorhandler(400)
def bad_request_handler(e):
    """Handle bad requests"""
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'Invalid request parameters'
    }), 400

@search_bp.errorhandler(500)
def internal_error_handler(e):
    """Handle internal server errors"""
    current_app.logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'Something went wrong. Please try again later.'
    }), 500