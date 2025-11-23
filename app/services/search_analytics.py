"""
Search Analytics Service for TutorPro Marketplace
Tracks search performance, user behavior, and provides optimization insights
"""

from flask import current_app
from sqlalchemy import func, and_, or_, desc
from app import db
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.category import Subject, SubjectCategory
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import re

class SearchAnalytics:
    """Search analytics and optimization service"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes cache for popular searches
    
    def log_search(self, search_params: Dict, results_count: int, user_id: Optional[int] = None, session_id: Optional[str] = None):
        """
        Log search query for analytics
        
        Args:
            search_params: Search parameters used
            results_count: Number of results returned
            user_id: User ID if authenticated
            session_id: Session identifier for anonymous users
        """
        try:
            # Extract key search terms
            query = search_params.get('query', '').strip()
            filters_applied = self._extract_applied_filters(search_params)
            
            # Create search log entry
            search_log = {
                'query': query,
                'filters': filters_applied,
                'results_count': results_count,
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': datetime.utcnow(),
                'ip_address': None,  # Would get from request
                'user_agent': None,  # Would get from request
                'referrer': None   # Would get from request
            }
            
            # This would save to search_logs table
            # For now, log to application logger
            current_app.logger.info(f"Search logged: {json.dumps(search_log)}")
            
            # Update search statistics
            self._update_search_stats(query, filters_applied, results_count)
            
        except Exception as e:
            current_app.logger.error(f"Error logging search analytics: {str(e)}")
    
    def _extract_applied_filters(self, search_params: Dict) -> Dict:
        """Extract and categorize applied filters"""
        filters = {
            'categories': search_params.get('category_ids', []),
            'subjects': search_params.get('subject_ids', []),
            'price_range': {
                'min': search_params.get('price_min'),
                'max': search_params.get('price_max')
            },
            'rating': search_params.get('min_rating'),
            'teaching_modes': search_params.get('teaching_modes', []),
            'location': {
                'text': search_params.get('location'),
                'coordinates': {
                    'latitude': search_params.get('latitude'),
                    'longitude': search_params.get('longitude'),
                    'radius': search_params.get('radius_km')
                }
            },
            'availability': {
                'now': search_params.get('available_now'),
                'days': search_params.get('available_days', [])
            },
            'verification': {
                'verified_only': search_params.get('verified_only'),
                'background_checked': search_params.get('background_checked_only')
            },
            'experience': search_params.get('min_experience_years'),
            'special_features': {
                'trial': search_params.get('offers_trial'),
                'group_sessions': search_params.get('accepts_group_sessions')
            }
        }
        
        return filters
    
    def _update_search_stats(self, query: str, filters: Dict, results_count: int):
        """Update search statistics in real-time"""
        # This would update search_stats table
        # For now, just log the update
        stats_update = {
            'query': query,
            'filter_count': self._count_active_filters(filters),
            'has_results': results_count > 0,
            'timestamp': datetime.utcnow()
        }
        
        current_app.logger.info(f"Search stats updated: {json.dumps(stats_update)}")
    
    def _count_active_filters(self, filters: Dict) -> int:
        """Count number of active filters"""
        count = 0
        
        # Count non-empty filter values
        if filters['categories']:
            count += 1
        if filters['subjects']:
            count += 1
        if filters['price_range']['min'] or filters['price_range']['max']:
            count += 1
        if filters['rating']:
            count += 1
        if filters['teaching_modes']:
            count += 1
        if filters['location']['text'] or filters['location']['coordinates']['latitude']:
            count += 1
        if filters['availability']['now'] or filters['availability']['days']:
            count += 1
        if filters['verification']['verified_only'] or filters['verification']['background_checked_only']:
            count += 1
        if filters['experience']:
            count += 1
        if filters['special_features']['trial'] or filters['special_features']['group_sessions']:
            count += 1
        
        return count
    
    def get_popular_searches(self, days: int = 30, limit: int = 20) -> List[Dict]:
        """
        Get popular search terms within specified time period
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results to return
            
        Returns:
            List of popular search terms with counts
        """
        try:
            # This would query search_logs table
            # For now, return static popular terms based on typical patterns
            popular_terms = [
                {'term': 'Mathematics', 'count': 1250, 'trend': 'up'},
                {'term': 'English', 'count': 980, 'trend': 'stable'},
                {'term': 'Python Programming', 'count': 856, 'trend': 'up'},
                {'term': 'Guitar Lessons', 'count': 743, 'trend': 'up'},
                {'term': 'Physics', 'count': 698, 'trend': 'stable'},
                {'term': 'Chemistry', 'count': 645, 'trend': 'down'},
                {'term': 'Spanish', 'count': 612, 'trend': 'up'},
                {'term': 'Web Development', 'count': 589, 'trend': 'up'},
                {'term': 'Piano', 'count': 567, 'trend': 'stable'},
                {'term': 'French', 'count': 534, 'trend': 'stable'},
                {'term': 'Calculus', 'count': 512, 'trend': 'up'},
                {'term': 'Data Science', 'count': 498, 'trend': 'up'},
                {'term': 'IELTS Preparation', 'count': 476, 'trend': 'up'},
                {'term': 'Java Programming', 'count': 453, 'trend': 'stable'},
                {'term': 'Photography', 'count': 421, 'trend': 'up'},
                {'term': 'Yoga', 'count': 398, 'trend': 'up'},
                {'term': 'Business English', 'count': 376, 'trend': 'stable'},
                {'term': 'Machine Learning', 'count': 354, 'trend': 'up'},
                {'term': 'Dance Classes', 'count': 332, 'trend': 'up'},
                {'term': 'Cooking Classes', 'count': 309, 'trend': 'stable'}
            ]
            
            return popular_terms[:limit]
            
        except Exception as e:
            current_app.logger.error(f"Error getting popular searches: {str(e)}")
            return []
    
    def get_search_trends(self, days: int = 7) -> Dict:
        """
        Get search trends and patterns
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend data
        """
        try:
            # This would analyze search_logs table for patterns
            # For now, return mock trend data
            trends = {
                'daily_searches': self._generate_daily_trends(days),
                'popular_filters': self._get_popular_filters(),
                'search_success_rate': self._calculate_success_rate(),
                'average_filter_count': 3.2,  # Would be calculated from actual data
                'peak_search_hours': [19, 20, 21, 22],  # 7-10 PM
                'top_converting_queries': [
                    {'query': 'Mathematics', 'conversion_rate': 12.5},
                    {'query': 'Python Programming', 'conversion_rate': 10.8},
                    {'query': 'English', 'conversion_rate': 9.6},
                    {'query': 'Guitar Lessons', 'conversion_rate': 8.9},
                    {'query': 'Spanish', 'conversion_rate': 8.2}
                ]
            }
            
            return trends
            
        except Exception as e:
            current_app.logger.error(f"Error getting search trends: {str(e)}")
            return {}
    
    def _generate_daily_trends(self, days: int) -> List[Dict]:
        """Generate mock daily search trends"""
        trends = []
        base_date = datetime.utcnow() - timedelta(days=days)
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            # Simulate search volume with some randomness
            base_volume = 100 + (i * 2)  # Growing trend
            volume = base_volume + (hash(date.strftime('%Y-%m-%d')) % 50)
            
            trends.append({
                'date': date.strftime('%Y-%m-%d'),
                'searches': max(50, volume),
                'unique_users': int(volume * 0.7)
            })
        
        return trends
    
    def _get_popular_filters(self) -> Dict:
        """Get most popular filter combinations"""
        return {
            'price_ranges': [
                {'range': '$25-50', 'usage_percentage': 35.2},
                {'range': '$50-75', 'usage_percentage': 28.7},
                {'range': '$0-25', 'usage_percentage': 22.1},
                {'range': '$75-100', 'usage_percentage': 10.3},
                {'range': '$100+', 'usage_percentage': 3.7}
            ],
            'teaching_modes': [
                {'mode': 'Online', 'usage_percentage': 72.4},
                {'mode': 'Offline', 'usage_percentage': 18.9},
                {'mode': 'Hybrid', 'usage_percentage': 8.7}
            ],
            'categories': [
                {'category': 'Academic Tuition', 'usage_percentage': 45.3},
                {'category': 'IT & Professional Skills', 'usage_percentage': 23.8},
                {'category': 'Languages & Communication', 'usage_percentage': 18.2},
                {'category': 'Hobbies & Lifestyle', 'usage_percentage': 12.7}
            ]
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate search success rate (searches with results)"""
        # Mock calculation - would be based on actual data
        return 78.5
    
    def get_zero_result_searches(self, days: int = 7, limit: int = 50) -> List[Dict]:
        """
        Get searches that returned no results
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List of zero-result searches with frequency
        """
        try:
            # This would query search_logs for zero-result searches
            # For now, return common problematic searches
            zero_result_searches = [
                {'query': 'Advanced Quantum Physics Tutor', 'count': 45, 'suggested_alternatives': ['Physics', 'Quantum Mechanics']},
                {'query': 'Ancient Greek Philosophy', 'count': 32, 'suggested_alternatives': ['Philosophy', 'Greek Language']},
                {'query': 'Blockchain Development Expert', 'count': 28, 'suggested_alternatives': ['Blockchain', 'Cryptocurrency', 'Web Development']},
                {'query': 'Professional Chef Training', 'count': 24, 'suggested_alternatives': ['Cooking', 'Culinary Arts', 'Chef Classes']},
                {'query': 'Space Engineering Tutor', 'count': 18, 'suggested_alternatives': ['Engineering', 'Physics', 'Astronomy']},
                {'query': 'Medieval History Expert', 'count': 15, 'suggested_alternatives': ['History', 'European History']},
                {'query': 'AI Ethics Specialist', 'count': 12, 'suggested_alternatives': ['Artificial Intelligence', 'Ethics', 'Philosophy']}
            ]
            
            return zero_result_searches[:limit]
            
        except Exception as e:
            current_app.logger.error(f"Error getting zero-result searches: {str(e)}")
            return []
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions based on common patterns and corrections
        
        Args:
            query: Original search query
            
        Returns:
            List of suggested search terms
        """
        suggestions = []
        
        # Common misspellings and corrections
        corrections = {
            'math': 'mathematics',
            'programmng': 'programming',
            'javascrpt': 'javascript',
            'phyton': 'python',
            'gitar': 'guitar',
            'piano lesso': 'piano lessons',
            'spanish clas': 'spanish classes',
            'web deve': 'web development',
            'data scince': 'data science'
        }
        
        # Check for common misspellings
        query_lower = query.lower()
        if query_lower in corrections:
            suggestions.append(corrections[query_lower])
        
        # Partial matches based on popular searches
        popular_terms = ['mathematics', 'programming', 'guitar', 'piano', 'spanish', 'english', 'physics', 'chemistry']
        
        for term in popular_terms:
            if term.startswith(query_lower) and term != query_lower:
                suggestions.append(term)
        
        # Subject-based suggestions
        subjects = Subject.query.filter(
            Subject.name.ilike(f'%{query}%')
        ).limit(5).all()
        
        for subject in subjects:
            suggestions.append(subject.name)
        
        # Remove duplicates and limit
        return list(set(suggestions))[:10]
    
    def analyze_search_performance(self, search_params: Dict, results_count: int, response_time: float) -> Dict:
        """
        Analyze search performance and provide optimization suggestions
        
        Args:
            search_params: Search parameters used
            results_count: Number of results returned
            response_time: Search response time in milliseconds
            
        Returns:
            Performance analysis and suggestions
        """
        analysis = {
            'performance_score': 0,
            'issues': [],
            'suggestions': [],
            'optimization_tips': []
        }
        
        # Analyze result count
        if results_count == 0:
            analysis['issues'].append('No results found')
            analysis['suggestions'].append('Try broader search terms or fewer filters')
            analysis['performance_score'] -= 30
        elif results_count < 5:
            analysis['issues'].append('Very few results')
            analysis['suggestions'].append('Consider expanding search criteria')
            analysis['performance_score'] -= 15
        elif results_count > 100:
            analysis['issues'].append('Too many results')
            analysis['suggestions'].append('Add more specific filters to narrow results')
            analysis['performance_score'] -= 10
        else:
            analysis['performance_score'] += 20
        
        # Analyze response time
        if response_time > 2000:  # 2 seconds
            analysis['issues'].append('Slow response time')
            analysis['optimization_tips'].append('Consider adding search indexes')
            analysis['performance_score'] -= 20
        elif response_time > 1000:  # 1 second
            analysis['optimization_tips'].append('Response time could be improved')
            analysis['performance_score'] -= 10
        else:
            analysis['performance_score'] += 10
        
        # Analyze filter usage
        filter_count = self._count_active_filters(self._extract_applied_filters(search_params))
        if filter_count > 8:
            analysis['issues'].append('Too many filters applied')
            analysis['suggestions'].append('Try reducing number of filters')
            analysis['performance_score'] -= 15
        elif filter_count < 1 and len(search_params.get('query', '').strip()) < 3:
            analysis['issues'].append('Very broad search')
            analysis['suggestions'].append('Add more specific terms or filters')
            analysis['performance_score'] -= 10
        
        # Normalize score
        analysis['performance_score'] = max(0, min(100, analysis['performance_score'] + 50))  # Base 50 points
        
        # Add general optimization tips
        if analysis['performance_score'] < 70:
            analysis['optimization_tips'].extend([
                'Consider implementing search result caching',
                'Review search query optimization',
                'Monitor search analytics regularly'
            ])
        
        return analysis
    
    def get_subject_popularity(self, days: int = 30) -> List[Dict]:
        """
        Get subject popularity based on search frequency
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of subjects with popularity metrics
        """
        try:
            # This would analyze search_logs and tutor data
            # For now, return mock data based on typical patterns
            subjects = Subject.query.filter_by(is_active=True).all()
            
            subject_popularity = []
            for subject in subjects:
                # Mock popularity calculation based on subject name and typical demand
                base_popularity = 50
                
                # Boost for popular subjects
                if any(keyword in subject.name.lower() for keyword in ['math', 'english', 'python', 'guitar']):
                    base_popularity += 30
                elif any(keyword in subject.name.lower() for keyword in ['physics', 'chemistry', 'spanish', 'piano']):
                    base_popularity += 20
                elif any(keyword in subject.name.lower() for keyword in ['programming', 'music', 'language']):
                    base_popularity += 15
                
                # Add some randomness
                import random
                popularity = base_popularity + random.randint(-10, 20)
                
                # Get tutor count for this subject
                tutor_count = len(subject.tutor_subjects.filter_by(is_active=True).all())
                
                subject_popularity.append({
                    'subject_id': subject.id,
                    'subject_name': subject.name,
                    'category_name': subject.category.name if subject.category else None,
                    'popularity_score': min(100, max(0, popularity)),
                    'tutor_count': tutor_count,
                    'average_price': subject.get_average_price(),
                    'trend': random.choice(['up', 'stable', 'down'])
                })
            
            # Sort by popularity
            subject_popularity.sort(key=lambda x: x['popularity_score'], reverse=True)
            
            return subject_popularity
            
        except Exception as e:
            current_app.logger.error(f"Error getting subject popularity: {str(e)}")
            return []
    
    def generate_search_report(self, days: int = 30) -> Dict:
        """
        Generate comprehensive search analytics report
        
        Args:
            days: Number of days to include in report
            
        Returns:
            Complete analytics report
        """
        try:
            report = {
                'period': {
                    'start_date': (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d'),
                    'end_date': datetime.utcnow().strftime('%Y-%m-%d'),
                    'days': days
                },
                'summary': {
                    'total_searches': 15420,  # Mock data
                    'unique_users': 8934,
                    'average_searches_per_user': 1.73,
                    'success_rate': self._calculate_success_rate(),
                    'average_response_time': 850,  # milliseconds
                    'average_filters_per_search': 3.2
                },
                'popular_searches': self.get_popular_searches(days, 10),
                'trends': self.get_search_trends(days),
                'zero_result_searches': self.get_zero_result_searches(days, 10),
                'subject_popularity': self.get_subject_popularity(days)[:20],
                'filter_usage': self._get_popular_filters(),
                'performance_metrics': {
                    'average_response_time': 850,
                    '95th_percentile_response_time': 1200,
                    'cache_hit_rate': 67.3,
                    'search_index_size': 15420
                },
                'recommendations': self._generate_recommendations()
            }
            
            return report
            
        except Exception as e:
            current_app.logger.error(f"Error generating search report: {str(e)}")
            return {}
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on analytics"""
        return [
            'Implement Elasticsearch for improved search performance',
            'Add autocomplete functionality for better user experience',
            'Optimize search result ranking algorithm',
            'Add search result caching for popular queries',
            'Implement A/B testing for search interface',
            'Add voice search capabilities',
            'Improve mobile search experience',
            'Add search result personalization',
            'Implement search analytics dashboard'
        ]