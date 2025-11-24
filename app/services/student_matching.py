"""
Student Matching Service for TutorPro Marketplace
Advanced AI-powered matching algorithm for student-tutor compatibility
"""

from flask import current_app
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import joinedload, contains_eager
from app import db
from app.models.user import User
from app.models.tutor import TutorProfile, TutorSubject
from app.models.category import Subject, SubjectCategory
from app.models.verification import TutorRating, TutorReview as Review
from app.models.booking import Booking
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import math
import re

class StudentMatchingService:
    """Advanced student-tutor matching service"""
    
    def __init__(self):
        self.matching_weights = {
            'subject_match': 0.30,      # 30% weight
            'learning_style': 0.20,      # 20% weight
            'schedule_compatibility': 0.15, # 15% weight
            'budget_match': 0.15,        # 15% weight
            'location_preference': 0.10,   # 10% weight
            'personality_match': 0.10      # 10% weight
        }
    
    def find_best_matches(self, student_id: int, limit: int = 20) -> List[Dict]:
        """
        Find best tutor matches for a student
        
        Args:
            student_id: Student user ID
            limit: Maximum number of matches to return
            
        Returns:
            List of tutor matches with compatibility scores
        """
        try:
            # Get student profile and preferences
            student_profile = self._get_student_profile(student_id)
            if not student_profile:
                return []
            
            # Build base query
            query = self._build_matching_query(student_profile)
            
            # Execute query with eager loading
            tutors = query.options(
                joinedload(TutorProfile.user),
                joinedload(TutorProfile.subjects),
                joinedload(TutorProfile.rating_summary),
                joinedload(TutorProfile.certifications)
            ).limit(limit * 3).all()  # Get more candidates for scoring
            
            # Calculate compatibility scores
            scored_tutors = []
            for tutor in tutors:
                score = self._calculate_compatibility_score(student_profile, tutor)
                scored_tutors.append({
                    'tutor': tutor.to_dict(),
                    'compatibility_score': score,
                    'match_factors': self._get_match_factors(student_profile, tutor)
                })
            
            # Sort by compatibility score and limit results
            scored_tutors.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            return scored_tutors[:limit]
            
        except Exception as e:
            current_app.logger.error(f"Error finding matches: {str(e)}")
            return []
    
    def _get_student_profile(self, student_id: int) -> Optional[Dict]:
        """Get student profile with learning preferences"""
        try:
            from app.models.user import User, LearnerProfile
            
            # Get user and learner profile
            user = User.query.filter_by(id=student_id).first()
            if not user or not user.is_learner():
                return None
            
            learner_profile = db.session.query(LearnerProfile).filter_by(user_id=student_id).first()
            
            # Get student's booking history for learning patterns
            booking_history = db.session.query(Booking).filter_by(student_id=student_id).all()
            
            # Build comprehensive student profile
            student_profile = {
                'user_id': student_id,
                'learning_goals': self._parse_json_field(learner_profile.learning_goals) if learner_profile else [],
                'preferred_subjects': self._parse_json_field(learner_profile.preferred_subjects) if learner_profile else [],
                'learning_style': getattr(learner_profile, 'learning_style', 'Visual'),
                'skill_level': getattr(learner_profile, 'experience_level', 'Beginner'),
                'budget_range': {
                    'min': float(learner_profile.budget_range_min) if learner_profile and learner_profile.budget_range_min else None,
                    'max': float(learner_profile.budget_range_max) if learner_profile and learner_profile.budget_range_max else None
                },
                'availability': self._parse_json_field(learner_profile.availability) if learner_profile else [],
                'timezone': getattr(learner_profile, 'timezone', 'UTC'),
                'location': {
                    'city': getattr(learner_profile, 'city', None),
                    'state': getattr(learner_profile, 'state', None),
                    'country': getattr(learner_profile, 'country', None)
                },
                'preferred_tutor_gender': getattr(learner_profile, 'preferred_tutor_gender', 'Any'),
                'language_preference': getattr(learner_profile, 'language_preference', 'English'),
                'booking_patterns': self._analyze_booking_patterns(booking_history),
                'subject_preferences': self._analyze_subject_preferences(booking_history),
                'interaction_history': self._analyze_interaction_history(student_id)
            }
            
            return student_profile
            
        except Exception as e:
            current_app.logger.error(f"Error getting student profile: {str(e)}")
            return None
    
    def _build_matching_query(self, student_profile: Dict):
        """Build base query for tutor matching"""
        # Get active tutors with basic criteria
        query = db.session.query(TutorProfile).join(User).filter(
            and_(
                User.role == 'Tutor',
                TutorProfile.is_active == True,
                User.is_active == True
            )
        )
        
        # Apply subject filter if student has preferences
        if student_profile.get('preferred_subjects'):
            query = query.filter(
                TutorProfile.subjects.any(
                    and_(
                        TutorSubject.is_active == True,
                        Subject.name.in_(student_profile['preferred_subjects'])
                    )
                )
            )
        
        # Apply budget filter
        budget_range = student_profile.get('budget_range', {})
        if budget_range.get('min') or budget_range.get('max'):
            if budget_range.get('min'):
                query = query.filter(
                    or_(
                        TutorProfile.hourly_rate >= budget_range['min'],
                        TutorProfile.price_per_group_session >= budget_range['min']
                    )
                )
            if budget_range.get('max'):
                query = query.filter(
                    or_(
                        TutorProfile.hourly_rate <= budget_range['max'],
                        TutorProfile.price_per_group_session <= budget_range['max']
                    )
                )
        
        # Apply gender preference if specified
        if student_profile.get('preferred_tutor_gender') != 'Any':
            # This would require gender information in tutor profiles
            pass
        
        # Apply location preference if specified
        student_location = student_profile.get('location', {})
        if student_location.get('city'):
            query = query.filter(
                or_(
                    TutorProfile.city.ilike(f'%{student_location["city"]}%'),
                    TutorProfile.state.ilike(f'%{student_location.get("state", "")}%'),
                    TutorProfile.country.ilike(f'%{student_location.get("country", "")}%')
                )
            )
        
        # Apply language preference
        if student_profile.get('language_preference'):
            query = query.filter(
                TutorProfile.languages_spoken.like(f'%"{student_profile["language_preference"]}%')
            )
        
        return query
    
    def _calculate_compatibility_score(self, student_profile: Dict, tutor: TutorProfile) -> float:
        """Calculate overall compatibility score between student and tutor"""
        try:
            scores = {}
            
            # Subject match score
            scores['subject_match'] = self._calculate_subject_match(student_profile, tutor)
            
            # Learning style compatibility
            scores['learning_style'] = self._calculate_learning_style_match(student_profile, tutor)
            
            # Schedule compatibility
            scores['schedule_compatibility'] = self._calculate_schedule_match(student_profile, tutor)
            
            # Budget match
            scores['budget_match'] = self._calculate_budget_match(student_profile, tutor)
            
            # Location preference
            scores['location_preference'] = self._calculate_location_match(student_profile, tutor)
            
            # Personality match (simplified)
            scores['personality_match'] = self._calculate_personality_match(student_profile, tutor)
            
            # Calculate weighted total score
            total_score = 0.0
            for factor, weight in self.matching_weights.items():
                factor_score = scores.get(factor, 0.0)
                total_score += factor_score * weight
            
            return round(total_score, 2)
            
        except Exception as e:
            current_app.logger.error(f"Error calculating compatibility score: {str(e)}")
            return 0.0
    
    def _calculate_subject_match(self, student_profile: Dict, tutor: TutorProfile) -> float:
        """Calculate subject compatibility score (0-100)"""
        try:
            preferred_subjects = set(student_profile.get('preferred_subjects', []))
            tutor_subjects = set()
            
            for tutor_subject in tutor.subjects:
                if tutor_subject.is_active:
                    tutor_subjects.add(tutor_subject.subject.name)
            
            if not preferred_subjects:
                return 50.0  # Neutral score if no preferences
            
            # Calculate intersection
            common_subjects = preferred_subjects.intersection(tutor_subjects)
            
            if not common_subjects:
                return 0.0
            
            # Score based on percentage of preferred subjects taught
            match_percentage = len(common_subjects) / len(preferred_subjects)
            
            # Bonus for exact matches
            if len(common_subjects) == len(preferred_subjects):
                return 100.0
            
            # Scale to 0-100 range
            return min(100.0, match_percentage * 100)
            
        except Exception as e:
            current_app.logger.error(f"Error calculating subject match: {str(e)}")
            return 0.0
    
    def _calculate_learning_style_match(self, student_profile: Dict, tutor: TutorProfile) -> float:
        """Calculate learning style compatibility score (0-100)"""
        try:
            student_style = student_profile.get('learning_style', 'Visual').lower()
            
            # Get tutor's teaching styles from description/bio
            tutor_description = (tutor.description or '').lower() + ' ' + (tutor.bio or '').lower()
            
            # Teaching style keywords
            style_keywords = {
                'visual': ['visual', 'diagrams', 'charts', 'images', 'demonstrations'],
                'auditory': ['verbal', 'lectures', 'discussions', 'audio', 'listening'],
                'kinesthetic': ['hands-on', 'practical', 'exercises', 'activities', 'movement'],
                'reading': ['reading', 'writing', 'texts', 'books', 'notes']
            }
            
            # Count keyword matches for student's preferred style
            student_keywords = style_keywords.get(student_style, [])
            match_count = sum(1 for keyword in student_keywords if keyword in tutor_description)
            
            # Calculate score based on keyword density
            if not student_keywords:
                return 50.0  # Neutral score
            
            # Base score from keyword matches
            keyword_score = min(50.0, (match_count / len(student_keywords)) * 100)
            
            # Bonus for explicit teaching style mention
            if student_style in tutor_description:
                keyword_score += 25.0
            
            return min(100.0, keyword_score)
            
        except Exception as e:
            current_app.logger.error(f"Error calculating learning style match: {str(e)}")
            return 50.0
    
    def _calculate_schedule_match(self, student_profile: Dict, tutor: TutorProfile) -> float:
        """Calculate schedule compatibility score (0-100)"""
        try:
            student_availability = student_profile.get('availability', [])
            tutor_availability = tutor.get_available_days()
            
            if not student_availability:
                return 75.0  # Good score if no specific requirements
            
            # Calculate overlap percentage
            student_days = set(student_availability)
            tutor_days = set(tutor_availability)
            
            if not tutor_days:
                return 0.0
            
            overlap_days = student_days.intersection(tutor_days)
            
            if not overlap_days:
                return 0.0
            
            # Calculate percentage of student's availability that matches
            overlap_percentage = len(overlap_days) / len(student_days)
            
            return overlap_percentage * 100
            
        except Exception as e:
            current_app.logger.error(f"Error calculating schedule match: {str(e)}")
            return 50.0
    
    def _calculate_budget_match(self, student_profile: Dict, tutor: TutorProfile) -> float:
        """Calculate budget compatibility score (0-100)"""
        try:
            budget_range = student_profile.get('budget_range', {})
            
            if not budget_range.get('min') and not budget_range.get('max'):
                return 75.0  # Good score if no budget constraints
            
            tutor_price = float(tutor.hourly_rate or 0)
            
            if tutor_price == 0:
                return 50.0  # Neutral score if no price listed
            
            budget_min = budget_range.get('min', 0)
            budget_max = budget_range.get('max', float('inf'))
            
            if tutor_price < budget_min:
                return 100.0  # Perfect score - under budget
            elif tutor_price > budget_max:
                return 0.0  # No match - over budget
            else:
                # Calculate how well it fits in the range
                if budget_max == float('inf'):
                    # Only minimum budget specified
                    if tutor_price == budget_min:
                        return 100.0
                    else:
                        return max(0.0, 100.0 - ((tutor_price - budget_min) / budget_min) * 50)
                else:
                    # Range specified - calculate position in range
                    range_size = budget_max - budget_min
                    price_position = tutor_price - budget_min
                    percentage_in_range = (range_size - price_position) / range_size
                    return percentage_in_range * 100
                    
        except Exception as e:
            current_app.logger.error(f"Error calculating budget match: {str(e)}")
            return 50.0
    
    def _calculate_location_match(self, student_profile: Dict, tutor: TutorProfile) -> float:
        """Calculate location preference score (0-100)"""
        try:
            student_location = student_profile.get('location', {})
            
            if not student_location.get('city'):
                return 50.0  # Neutral score if no location preference
            
            # Check for exact city match
            if (tutor.city and student_location['city'] and 
                tutor.city.lower() == student_location['city'].lower()):
                return 100.0
            
            # Check for state match
            if (tutor.state and student_location.get('state') and 
                tutor.state.lower() == student_location['state'].lower()):
                return 80.0
            
            # Check for country match
            if (tutor.country and student_location.get('country') and 
                tutor.country.lower() == student_location['country'].lower()):
                return 60.0
            
            # Check if tutor offers online (always a match for location flexibility)
            teaching_modes = tutor.get_teaching_modes_list()
            if 'online' in teaching_modes:
                return 70.0
            
            return 0.0  # No location match
            
        except Exception as e:
            current_app.logger.error(f"Error calculating location match: {str(e)}")
            return 50.0
    
    def _calculate_personality_match(self, student_profile: Dict, tutor: TutorProfile) -> float:
        """Calculate personality compatibility score (simplified) (0-100)"""
        try:
            # This is a simplified version - in production, would use more sophisticated
            # personality analysis based on profiles, communication style, etc.
            
            # Base score from tutor's communication indicators
            base_score = 50.0
            
            # Bonus factors
            if tutor.response_time_hours and tutor.response_time_hours < 24:
                base_score += 15.0  # Quick responder
            
            if tutor.rating and tutor.rating >= 4.5:
                base_score += 15.0  # High-rated tutor
            
            if tutor.total_reviews and tutor.total_reviews > 50:
                base_score += 10.0  # Experienced with many reviews
            
            if tutor.is_verified:
                base_score += 10.0  # Verified tutor
            
            # Check for student-friendly indicators in profile
            tutor_text = ((tutor.description or '') + ' ' + (tutor.bio or '')).lower()
            
            friendly_keywords = ['patient', 'friendly', 'supportive', 'encouraging', 'understanding']
            friendly_matches = sum(1 for keyword in friendly_keywords if keyword in tutor_text)
            base_score += min(20.0, friendly_matches * 5)
            
            return min(100.0, base_score)
            
        except Exception as e:
            current_app.logger.error(f"Error calculating personality match: {str(e)}")
            return 50.0
    
    def _get_match_factors(self, student_profile: Dict, tutor: TutorProfile) -> Dict:
        """Get detailed breakdown of matching factors"""
        try:
            factors = {}
            
            # Subject compatibility details
            preferred_subjects = set(student_profile.get('preferred_subjects', []))
            tutor_subjects = set()
            for tutor_subject in tutor.subjects:
                if tutor_subject.is_active:
                    tutor_subjects.add(tutor_subject.subject.name)
            
            common_subjects = preferred_subjects.intersection(tutor_subjects)
            factors['subjects'] = {
                'student_prefers': list(preferred_subjects),
                'tutor_teaches': list(tutor_subjects),
                'common_subjects': list(common_subjects),
                'match_percentage': len(common_subjects) / len(preferred_subjects) * 100 if preferred_subjects else 0
            }
            
            # Budget compatibility details
            budget_range = student_profile.get('budget_range', {})
            tutor_price = float(tutor.hourly_rate or 0)
            factors['budget'] = {
                'student_range': budget_range,
                'tutor_price': tutor_price,
                'within_budget': (budget_range.get('min', 0) <= tutor_price <= budget_range.get('max', float('inf'))),
                'budget_score': self._calculate_budget_match(student_profile, tutor)
            }
            
            # Location compatibility details
            student_location = student_profile.get('location', {})
            factors['location'] = {
                'student_prefers': student_location,
                'tutor_location': {
                    'city': tutor.city,
                    'state': tutor.state,
                    'country': tutor.country
                },
                'offers_online': 'online' in tutor.get_teaching_modes_list(),
                'match_score': self._calculate_location_match(student_profile, tutor)
            }
            
            # Teaching style compatibility
            factors['teaching_style'] = {
                'student_preference': student_profile.get('learning_style', 'Visual'),
                'tutor_description': tutor.description or '',
                'match_score': self._calculate_learning_style_match(student_profile, tutor)
            }
            
            return factors
            
        except Exception as e:
            current_app.logger.error(f"Error getting match factors: {str(e)}")
            return {}
    
    def _parse_json_field(self, field_value) -> List:
        """Parse JSON field safely"""
        try:
            if field_value:
                return json.loads(field_value)
            return []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def _analyze_booking_patterns(self, bookings: List) -> Dict:
        """Analyze student's booking patterns"""
        if not bookings:
            return {}
        
        patterns = {
            'preferred_days': [],
            'preferred_times': [],
            'session_duration_preference': 'medium',
            'booking_frequency': 0,
            'cancellation_rate': 0.0,
            'repeat_tutor_rate': 0.0
        }
        
        # Analyze booking times
        day_counts = {}
        time_counts = {}
        tutor_counts = {}
        
        for booking in bookings:
            if booking.scheduled_start_time:
                day_name = booking.scheduled_start_time.strftime('%A')
                time_hour = booking.scheduled_start_time.hour
                
                day_counts[day_name] = day_counts.get(day_name, 0) + 1
                time_counts[time_hour] = time_counts.get(time_hour, 0) + 1
                
                if booking.tutor_id:
                    tutor_counts[booking.tutor_id] = tutor_counts.get(booking.tutor_id, 0) + 1
        
        # Extract patterns
        if day_counts:
            patterns['preferred_days'] = [day for day, count in day_counts.items() if count >= 2]
        
        if time_counts:
            patterns['preferred_times'] = [hour for hour, count in time_counts.items() if count >= 2]
        
        patterns['booking_frequency'] = len(bookings)
        
        # Calculate repeat tutor rate
        if tutor_counts:
            repeat_bookings = sum(1 for count in tutor_counts.values() if count > 1)
            patterns['repeat_tutor_rate'] = (repeat_bookings / len(tutor_counts)) * 100 if tutor_counts else 0
        
        return patterns
    
    def _analyze_subject_preferences(self, bookings: List) -> List[str]:
        """Analyze subject preferences from booking history"""
        if not bookings:
            return []
        
        subject_counts = {}
        for booking in bookings:
            if booking.subject_id:
                subject_counts[booking.subject_id] = subject_counts.get(booking.subject_id, 0) + 1
        
        # Sort by frequency and return top subjects
        sorted_subjects = sorted(subject_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [subject_id for subject_id, count in sorted_subjects[:5]]
    
    def _analyze_interaction_history(self, student_id: int) -> Dict:
        """Analyze student's interaction history"""
        # This would analyze messages, profile views, search history, etc.
        # For now, return basic interaction metrics
        return {
            'profile_views': 0,  # Would be tracked
            'messages_sent': 0,  # Would be tracked
            'searches_performed': 0,  # Would be tracked
            'last_active': datetime.utcnow() - timedelta(days=7)  # Mock data
        }
    
    def recommend_learning_path(self, student_id: int, subject_id: int) -> List[Dict]:
        """
        Recommend learning path for student in specific subject
        
        Args:
            student_id: Student user ID
            subject_id: Subject ID for learning path
            
        Returns:
            List of recommended learning steps
        """
        try:
            student_profile = self._get_student_profile(student_id)
            if not student_profile:
                return []
            
            # Get subject information
            subject = Subject.query.filter_by(id=subject_id).first()
            if not subject:
                return []
            
            # Get learning objectives for subject
            learning_objectives = subject.learning_objectives.filter_by(is_active=True).order_by('sort_order').all()
            
            # Find tutors who teach this subject
            suitable_tutors = self._find_suitable_tutors_for_subject(student_profile, subject_id)
            
            # Build learning path recommendations
            learning_path = []
            for i, objective in enumerate(learning_objectives):
                step = {
                    'step_number': i + 1,
                    'objective': objective.to_dict(),
                    'estimated_duration': self._estimate_step_duration(objective, student_profile),
                    'recommended_tutors': self._recommend_tutors_for_step(suitable_tutors, objective),
                    'prerequisites': self._get_prerequisites(objective, i),
                    'difficulty_level': self._assess_step_difficulty(objective, student_profile)
                }
                learning_path.append(step)
            
            return learning_path
            
        except Exception as e:
            current_app.logger.error(f"Error recommending learning path: {str(e)}")
            return []
    
    def _find_suitable_tutors_for_subject(self, student_profile: Dict, subject_id: int) -> List[TutorProfile]:
        """Find tutors suitable for specific subject and student"""
        query = db.session.query(TutorProfile).join(User).filter(
            and_(
                User.role == 'Tutor',
                TutorProfile.is_active == True,
                User.is_active == True
            )
        ).join(TutorSubject).filter(
            and_(
                TutorSubject.subject_id == subject_id,
                TutorSubject.is_active == True
            )
        )
        
        # Apply student preferences
        budget_range = student_profile.get('budget_range', {})
        if budget_range.get('max'):
            query = query.filter(
                or_(
                    TutorProfile.hourly_rate <= budget_range['max'],
                    TutorProfile.price_per_group_session <= budget_range['max']
                )
            )
        
        # Order by rating and experience
        query = query.order_by(
            desc(TutorProfile.rating),
            desc(TutorProfile.total_hours_taught)
        )
        
        return query.limit(10).all()
    
    def _recommend_tutors_for_step(self, tutors: List[TutorProfile], objective) -> List[Dict]:
        """Recommend best tutors for specific learning step"""
        tutor_recommendations = []
        
        for tutor in tutors:
            recommendation = {
                'tutor': tutor.to_dict(),
                'recommendation_score': self._calculate_tutor_step_score(tutor, objective),
                'match_reasons': self._get_match_reasons(tutor, objective)
            }
            tutor_recommendations.append(recommendation)
        
        # Sort by recommendation score
        tutor_recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return tutor_recommendations[:3]  # Top 3 recommendations
    
    def _calculate_tutor_step_score(self, tutor: TutorProfile, objective) -> float:
        """Calculate how suitable a tutor is for specific learning objective"""
        score = 0.0
        
        # Base score from overall rating
        score += (tutor.rating or 0) * 20
        
        # Experience in subject area
        for tutor_subject in tutor.subjects:
            if tutor_subject.subject_id == objective.subject_id:
                score += tutor_subject.experience_years * 2
                score += tutor_subject.teaching_experience_years * 3
                break
        
        # Verification bonus
        if tutor.is_verified:
            score += 15
        
        # Specialization bonus
        if objective.title.lower() in (tutor.description or '').lower():
            score += 10
        
        return score
    
    def _get_match_reasons(self, tutor: TutorProfile, objective) -> List[str]:
        """Get reasons why tutor is recommended for this objective"""
        reasons = []
        
        if tutor.rating and tutor.rating >= 4.5:
            reasons.append(f"Highly rated ({tutor.rating}/5 stars)")
        
        if tutor.is_verified:
            reasons.append("Verified tutor")
        
        for tutor_subject in tutor.subjects:
            if tutor_subject.subject_id == objective.subject_id:
                if tutor_subject.experience_years >= 5:
                    reasons.append(f"Experienced in {objective.title} ({tutor_subject.experience_years} years)")
                break
        
        if 'patient' in (tutor.description or '').lower():
            reasons.append("Known for patient teaching style")
        
        return reasons
    
    def _estimate_step_duration(self, objective, student_profile: Dict) -> int:
        """Estimate duration of learning step in hours"""
        # Base duration from objective
        base_duration = 10  # Default 10 hours
        
        # Adjust based on student's skill level
        skill_level = student_profile.get('skill_level', 'Beginner')
        if skill_level == 'Beginner':
            base_duration *= 1.5
        elif skill_level == 'Advanced':
            base_duration *= 0.8
        
        return max(2, int(base_duration))
    
    def _get_prerequisites(self, objective, step_number: int) -> List[str]:
        """Get prerequisites for learning step"""
        # For now, return empty - would be based on subject curriculum
        return []
    
    def _assess_step_difficulty(self, objective, student_profile: Dict) -> str:
        """Assess difficulty of learning step for student"""
        skill_level = student_profile.get('skill_level', 'Beginner')
        
        # Map skill level to difficulty
        difficulty_mapping = {
            'Beginner': 'Beginner',
            'Intermediate': 'Intermediate',
            'Advanced': 'Advanced'
        }
        
        return difficulty_mapping.get(skill_level, 'Beginner')
    
    def get_match_explanation(self, student_profile: Dict, tutor: TutorProfile) -> Dict:
        """Get detailed explanation of match score"""
        try:
            explanation = {
                'overall_score': 0.0,
                'factor_scores': {},
                'strengths': [],
                'areas_for_improvement': [],
                'recommendations': []
            }
            
            # Calculate detailed scores
            explanation['factor_scores'] = {
                'subject_match': self._calculate_subject_match(student_profile, tutor),
                'learning_style': self._calculate_learning_style_match(student_profile, tutor),
                'schedule_compatibility': self._calculate_schedule_match(student_profile, tutor),
                'budget_match': self._calculate_budget_match(student_profile, tutor),
                'location_preference': self._calculate_location_match(student_profile, tutor),
                'personality_match': self._calculate_personality_match(student_profile, tutor)
            }
            
            # Calculate overall score
            total_score = 0.0
            for factor, score in explanation['factor_scores'].items():
                weight = self.matching_weights.get(factor, 0.0)
                total_score += score * weight
                explanation['overall_score'] = total_score
            
            # Identify strengths (scores > 70)
            for factor, score in explanation['factor_scores'].items():
                if score >= 70:
                    explanation['strengths'].append({
                        'factor': factor,
                        'score': score,
                        'description': self._get_factor_description(factor, score)
                    })
            
            # Identify areas for improvement (scores < 50)
            for factor, score in explanation['factor_scores'].items():
                if score < 50:
                    explanation['areas_for_improvement'].append({
                        'factor': factor,
                        'score': score,
                        'suggestion': self._get_improvement_suggestion(factor, score)
                    })
            
            # Generate recommendations
            explanation['recommendations'] = self._generate_recommendations(explanation['factor_scores'])
            
            return explanation
            
        except Exception as e:
            current_app.logger.error(f"Error getting match explanation: {str(e)}")
            return {}
    
    def _get_factor_description(self, factor: str, score: float) -> str:
        """Get description for factor score"""
        if score >= 90:
            return "Excellent match"
        elif score >= 75:
            return "Very good match"
        elif score >= 60:
            return "Good match"
        elif score >= 40:
            return "Fair match"
        else:
            return "Poor match"
    
    def _get_improvement_suggestion(self, factor: str, score: float) -> str:
        """Get improvement suggestion for factor"""
        suggestions = {
            'subject_match': "Consider tutors who teach more of your preferred subjects",
            'learning_style': "Look for tutors with teaching methods that match your learning style",
            'schedule_compatibility': "Find tutors with more flexible scheduling options",
            'budget_match': "Consider adjusting your budget range or looking for tutors with different pricing",
            'location_preference': "Expand your search to include online tutors or nearby locations",
            'personality_match': "Read tutor reviews to find teaching styles that match your preferences"
        }
        
        return suggestions.get(factor, "Consider adjusting your search criteria")
    
    def _generate_recommendations(self, factor_scores: Dict) -> List[str]:
        """Generate recommendations based on factor scores"""
        recommendations = []
        
        # Low score recommendations
        if factor_scores.get('budget_match', 0) < 50:
            recommendations.append("Consider expanding your budget range for more options")
        
        if factor_scores.get('subject_match', 0) < 60:
            recommendations.append("Try searching with broader subject terms or related subjects")
        
        if factor_scores.get('location_preference', 0) < 50:
            recommendations.append("Include online tutors in your search for more options")
        
        if factor_scores.get('schedule_compatibility', 0) < 50:
            recommendations.append("Look for tutors with more flexible availability")
        
        # High score recommendations
        if factor_scores.get('personality_match', 0) > 80:
            recommendations.append("This tutor's teaching style seems to match well with your preferences")
        
        return recommendations