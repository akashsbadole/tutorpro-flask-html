"""
Advanced Search Service for TutorPro Marketplace
Provides comprehensive search and filtering capabilities for tutor discovery
"""

from flask import current_app
from sqlalchemy import and_, or_, not_, func, desc, asc
from sqlalchemy.orm import joinedload, contains_eager
from app import db
from app.models.user import User
from app.models.tutor import TutorProfile, TutorSubject, TutorAvailability
from app.models.category import SubjectCategory, Subject
from app.models.verification import TutorRating, Review
from app.models.booking import Booking
from datetime import datetime, timedelta
import json
import math
from typing import Dict, List, Optional, Tuple

class SearchService:
    """Advanced search service for tutor discovery"""
    
    def __init__(self):
        self.default_page_size = 20
        self.max_page_size = 100
    
    def search_tutors(self, search_params: Dict) -> Dict:
        """
        Main search method with comprehensive filtering
        
        Args:
            search_params: Dictionary containing search criteria
            
        Returns:
            Dict with search results and metadata
        """
        # Parse and validate parameters
        params = self._parse_search_params(search_params)
        
        # Build base query
        query = self._build_base_query(params)
        
        # Apply filters
        query = self._apply_filters(query, params)
        
        # Apply search ranking
        query = self._apply_ranking(query, params)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        query = self._apply_pagination(query, params)
        
        # Execute query
        tutors = query.all()
        
        # Process results
        results = self._process_results(tutors, params)
        
        # Build response
        return {
            'tutors': results,
            'pagination': {
                'page': params['page'],
                'per_page': params['per_page'],
                'total': total_count,
                'pages': math.ceil(total_count / params['per_page']),
                'has_next': (params['page'] * params['per_page']) < total_count,
                'has_prev': params['page'] > 1
            },
            'search_params': params,
            'filters_applied': self._get_applied_filters(params),
            'search_time': datetime.utcnow().isoformat()
        }
    
    def _parse_search_params(self, search_params: Dict) -> Dict:
        """Parse and validate search parameters"""
        params = {
            # Text search
            'query': search_params.get('query', '').strip(),
            
            # Location
            'location': search_params.get('location', '').strip(),
            'latitude': search_params.get('latitude'),
            'longitude': search_params.get('longitude'),
            'radius_km': search_params.get('radius_km', 50),
            
            # Categories and subjects
            'category_ids': self._parse_list_param(search_params.get('category_ids')),
            'subject_ids': self._parse_list_param(search_params.get('subject_ids')),
            
            # Price range
            'price_min': self._parse_float_param(search_params.get('price_min')),
            'price_max': self._parse_float_param(search_params.get('price_max')),
            
            # Rating
            'min_rating': self._parse_float_param(search_params.get('min_rating')),
            
            # Availability
            'available_now': search_params.get('available_now', False),
            'available_days': self._parse_list_param(search_params.get('available_days')),
            'time_slot_start': search_params.get('time_slot_start'),
            'time_slot_end': search_params.get('time_slot_end'),
            
            # Teaching preferences
            'teaching_modes': self._parse_list_param(search_params.get('teaching_modes')),
            'age_groups': self._parse_list_param(search_params.get('age_groups')),
            'languages': self._parse_list_param(search_params.get('languages')),
            
            # Verification
            'verified_only': search_params.get('verified_only', False),
            'background_checked_only': search_params.get('background_checked_only', False),
            
            # Experience
            'min_experience_years': self._parse_int_param(search_params.get('min_experience_years')),
            
            # Session type
            'offers_trial': search_params.get('offers_trial', False),
            'accepts_group_sessions': search_params.get('accepts_group_sessions', False),
            
            # Sorting
            'sort_by': search_params.get('sort_by', 'relevance'),
            'sort_order': search_params.get('sort_order', 'desc'),
            
            # Pagination
            'page': max(1, self._parse_int_param(search_params.get('page', 1))),
            'per_page': min(self.max_page_size, max(1, self._parse_int_param(search_params.get('per_page', self.default_page_size))))
        }
        
        return params
    
    def _parse_list_param(self, param) -> List:
        """Parse list parameters from various input formats"""
        if not param:
            return []
        
        if isinstance(param, list):
            return [str(item).strip() for item in param if str(item).strip()]
        
        if isinstance(param, str):
            # Handle comma-separated strings
            return [item.strip() for item in param.split(',') if item.strip()]
        
        return []
    
    def _parse_float_param(self, param) -> Optional[float]:
        """Parse float parameter safely"""
        try:
            return float(param) if param is not None else None
        except (ValueError, TypeError):
            return None
    
    def _parse_int_param(self, param) -> Optional[int]:
        """Parse integer parameter safely"""
        try:
            return int(param) if param is not None else None
        except (ValueError, TypeError):
            return None
    
    def _build_base_query(self, params: Dict):
        """Build base query with essential joins"""
        query = db.session.query(TutorProfile).join(User).filter(
            and_(
                User.role == 'Tutor',
                TutorProfile.is_active == True,
                User.is_active == True
            )
        )
        
        # Eager load related data
        query = query.options(
            joinedload(TutorProfile.user),
            joinedload(TutorProfile.subjects),
            joinedload(TutorProfile.rating_summary),
            joinedload(TutorProfile.certifications)
        )
        
        return query
    
    def _apply_filters(self, query, params: Dict):
        """Apply all filters to the query"""
        
        # Text search
        if params['query']:
            query = self._apply_text_search(query, params['query'])
        
        # Location filter
        if params['location'] or (params['latitude'] and params['longitude']):
            query = self._apply_location_filter(query, params)
        
        # Category and subject filters
        if params['category_ids']:
            query = self._apply_category_filter(query, params['category_ids'])
        
        if params['subject_ids']:
            query = self._apply_subject_filter(query, params['subject_ids'])
        
        # Price range filter
        if params['price_min'] is not None or params['price_max'] is not None:
            query = self._apply_price_filter(query, params['price_min'], params['price_max'])
        
        # Rating filter
        if params['min_rating'] is not None:
            query = self._apply_rating_filter(query, params['min_rating'])
        
        # Availability filters
        if params['available_now']:
            query = self._apply_availability_now_filter(query)
        
        if params['available_days']:
            query = self._apply_availability_days_filter(query, params['available_days'])
        
        # Teaching mode filter
        if params['teaching_modes']:
            query = self._apply_teaching_mode_filter(query, params['teaching_modes'])
        
        # Age group filter
        if params['age_groups']:
            query = self._apply_age_group_filter(query, params['age_groups'])
        
        # Language filter
        if params['languages']:
            query = self._apply_language_filter(query, params['languages'])
        
        # Verification filters
        if params['verified_only']:
            query = query.filter(TutorProfile.is_verified == True)
        
        if params['background_checked_only']:
            query = query.filter(
                and_(
                    TutorProfile.background_check_status == 'Approved',
                    TutorProfile.background_check_expiry > datetime.utcnow()
                )
            )
        
        # Experience filter
        if params['min_experience_years'] is not None:
            query = self._apply_experience_filter(query, params['min_experience_years'])
        
        # Trial session filter
        if params['offers_trial']:
            query = query.filter(TutorProfile.offers_free_trial == True)
        
        # Group session filter
        if params['accepts_group_sessions']:
            query = query.filter(TutorProfile.max_group_size > 1)
        
        return query
    
    def _apply_text_search(self, query, search_query: str):
        """Apply text search across multiple fields"""
        search_terms = search_query.split()
        
        # Search in tutor profile fields
        conditions = []
        for term in search_terms:
            term_condition = or_(
                TutorProfile.title.ilike(f'%{term}%'),
                TutorProfile.tagline.ilike(f'%{term}%'),
                TutorProfile.description.ilike(f'%{term}%'),
                TutorProfile.bio.ilike(f'%{term}%'),
                User.user_profile.has(
                    or_(
                        User.user_profile.property.mapper.class_.first_name.ilike(f'%{term}%'),
                        User.user_profile.property.mapper.class_.last_name.ilike(f'%{term}%')
                    )
                )
            )
            conditions.append(term_condition)
        
        # Search in subjects
        subject_conditions = []
        for term in search_terms:
            subject_conditions.append(
                TutorProfile.subjects.any(
                    and_(
                        TutorSubject.is_active == True,
                        Subject.name.ilike(f'%{term}%')
                    )
                )
            )
        
        if subject_conditions:
            conditions.append(or_(*subject_conditions))
        
        return query.filter(or_(*conditions))
    
    def _apply_location_filter(self, query, params: Dict):
        """Apply location-based filtering"""
        if params['latitude'] and params['longitude']:
            # Use Haversine formula for distance calculation
            # This is a simplified version - in production, consider using PostGIS
            radius_km = params['radius_km']
            
            # Approximate degree conversion (1 degree ≈ 111 km)
            lat_delta = radius_km / 111.0
            lng_delta = radius_km / (111.0 * math.cos(math.radians(params['latitude'])))
            
            return query.filter(
                and_(
                    TutorProfile.latitude.isnot(None),
                    TutorProfile.longitude.isnot(None),
                    TutorProfile.latitude.between(params['latitude'] - lat_delta, params['latitude'] + lat_delta),
                    TutorProfile.longitude.between(params['longitude'] - lng_delta, params['longitude'] + lng_delta)
                )
            )
        elif params['location']:
            # Text-based location search
            return query.filter(
                or_(
                    TutorProfile.city.ilike(f'%{params["location"]}%'),
                    TutorProfile.state.ilike(f'%{params["location"]}%'),
                    TutorProfile.country.ilike(f'%{params["location"]}%')
                )
            )
        
        return query
    
    def _apply_category_filter(self, query, category_ids: List):
        """Apply category filtering"""
        return query.filter(
            TutorProfile.subjects.any(
                and_(
                    TutorSubject.is_active == True,
                    Subject.category_id.in_(category_ids)
                )
            )
        )
    
    def _apply_subject_filter(self, query, subject_ids: List):
        """Apply subject filtering"""
        return query.filter(
            TutorProfile.subjects.any(
                and_(
                    TutorSubject.is_active == True,
                    TutorSubject.subject_id.in_(subject_ids)
                )
            )
        )
    
    def _apply_price_filter(self, query, price_min: Optional[float], price_max: Optional[float]):
        """Apply price range filtering"""
        price_conditions = []
        
        if price_min is not None:
            price_conditions.append(
                or_(
                    TutorProfile.hourly_rate >= price_min,
                    TutorProfile.price_per_group_session >= price_min
                )
            )
        
        if price_max is not None:
            price_conditions.append(
                or_(
                    TutorProfile.hourly_rate <= price_max,
                    TutorProfile.price_per_group_session <= price_max
                )
            )
        
        if price_conditions:
            return query.filter(and_(*price_conditions))
        
        return query
    
    def _apply_rating_filter(self, query, min_rating: float):
        """Apply minimum rating filter"""
        return query.filter(TutorProfile.rating >= min_rating)
    
    def _apply_availability_now_filter(self, query):
        """Filter tutors available right now"""
        # This is a simplified check - in production, consider timezone handling
        current_day = datetime.utcnow().strftime('%A')
        current_time = datetime.utcnow().time()
        
        return query.filter(
            TutorProfile.availability_slots.any(
                and_(
                    TutorAvailability.is_available == True,
                    TutorAvailability.day_of_week == current_day,
                    TutorAvailability.start_time <= current_time,
                    TutorAvailability.end_time >= current_time
                )
            )
        )
    
    def _apply_availability_days_filter(self, query, available_days: List):
        """Filter by available days of week"""
        return query.filter(
            TutorProfile.availability_slots.any(
                and_(
                    TutorAvailability.is_available == True,
                    TutorAvailability.day_of_week.in_(available_days)
                )
            )
        )
    
    def _apply_teaching_mode_filter(self, query, teaching_modes: List):
        """Filter by teaching modes"""
        # Check if any of the requested modes are in the tutor's teaching modes
        mode_conditions = []
        for mode in teaching_modes:
            mode_conditions.append(TutorProfile.teaching_modes.like(f'%"{mode}"%'))
        
        return query.filter(or_(*mode_conditions))
    
    def _apply_age_group_filter(self, query, age_groups: List):
        """Filter by age groups taught"""
        group_conditions = []
        for group in age_groups:
            group_conditions.append(TutorProfile.age_groups_taught.like(f'%"{group}"%'))
        
        return query.filter(or_(*group_conditions))
    
    def _apply_language_filter(self, query, languages: List):
        """Filter by languages spoken"""
        language_conditions = []
        for language in languages:
            language_conditions.append(TutorProfile.languages_spoken.like(f'%"{language}"%'))
        
        return query.filter(or_(*language_conditions))
    
    def _apply_experience_filter(self, query, min_experience_years: int):
        """Filter by minimum experience"""
        return query.filter(
            or_(
                TutorProfile.subjects.any(TutorSubject.experience_years >= min_experience_years),
                TutorProfile.subjects.any(TutorSubject.teaching_experience_years >= min_experience_years)
            )
        )
    
    def _apply_ranking(self, query, params: Dict):
        """Apply sorting and ranking to results"""
        sort_by = params['sort_by']
        sort_order = desc if params['sort_order'] == 'desc' else asc
        
        if sort_by == 'relevance':
            # Default relevance ranking (can be enhanced with Elasticsearch)
            query = query.order_by(sort_order(TutorProfile.rating))
        elif sort_by == 'rating':
            query = query.order_by(sort_order(TutorProfile.rating))
        elif sort_by == 'price_low':
            query = query.order_by(asc(TutorProfile.hourly_rate))
        elif sort_by == 'price_high':
            query = query.order_by(desc(TutorProfile.hourly_rate))
        elif sort_by == 'experience':
            query = query.order_by(desc(func.coalesce(TutorProfile.total_hours_taught, 0)))
        elif sort_by == 'reviews':
            query = query.order_by(desc(func.coalesce(TutorProfile.total_reviews, 0)))
        elif sort_by == 'newest':
            query = query.order_by(desc(TutorProfile.created_at))
        elif sort_by == 'availability':
            # Sort by tutors with more availability slots
            query = query.outerjoin(TutorAvailability).group_by(TutorProfile.id).order_by(
                desc(func.count(TutorAvailability.id))
            )
        
        return query
    
    def _apply_pagination(self, query, params: Dict):
        """Apply pagination to query"""
        offset = (params['page'] - 1) * params['per_page']
        return query.offset(offset).limit(params['per_page'])
    
    def _process_results(self, tutors: List, params: Dict):
        """Process and enrich search results"""
        results = []
        
        for tutor in tutors:
            # Calculate distance if location search
            distance = None
            if params['latitude'] and params['longitude'] and tutor.latitude and tutor.longitude:
                distance = self._calculate_distance(
                    params['latitude'], params['longitude'],
                    tutor.latitude, tutor.longitude
                )
            
            # Get availability status
            available_now = tutor.is_available_now()
            
            # Build tutor data
            tutor_data = tutor.to_dict()
            tutor_data.update({
                'distance_km': round(distance, 2) if distance else None,
                'available_now': available_now,
                'search_score': self._calculate_search_score(tutor, params)
            })
            
            results.append(tutor_data)
        
        # Sort by search score if relevance sorting
        if params['sort_by'] == 'relevance':
            results.sort(key=lambda x: x['search_score'], reverse=True)
        
        return results
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 + 
               math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _calculate_search_score(self, tutor: TutorProfile, params: Dict) -> float:
        """Calculate search relevance score for tutor"""
        score = 0.0
        
        # Base score from rating
        score += (tutor.rating or 0) * 20
        
        # Verification bonus
        if tutor.is_verified:
            score += 10
        
        if tutor.background_check_status == 'Approved':
            score += 5
        
        # Experience bonus
        score += (tutor.total_hours_taught or 0) * 0.01
        
        # Review count bonus
        score += (tutor.total_reviews or 0) * 0.1
        
        # Featured tutor bonus
        if tutor.is_featured:
            score += 15
        
        # Availability bonus
        if tutor.is_available_now():
            score += 8
        
        # Price competitiveness (lower prices get bonus)
        if tutor.hourly_rate:
            avg_price = 50  # Could be calculated dynamically
            if tutor.hourly_rate < avg_price:
                score += (avg_price - float(tutor.hourly_rate)) * 0.1
        
        # Text relevance bonus (simplified)
        if params['query']:
            query_lower = params['query'].lower()
            text_fields = [
                (tutor.title or '').lower(),
                (tutor.tagline or '').lower(),
                (tutor.description or '').lower(),
                (tutor.bio or '').lower()
            ]
            
            for field in text_fields:
                if query_lower in field:
                    score += 5
        
        return round(score, 2)
    
    def _get_applied_filters(self, params: Dict) -> Dict:
        """Get list of applied filters for display"""
        applied = {}
        
        filter_mapping = {
            'query': 'Search Query',
            'location': 'Location',
            'category_ids': 'Categories',
            'subject_ids': 'Subjects',
            'price_min': 'Min Price',
            'price_max': 'Max Price',
            'min_rating': 'Min Rating',
            'teaching_modes': 'Teaching Modes',
            'age_groups': 'Age Groups',
            'languages': 'Languages',
            'verified_only': 'Verified Only',
            'background_checked_only': 'Background Checked',
            'offers_trial': 'Free Trial',
            'accepts_group_sessions': 'Group Sessions'
        }
        
        for key, label in filter_mapping.items():
            value = params.get(key)
            if value and (isinstance(value, bool) or 
                         (isinstance(value, list) and value) or 
                         (isinstance(value, (str, int, float)) and str(value).strip())):
                applied[key] = {
                    'label': label,
                    'value': value,
                    'display_value': self._format_filter_value(key, value)
                }
        
        return applied
    
    def _format_filter_value(self, key: str, value) -> str:
        """Format filter value for display"""
        if key in ['category_ids', 'subject_ids', 'teaching_modes', 'age_groups', 'languages']:
            if isinstance(value, list):
                return ', '.join(value)
        
        if key in ['price_min', 'price_max']:
            return f"${value}" if value else ""
        
        if key in ['verified_only', 'background_checked_only', 'offers_trial', 'accepts_group_sessions']:
            return "Yes" if value else "No"
        
        if key == 'min_rating':
            return f"{'⭐' * int(value)}" if value else ""
        
        return str(value)
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> Dict:
        """Get search suggestions for autocomplete"""
        if not query or len(query) < 2:
            return {'subjects': [], 'tutors': []}
        
        query_lower = query.lower()
        
        # Subject suggestions
        subjects = Subject.query.filter(
            and_(
                Subject.is_active == True,
                or_(
                    Subject.name.ilike(f'%{query}%'),
                    Subject.description.ilike(f'%{query}%')
                )
            )
        ).limit(limit).all()
        
        # Tutor suggestions
        tutors = TutorProfile.query.join(User).filter(
            and_(
                TutorProfile.is_active == True,
                User.role == 'Tutor',
                or_(
                    TutorProfile.title.ilike(f'%{query}%'),
                    TutorProfile.tagline.ilike(f'%{query}%'),
                    User.user_profile.has(
                        or_(
                            User.user_profile.property.mapper.class_.first_name.ilike(f'%{query}%'),
                            User.user_profile.property.mapper.class_.last_name.ilike(f'%{query}%')
                        )
                    )
                )
            )
        ).limit(limit).all()
        
        return {
            'subjects': [subject.to_dict() for subject in subjects],
            'tutors': [{'id': tutor.id, 'name': tutor.full_name, 'title': tutor.title} for tutor in tutors]
        }
    
    def get_popular_searches(self, limit: int = 20) -> List[Dict]:
        """Get popular search terms (could be implemented with analytics)"""
        # This would typically come from search analytics
        # For now, return static popular terms
        return [
            {'term': 'Mathematics', 'count': 1250},
            {'term': 'English', 'count': 980},
            {'term': 'Python Programming', 'count': 856},
            {'term': 'Guitar Lessons', 'count': 743},
            {'term': 'Physics', 'count': 698},
            {'term': 'Chemistry', 'count': 645},
            {'term': 'Spanish', 'count': 612},
            {'term': 'Web Development', 'count': 589},
            {'term': 'Piano', 'count': 567},
            {'term': 'French', 'count': 534}
        ][:limit]