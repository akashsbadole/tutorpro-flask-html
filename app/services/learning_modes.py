"""
Learning Modes Service for TutorPro Marketplace
Flexible learning options (online/offline/hybrid) management
"""

from flask import current_app
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import json

from app import db
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.subject import Subject
from app.models.booking import Booking
from app.models.demo import DemoSession
from app.models.student import LearnerProfile

class LearningModeService:
    """Service for managing flexible learning modes"""
    
    def __init__(self):
        self.learning_modes = {
            'online': {
                'name': 'Online Learning',
                'description': 'Learn from anywhere with internet connection',
                'features': ['Video calls', 'Screen sharing', 'Digital whiteboard', 'Recording', 'Chat'],
                'requirements': ['Internet connection', 'Device with camera/mic', 'Quiet space'],
                'benefits': ['Flexible location', 'No travel time', 'Record sessions', 'Digital resources']
            },
            'offline': {
                'name': 'In-Person Learning',
                'description': 'Face-to-face learning at a physical location',
                'features': ['Personal interaction', 'Hands-on learning', 'Immediate feedback', 'Physical materials'],
                'requirements': ['Travel to location', 'Meeting place', 'Physical materials'],
                'benefits': ['Personal connection', 'Hands-on experience', 'Better focus', 'Social interaction']
            },
            'hybrid': {
                'name': 'Hybrid Learning',
                'description': 'Combination of online and in-person sessions',
                'features': ['Flexible scheduling', 'Mixed learning methods', 'Adaptive approach', 'Best of both worlds'],
                'requirements': ['Internet access', 'Occasional travel', 'Flexible schedule'],
                'benefits': ['Maximum flexibility', 'Varied learning experience', 'Adaptable to needs', 'Comprehensive approach']
            }
        }
    
    def get_available_learning_modes(self, tutor_id: int, subject_id: int = None) -> List[Dict]:
        """
        Get available learning modes for a tutor
        
        Args:
            tutor_id: Tutor user ID
            subject_id: Subject ID (optional)
            
        Returns:
            List of available learning modes with details
        """
        try:
            # Get tutor profile
            tutor_profile = TutorProfile.query.filter_by(user_id=tutor_id).first()
            if not tutor_profile:
                return []
            
            # Get tutor's teaching modes
            teaching_modes = tutor_profile.get_teaching_modes_list()
            
            # Build mode details
            available_modes = []
            for mode in teaching_modes:
                if mode in self.learning_modes:
                    mode_info = self.learning_modes[mode].copy()
                    mode_info['mode'] = mode
                    mode_info['available'] = True
                    
                    # Add mode-specific details
                    if mode == 'online':
                        mode_info.update(self._get_online_mode_details(tutor_profile))
                    elif mode == 'offline':
                        mode_info.update(self._get_offline_mode_details(tutor_profile))
                    elif mode == 'hybrid':
                        mode_info.update(self._get_hybrid_mode_details(tutor_profile))
                    
                    available_modes.append(mode_info)
            
            return available_modes
            
        except Exception as e:
            current_app.logger.error(f"Error getting available learning modes: {str(e)}")
            return []
    
    def _get_online_mode_details(self, tutor_profile: TutorProfile) -> Dict:
        """Get online learning mode specific details"""
        details = {
            'platforms': self._get_tutor_platforms(tutor_profile),
            'tools': self._get_tutor_online_tools(tutor_profile),
            'recording_available': tutor_profile.allows_session_recording if hasattr(tutor_profile, 'allows_session_recording') else True,
            'digital_materials': tutor_profile.provides_digital_materials if hasattr(tutor_profile, 'provides_digital_materials') else True
        }
        
        # Add pricing for online sessions
        if tutor_profile.hourly_rate_online:
            details['pricing'] = {
                'hourly_rate': tutor_profile.hourly_rate_online,
                'currency': 'USD'  # Would get from tutor profile
            }
        elif tutor_profile.hourly_rate:
            details['pricing'] = {
                'hourly_rate': tutor_profile.hourly_rate,
                'currency': 'USD'
            }
        
        return details
    
    def _get_offline_mode_details(self, tutor_profile: TutorProfile) -> Dict:
        """Get offline learning mode specific details"""
        details = {
            'locations': self._get_tutor_locations(tutor_profile),
            'travel_preferences': self._get_travel_preferences(tutor_profile),
            'materials_provided': tutor_profile.provides_physical_materials if hasattr(tutor_profile, 'provides_physical_materials') else False,
            'max_travel_distance': tutor_profile.max_travel_distance if hasattr(tutor_profile, 'max_travel_distance') else None
        }
        
        # Add pricing for offline sessions
        if tutor_profile.hourly_rate_offline:
            details['pricing'] = {
                'hourly_rate': tutor_profile.hourly_rate_offline,
                'currency': 'USD'
            }
        elif tutor_profile.hourly_rate:
            details['pricing'] = {
                'hourly_rate': tutor_profile.hourly_rate,
                'currency': 'USD'
            }
        
        # Add travel fees if applicable
        if hasattr(tutor_profile, 'travel_fee_per_km') and tutor_profile.travel_fee_per_km:
            details['travel_fee'] = {
                'fee_per_km': tutor_profile.travel_fee_per_km,
                'included_km': tutor_profile.included_travel_km if hasattr(tutor_profile, 'included_travel_km') else 0
            }
        
        return details
    
    def _get_hybrid_mode_details(self, tutor_profile: TutorProfile) -> Dict:
        """Get hybrid learning mode specific details"""
        details = {
            'online_ratio': tutor_profile.hybrid_online_ratio if hasattr(tutor_profile, 'hybrid_online_ratio') else 0.5,
            'flexible_scheduling': True,
            'customizable_plan': True
        }
        
        # Combine online and offline pricing
        online_rate = tutor_profile.hourly_rate_online or tutor_profile.hourly_rate or 0
        offline_rate = tutor_profile.hourly_rate_offline or tutor_profile.hourly_rate or 0
        
        details['pricing'] = {
            'online_hourly_rate': online_rate,
            'offline_hourly_rate': offline_rate,
            'blended_rate': (online_rate + offline_rate) / 2,
            'currency': 'USD'
        }
        
        return details
    
    def _get_tutor_platforms(self, tutor_profile: TutorProfile) -> List[str]:
        """Get tutor's online teaching platforms"""
        # This would be stored in tutor profile
        default_platforms = ['Zoom', 'Google Meet', 'Skype']
        
        if hasattr(tutor_profile, 'teaching_platforms') and tutor_profile.teaching_platforms:
            try:
                platforms = json.loads(tutor_profile.teaching_platforms)
                return platforms if isinstance(platforms, list) else default_platforms
            except:
                return default_platforms
        
        return default_platforms
    
    def _get_tutor_online_tools(self, tutor_profile: TutorProfile) -> List[str]:
        """Get tutor's online teaching tools"""
        default_tools = ['Digital Whiteboard', 'Screen Sharing', 'File Sharing', 'Chat']
        
        if hasattr(tutor_profile, 'online_tools') and tutor_profile.online_tools:
            try:
                tools = json.loads(tutor_profile.online_tools)
                return tools if isinstance(tools, list) else default_tools
            except:
                return default_tools
        
        return default_tools
    
    def _get_tutor_locations(self, tutor_profile: TutorProfile) -> List[Dict]:
        """Get tutor's teaching locations"""
        locations = []
        
        # Add tutor's address if available
        if tutor_profile.city and tutor_profile.state:
            locations.append({
                'type': 'tutor_location',
                'address': f"{tutor_profile.city}, {tutor_profile.state}",
                'description': "Tutor's location",
                'additional_fee': False
            })
        
        # Add other locations if available
        if hasattr(tutor_profile, 'teaching_locations') and tutor_profile.teaching_locations:
            try:
                teaching_locations = json.loads(tutor_profile.teaching_locations)
                for location in teaching_locations:
                    locations.append({
                        'type': 'additional_location',
                        'address': location.get('address', ''),
                        'description': location.get('description', ''),
                        'additional_fee': location.get('additional_fee', False)
                    })
            except:
                pass
        
        return locations
    
    def _get_travel_preferences(self, tutor_profile: TutorProfile) -> Dict:
        """Get tutor's travel preferences"""
        return {
            'willing_to_travel': tutor_profile.willing_to_travel if hasattr(tutor_profile, 'willing_to_travel') else True,
            'max_distance': tutor_profile.max_travel_distance if hasattr(tutor_profile, 'max_travel_distance') else 25,
            'travel_fee_per_km': tutor_profile.travel_fee_per_km if hasattr(tutor_profile, 'travel_fee_per_km') else 0,
            'included_km': tutor_profile.included_travel_km if hasattr(tutor_profile, 'included_travel_km') else 5
        }
    
    def get_student_preferences(self, student_id: int) -> Dict:
        """
        Get student's learning mode preferences
        
        Args:
            student_id: Student user ID
            
        Returns:
            Student preferences dictionary
        """
        try:
            # Get learner profile
            learner_profile = LearnerProfile.query.filter_by(user_id=student_id).first()
            if not learner_profile:
                return self._get_default_student_preferences()
            
            # Get preferred teaching modes
            preferred_modes = learner_profile.get_preferred_teaching_modes_list()
            
            # Build preferences
            preferences = {
                'preferred_modes': preferred_modes,
                'location': {
                    'city': learner_profile.city,
                    'state': learner_profile.state,
                    'country': learner_profile.country,
                    'max_travel_distance': learner_profile.max_travel_distance
                },
                'scheduling': {
                    'flexible_scheduling': learner_profile.flexible_scheduling,
                    'preferred_session_duration': learner_profile.preferred_session_duration,
                    'preferred_session_frequency': learner_profile.preferred_session_frequency
                },
                'budget': {
                    'min': learner_profile.budget_range_min,
                    'max': learner_profile.budget_range_max
                }
            }
            
            return preferences
            
        except Exception as e:
            current_app.logger.error(f"Error getting student preferences: {str(e)}")
            return self._get_default_student_preferences()
    
    def _get_default_student_preferences(self) -> Dict:
        """Get default student preferences"""
        return {
            'preferred_modes': ['online'],
            'location': {
                'city': None,
                'state': None,
                'country': None,
                'max_travel_distance': None
            },
            'scheduling': {
                'flexible_scheduling': True,
                'preferred_session_duration': 60,
                'preferred_session_frequency': 'Weekly'
            },
            'budget': {
                'min': None,
                'max': None
            }
        }
    
    def find_compatible_tutors(self, student_id: int, subject_id: int, 
                            learning_mode: str = None) -> List[Dict]:
        """
        Find tutors compatible with student's learning preferences
        
        Args:
            student_id: Student user ID
            subject_id: Subject ID
            learning_mode: Preferred learning mode (optional)
            
        Returns:
            List of compatible tutors with compatibility scores
        """
        try:
            # Get student preferences
            student_prefs = self.get_student_preferences(student_id)
            
            # If learning mode specified, use it
            if learning_mode:
                student_prefs['preferred_modes'] = [learning_mode]
            
            # Find tutors who teach the subject
            query = db.session.query(TutorProfile).join(User).filter(
                and_(
                    User.role == 'Tutor',
                    TutorProfile.is_active == True,
                    User.is_active == True
                )
            ).join(TutorProfile.subjects).filter(
                and_(
                    TutorProfile.subjects.any(subject_id=subject_id),
                    TutorProfile.subjects.any(is_active=True)
                )
            )
            
            tutors = query.options(
                joinedload(TutorProfile.user),
                joinedload(TutorProfile.subjects)
            ).all()
            
            # Calculate compatibility scores
            compatible_tutors = []
            for tutor in tutors:
                compatibility = self._calculate_learning_mode_compatibility(student_prefs, tutor)
                if compatibility['score'] > 0:
                    compatible_tutors.append({
                        'tutor': tutor.to_dict(),
                        'compatibility': compatibility
                    })
            
            # Sort by compatibility score
            compatible_tutors.sort(key=lambda x: x['compatibility']['score'], reverse=True)
            
            return compatible_tutors
            
        except Exception as e:
            current_app.logger.error(f"Error finding compatible tutors: {str(e)}")
            return []
    
    def _calculate_learning_mode_compatibility(self, student_prefs: Dict, tutor: TutorProfile) -> Dict:
        """Calculate learning mode compatibility score"""
        try:
            compatibility = {
                'score': 0,
                'mode_matches': [],
                'mode_mismatches': [],
                'location_compatibility': 0,
                'budget_compatibility': 0,
                'details': {}
            }
            
            # Get tutor's teaching modes
            tutor_modes = tutor.get_teaching_modes_list()
            student_modes = student_prefs.get('preferred_modes', ['online'])
            
            # Calculate mode compatibility
            for mode in student_modes:
                if mode in tutor_modes:
                    compatibility['mode_matches'].append(mode)
                    compatibility['score'] += 30  # 30 points for mode match
                else:
                    compatibility['mode_mismatches'].append(mode)
            
            # Calculate location compatibility for offline/hybrid modes
            if any(mode in ['offline', 'hybrid'] for mode in student_modes):
                location_score = self._calculate_location_compatibility(student_prefs, tutor)
                compatibility['location_compatibility'] = location_score
                compatibility['score'] += location_score * 0.2  # 20% weight for location
            
            # Calculate budget compatibility
            budget_score = self._calculate_budget_compatibility(student_prefs, tutor)
            compatibility['budget_compatibility'] = budget_score
            compatibility['score'] += budget_score * 0.2  # 20% weight for budget
            
            # Add bonus for multiple mode matches
            if len(compatibility['mode_matches']) > 1:
                compatibility['score'] += 10
            
            # Add bonus for flexible scheduling
            if student_prefs.get('scheduling', {}).get('flexible_scheduling', False):
                compatibility['score'] += 5
            
            # Cap score at 100
            compatibility['score'] = min(100, compatibility['score'])
            
            return compatibility
            
        except Exception as e:
            current_app.logger.error(f"Error calculating compatibility: {str(e)}")
            return {'score': 0, 'mode_matches': [], 'mode_mismatches': [], 'location_compatibility': 0, 'budget_compatibility': 0}
    
    def _calculate_location_compatibility(self, student_prefs: Dict, tutor: TutorProfile) -> float:
        """Calculate location compatibility score"""
        try:
            student_location = student_prefs.get('location', {})
            student_city = student_location.get('city')
            student_state = student_location.get('state')
            
            if not student_city and not student_state:
                return 50.0  # Neutral score if no location preference
            
            # Check for city match
            if (tutor.city and student_city and 
                tutor.city.lower() == student_city.lower()):
                return 100.0
            
            # Check for state match
            if (tutor.state and student_state and 
                tutor.state.lower() == student_state.lower()):
                return 80.0
            
            # Check if tutor offers online (always compatible for location)
            tutor_modes = tutor.get_teaching_modes_list()
            if 'online' in tutor_modes:
                return 70.0
            
            return 0.0  # No location compatibility
            
        except Exception as e:
            current_app.logger.error(f"Error calculating location compatibility: {str(e)}")
            return 0.0
    
    def _calculate_budget_compatibility(self, student_prefs: Dict, tutor: TutorProfile) -> float:
        """Calculate budget compatibility score"""
        try:
            student_budget = student_prefs.get('budget', {})
            budget_min = student_budget.get('min')
            budget_max = student_budget.get('max')
            
            if not budget_min and not budget_max:
                return 75.0  # Good score if no budget constraints
            
            # Get tutor's rates
            online_rate = tutor.hourly_rate_online or tutor.hourly_rate or 0
            offline_rate = tutor.hourly_rate_offline or tutor.hourly_rate or 0
            
            # Use minimum rate for compatibility check
            tutor_rate = min(online_rate, offline_rate)
            
            if tutor_rate == 0:
                return 50.0  # Neutral score if no rate listed
            
            if budget_max and tutor_rate > budget_max:
                return 0.0  # Over budget
            
            if budget_min and tutor_rate < budget_min:
                return 100.0  # Under budget (great deal)
            
            # Within budget range
            if budget_min and budget_max:
                range_size = budget_max - budget_min
                position = (tutor_rate - budget_min) / range_size
                return (1 - position) * 100
            
            return 75.0  # Good score if only one budget constraint
            
        except Exception as e:
            current_app.logger.error(f"Error calculating budget compatibility: {str(e)}")
            return 50.0
    
    def create_hybrid_learning_plan(self, student_id: int, tutor_id: int, 
                                subject_id: int, plan_data: Dict) -> Dict:
        """
        Create a hybrid learning plan
        
        Args:
            student_id: Student user ID
            tutor_id: Tutor user ID
            subject_id: Subject ID
            plan_data: Hybrid plan details
            
        Returns:
            Created learning plan
        """
        try:
            # Get student and tutor preferences
            student_prefs = self.get_student_preferences(student_id)
            tutor_modes = self.get_available_learning_modes(tutor_id, subject_id)
            
            # Validate hybrid mode is available
            hybrid_available = any(mode['mode'] == 'hybrid' for mode in tutor_modes)
            if not hybrid_available:
                return {'success': False, 'message': 'Hybrid mode not available for this tutor'}
            
            # Create hybrid plan
            hybrid_plan = {
                'student_id': student_id,
                'tutor_id': tutor_id,
                'subject_id': subject_id,
                'plan_type': 'hybrid',
                'online_sessions_per_month': plan_data.get('online_sessions_per_month', 2),
                'offline_sessions_per_month': plan_data.get('offline_sessions_per_month', 2),
                'total_sessions_per_month': plan_data.get('total_sessions_per_month', 4),
                'session_duration': plan_data.get('session_duration', 60),
                'plan_duration_months': plan_data.get('plan_duration_months', 3),
                'online_topics': plan_data.get('online_topics', []),
                'offline_topics': plan_data.get('offline_topics', []),
                'flexible_scheduling': plan_data.get('flexible_scheduling', True),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Calculate pricing
            online_rate = 0
            offline_rate = 0
            
            for mode in tutor_modes:
                if mode['mode'] == 'online' and 'pricing' in mode:
                    online_rate = mode['pricing']['hourly_rate']
                elif mode['mode'] == 'offline' and 'pricing' in mode:
                    offline_rate = mode['pricing']['hourly_rate']
            
            monthly_cost = (
                (hybrid_plan['online_sessions_per_month'] * online_rate * hybrid_plan['session_duration'] / 60) +
                (hybrid_plan['offline_sessions_per_month'] * offline_rate * hybrid_plan['session_duration'] / 60)
            )
            
            hybrid_plan['pricing'] = {
                'online_rate_per_hour': online_rate,
                'offline_rate_per_hour': offline_rate,
                'monthly_cost': monthly_cost,
                'total_cost': monthly_cost * hybrid_plan['plan_duration_months'],
                'currency': 'USD'
            }
            
            return {'success': True, 'plan': hybrid_plan}
            
        except Exception as e:
            current_app.logger.error(f"Error creating hybrid plan: {str(e)}")
            return {'success': False, 'message': 'Error creating learning plan'}
    
    def get_learning_mode_recommendations(self, student_id: int, subject_id: int) -> List[Dict]:
        """
        Get learning mode recommendations for a student
        
        Args:
            student_id: Student user ID
            subject_id: Subject ID
            
        Returns:
            List of recommended learning modes with reasons
        """
        try:
            # Get student preferences
            student_prefs = self.get_student_preferences(student_id)
            
            # Get subject characteristics
            subject = Subject.query.filter_by(id=subject_id).first()
            
            recommendations = []
            
            # Analyze each learning mode
            for mode, mode_info in self.learning_modes.items():
                recommendation = {
                    'mode': mode,
                    'name': mode_info['name'],
                    'description': mode_info['description'],
                    'recommended': False,
                    'score': 0,
                    'reasons': [],
                    'benefits': mode_info['benefits'],
                    'requirements': mode_info['requirements']
                }
                
                # Calculate recommendation score
                score = 0
                reasons = []
                
                # Check if mode is in student preferences
                if mode in student_prefs.get('preferred_modes', []):
                    score += 30
                    reasons.append('Matches your preferred learning mode')
                
                # Subject-specific recommendations
                if subject:
                    if subject.category and subject.category.name in ['Programming', 'IT Skills', 'Digital Arts']:
                        if mode == 'online':
                            score += 25
                            reasons.append('Ideal for technical subjects with screen sharing')
                    elif subject.category and subject.category.name in ['Music', 'Sports', 'Arts & Crafts']:
                        if mode == 'offline':
                            score += 25
                            reasons.append('Hands-on learning benefits for practical subjects')
                
                # Location-based recommendations
                if student_prefs.get('location', {}).get('city'):
                    if mode == 'offline':
                        score += 15
                        reasons.append('Local tutors available in your area')
                else:
                    if mode == 'online':
                        score += 20
                        reasons.append('No location constraints with online learning')
                
                # Budget considerations
                student_budget = student_prefs.get('budget', {})
                if student_budget.get('max'):
                    if mode == 'online':
                        score += 10
                        reasons.append('No travel costs with online learning')
                
                # Scheduling flexibility
                if student_prefs.get('scheduling', {}).get('flexible_scheduling'):
                    if mode in ['online', 'hybrid']:
                        score += 15
                        reasons.append('Maximum scheduling flexibility')
                
                # Set recommendation status
                recommendation['score'] = score
                recommendation['reasons'] = reasons
                recommendation['recommended'] = score >= 50
                
                recommendations.append(recommendation)
            
            # Sort by score
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
            return recommendations
            
        except Exception as e:
            current_app.logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    def compare_learning_modes(self, modes: List[str]) -> Dict:
        """
        Compare multiple learning modes
        
        Args:
            modes: List of learning modes to compare
            
        Returns:
            Comparison data
        """
        try:
            comparison = {
                'modes': [],
                'comparison_table': {},
                'recommendations': []
            }
            
            # Get mode details
            for mode in modes:
                if mode in self.learning_modes:
                    mode_info = self.learning_modes[mode].copy()
                    mode_info['mode'] = mode
                    comparison['modes'].append(mode_info)
            
            # Create comparison table
            criteria = [
                'Flexibility', 'Cost Effectiveness', 'Personal Interaction', 
                'Hands-on Learning', 'Convenience', 'Resources Available'
            ]
            
            for criterion in criteria:
                comparison['comparison_table'][criterion] = {}
                for mode in modes:
                    score = self._get_mode_score_for_criterion(mode, criterion)
                    comparison['comparison_table'][criterion][mode] = score
            
            # Generate recommendations
            best_modes = []
            for criterion in criteria:
                scores = comparison['comparison_table'][criterion]
                if scores:
                    best_mode = max(scores.keys(), key=lambda k: scores[k])
                    best_modes.append({
                        'criterion': criterion,
                        'best_mode': best_mode,
                        'score': scores[best_mode]
                    })
            
            comparison['recommendations'] = best_modes
            
            return comparison
            
        except Exception as e:
            current_app.logger.error(f"Error comparing learning modes: {str(e)}")
            return {}
    
    def _get_mode_score_for_criterion(self, mode: str, criterion: str) -> int:
        """Get score for a learning mode against a criterion"""
        scoring_matrix = {
            'online': {
                'Flexibility': 5,
                'Cost Effectiveness': 5,
                'Personal Interaction': 3,
                'Hands-on Learning': 2,
                'Convenience': 5,
                'Resources Available': 5
            },
            'offline': {
                'Flexibility': 2,
                'Cost Effectiveness': 3,
                'Personal Interaction': 5,
                'Hands-on Learning': 5,
                'Convenience': 2,
                'Resources Available': 3
            },
            'hybrid': {
                'Flexibility': 4,
                'Cost Effectiveness': 3,
                'Personal Interaction': 4,
                'Hands-on Learning': 4,
                'Convenience': 4,
                'Resources Available': 4
            }
        }
        
        return scoring_matrix.get(mode, {}).get(criterion, 0)