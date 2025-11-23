"""
AI Service for TutorPro Marketplace
Provides AI-powered features including tutor matching, translation, and content generation
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from flask import current_app
from datetime import datetime
import requests
from app import db
from app.models.user import User
from app.models.tutor import TutorProfile, TutorSubject
from app.models.category import Subject
from app.models.student import LearnerProfile
from app.models.booking import Booking


class AIService:
    """AI-powered services for TutorPro platform"""
    
    def __init__(self):
        self.openai_api_key = current_app.config.get('OPENAI_API_KEY')
        self.google_translate_key = current_app.config.get('GOOGLE_TRANSLATE_API_KEY')
        self.base_url = "https://api.openai.com/v1"
        self.translate_url = "https://translation.googleapis.com/language/translate/v2"
    
    def get_tutor_recommendations(self, student_id: int, limit: int = 10) -> List[Dict]:
        """
        Get AI-powered tutor recommendations for a student
        
        Args:
            student_id: Student user ID
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended tutors with scores and reasons
        """
        try:
            # Get student profile
            student = User.query.get(student_id)
            if not student or not student.is_learner():
                return []
            
            learner_profile = getattr(student, 'learner_profile', None)
            if not learner_profile:
                return []
            
            # Get all active tutors
            tutors = TutorProfile.query.filter_by(is_active=True, is_verified=True).all()
            
            recommendations = []
            
            for tutor in tutors:
                score = self._calculate_tutor_match_score(student, tutor, learner_profile)
                if score > 0.3:  # Minimum threshold for recommendations
                    recommendations.append({
                        'tutor_id': tutor.id,
                        'tutor': tutor.to_dict(),
                        'score': round(score, 3),
                        'reasons': self._get_match_reasons(student, tutor, learner_profile, score)
                    })
            
            # Sort by score and limit results
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            current_app.logger.error(f"Error getting AI tutor recommendations: {str(e)}")
            return []
    
    def _calculate_tutor_match_score(self, student: User, tutor: TutorProfile, learner_profile: LearnerProfile) -> float:
        """Calculate AI-powered match score between student and tutor"""
        score = 0.0
        
        try:
            # Subject alignment (40% weight)
            subject_score = self._calculate_subject_alignment(student, tutor)
            score += subject_score * 0.4
            
            # Learning goals compatibility (25% weight)
            goals_score = self._calculate_goals_compatibility(learner_profile, tutor)
            score += goals_score * 0.25
            
            # Schedule compatibility (20% weight)
            schedule_score = self._calculate_schedule_compatibility(student, tutor)
            score += schedule_score * 0.2
            
            # Personality/teaching style match (15% weight)
            personality_score = self._calculate_personality_match(learner_profile, tutor)
            score += personality_score * 0.15
            
            return min(score, 1.0)
            
        except Exception as e:
            current_app.logger.error(f"Error calculating match score: {str(e)}")
            return 0.0
    
    def _calculate_subject_alignment(self, student: User, tutor: TutorProfile) -> float:
        """Calculate subject alignment score"""
        try:
            # Get student's interested subjects (from learning goals or bookings)
            student_subjects = set()
            
            # From learning goals
            learner_profile = getattr(student, 'learner_profile', None)
            if learner_profile and learner_profile.learning_goals:
                goals = learner_profile.learning_goals.lower()
                common_subjects = ['math', 'english', 'science', 'physics', 'chemistry', 'biology', 
                                 'programming', 'python', 'javascript', 'music', 'guitar', 'piano']
                for subject in common_subjects:
                    if subject in goals:
                        student_subjects.add(subject)
            
            # From past bookings
            past_bookings = Booking.query.filter_by(student_id=student.id).join('course').all()
            for booking in past_bookings:
                if booking.course and booking.course.subject:
                    student_subjects.add(booking.course.subject.name.lower())
            
            # Get tutor's subjects
            tutor_subjects = set()
            for tutor_subject in tutor.subjects:
                if tutor_subject.subject:
                    tutor_subjects.add(tutor_subject.subject.name.lower())
            
            if not student_subjects or not tutor_subjects:
                return 0.5  # Neutral score if no data
            
            # Calculate intersection
            intersection = student_subjects.intersection(tutor_subjects)
            alignment_score = len(intersection) / len(student_subjects.union(tutor_subjects))
            
            return alignment_score
            
        except Exception as e:
            current_app.logger.error(f"Error calculating subject alignment: {str(e)}")
            return 0.0
    
    def _calculate_goals_compatibility(self, learner_profile: LearnerProfile, tutor: TutorProfile) -> float:
        """Calculate learning goals compatibility with tutor's expertise"""
        try:
            if not learner_profile or not learner_profile.learning_goals:
                return 0.5
            
            goals = learner_profile.learning_goals.lower()
            
            # Define goal patterns and tutor specializations
            goal_patterns = {
                'exam': ['exam', 'test', 'sat', 'gre', 'ielts', 'toefl'],
                'homework': ['homework', 'assignment', 'help'],
                'conversation': ['speaking', 'conversation', 'talk', 'practice'],
                'beginner': ['beginner', 'basic', 'foundation', 'intro'],
                'advanced': ['advanced', 'expert', 'professional', 'master'],
                'business': ['business', 'professional', 'corporate', 'work'],
                'academic': ['academic', 'school', 'college', 'university', 'study']
            }
            
            # Check tutor's description and title for matching specializations
            tutor_text = f"{tutor.description or ''} {tutor.title or ''} {tutor.tagline or ''}".lower()
            
            compatibility_score = 0.0
            matched_goals = 0
            
            for goal_type, patterns in goal_patterns.items():
                goal_matches = any(pattern in goals for pattern in patterns)
                tutor_specializes = any(pattern in tutor_text for pattern in patterns)
                
                if goal_matches and tutor_specializes:
                    compatibility_score += 1.0
                    matched_goals += 1
                elif goal_matches:
                    compatibility_score += 0.3  # Partial match
                    matched_goals += 1
            
            if matched_goals == 0:
                return 0.5
            
            return min(compatibility_score / matched_goals, 1.0)
            
        except Exception as e:
            current_app.logger.error(f"Error calculating goals compatibility: {str(e)}")
            return 0.0
    
    def _calculate_schedule_compatibility(self, student: User, tutor: TutorProfile) -> float:
        """Calculate schedule compatibility based on availability patterns"""
        try:
            # Get student's booking patterns
            student_bookings = Booking.query.filter_by(student_id=student.id).all()
            
            if not student_bookings:
                return 0.7  # Neutral score for new students
            
            # Analyze student's preferred days and times
            preferred_hours = {}
            preferred_days = set()
            
            for booking in student_bookings:
                if booking.scheduled_time:
                    hour = booking.scheduled_time.hour
                    day = booking.scheduled_time.weekday()
                    
                    preferred_hours[hour] = preferred_hours.get(hour, 0) + 1
                    preferred_days.add(day)
            
            # Get tutor's availability
            tutor_availability = tutor.availability_slots or []
            
            if not tutor_availability:
                return 0.3  # Low score if no availability data
            
            # Calculate overlap
            available_hours = set()
            available_days = set()
            
            for avail in tutor_availability:
                if avail.is_available:
                    available_days.add(avail.day_of_week)
                    # Convert time range to hours
                    start_hour = avail.start_time.hour
                    end_hour = avail.end_time.hour
                    for hour in range(start_hour, min(end_hour, 24)):
                        available_hours.add(hour)
            
            # Calculate compatibility scores
            day_overlap = len(preferred_days.intersection(available_days)) / len(preferred_days) if preferred_days else 0
            hour_overlap = len(set(preferred_hours.keys()).intersection(available_hours)) / len(preferred_hours) if preferred_hours else 0
            
            # Weighted average
            schedule_score = (day_overlap * 0.6 + hour_overlap * 0.4)
            
            return min(schedule_score, 1.0)
            
        except Exception as e:
            current_app.logger.error(f"Error calculating schedule compatibility: {str(e)}")
            return 0.0
    
    def _calculate_personality_match(self, learner_profile: LearnerProfile, tutor: TutorProfile) -> float:
        """Calculate personality/teaching style match"""
        try:
            # This is a simplified personality matching algorithm
            # In production, this could use more sophisticated ML models
            
            learning_style_keywords = {
                'visual': ['visual', 'see', 'diagram', 'chart', 'graph', 'picture'],
                'auditory': ['listen', 'hear', 'audio', 'verbal', 'discussion', 'talk'],
                'kinesthetic': ['hands-on', 'practice', 'do', 'active', 'movement', 'try'],
                'structured': ['structured', 'organized', 'step-by-step', 'systematic', 'clear'],
                'flexible': ['flexible', 'adaptive', 'customized', 'personalized', 'tailored']
            }
            
            # Analyze student's learning preferences
            student_text = f"{learner_profile.learning_goals or ''} {learner_profile.bio or ''}".lower()
            
            teaching_style_keywords = {
                'patient': ['patient', 'calm', 'understanding', 'supportive'],
                'enthusiastic': ['enthusiastic', 'energetic', 'passionate', 'excited'],
                'structured': ['structured', 'organized', 'methodical', 'systematic'],
                'creative': ['creative', 'innovative', 'imaginative', 'original'],
                'practical': ['practical', 'real-world', 'hands-on', 'applied']
            }
            
            # Analyze tutor's teaching style
            tutor_text = f"{tutor.description or ''} {tutor.teaching_style or ''} {tutor.tagline or ''}".lower()
            
            # Calculate compatibility based on keyword matching
            compatibility_score = 0.0
            total_matches = 0
            
            for style, keywords in learning_style_keywords.items():
                student_prefers = any(keyword in student_text for keyword in keywords)
                tutor_provides = any(keyword in tutor_text for keyword in keywords)
                
                if student_prefers and tutor_provides:
                    compatibility_score += 1.0
                    total_matches += 1
                elif student_prefers:
                    compatibility_score += 0.3
                    total_matches += 1
            
            if total_matches == 0:
                return 0.6  # Neutral score
            
            return min(compatibility_score / total_matches, 1.0)
            
        except Exception as e:
            current_app.logger.error(f"Error calculating personality match: {str(e)}")
            return 0.0
    
    def _get_match_reasons(self, student: User, tutor: TutorProfile, learner_profile: LearnerProfile, score: float) -> List[str]:
        """Generate reasons for tutor recommendation"""
        reasons = []
        
        try:
            # Subject alignment
            if self._calculate_subject_alignment(student, tutor) > 0.6:
                reasons.append("Strong subject alignment with your learning goals")
            
            # Teaching style
            if self._calculate_goals_compatibility(learner_profile, tutor) > 0.7:
                reasons.append("Teaching style matches your learning preferences")
            
            # Schedule
            if self._calculate_schedule_compatibility(student, tutor) > 0.6:
                reasons.append("Flexible availability that fits your schedule")
            
            # Experience
            if tutor.total_hours_taught and tutor.total_hours_taught > 100:
                reasons.append(f"Experienced tutor with {tutor.total_hours_taught}+ hours taught")
            
            # Rating
            if tutor.rating and tutor.rating >= 4.5:
                reasons.append(f"Highly rated ({tutor.rating}⭐) by other students")
            
            # Special features
            if tutor.offers_free_trial:
                reasons.append("Offers free trial sessions")
            
            if len(tutor.languages_spoken) > 1:
                reasons.append(f"Speaks multiple languages: {', '.join(tutor.languages_spoken[:2])}")
            
            return reasons[:3]  # Return top 3 reasons
            
        except Exception as e:
            current_app.logger.error(f"Error generating match reasons: {str(e)}")
            return ["Great match for your learning needs"]
    
    def translate_text(self, text: str, target_language: str, source_language: str = 'auto') -> Dict:
        """
        Translate text using Google Translate API
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'es', 'hi', 'fr')
            source_language: Source language code (default: auto-detect)
            
        Returns:
            Dictionary with translation result
        """
        try:
            if not self.google_translate_key:
                return {
                    'success': False,
                    'error': 'Translation service not configured'
                }
            
            url = f"{self.translate_url}?key={self.google_translate_key}"
            
            data = {
                'q': text,
                'target': target_language,
                'source': source_language if source_language != 'auto' else None,
                'format': 'text'
            }
            
            response = requests.post(url, data=data)
            result = response.json()
            
            if 'data' in result and 'translations' in result['data']:
                translation = result['data']['translations'][0]
                return {
                    'success': True,
                    'translated_text': translation['translatedText'],
                    'detected_language': translation.get('detectedSourceLanguage'),
                    'source_language': source_language
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', {}).get('message', 'Translation failed')
                }
                
        except Exception as e:
            current_app.logger.error(f"Error translating text: {str(e)}")
            return {
                'success': False,
                'error': 'Translation service unavailable'
            }
    
    def generate_lesson_summary(self, session_content: str, subject: str = None) -> Dict:
        """
        Generate AI-powered lesson summary
        
        Args:
            session_content: Transcript or content of the session
            subject: Subject area for context
            
        Returns:
            Dictionary with lesson summary
        """
        try:
            if not self.openai_api_key:
                return self._generate_simple_summary(session_content, subject)
            
            # Prepare prompt for OpenAI
            prompt = f"""
            Please analyze the following tutoring session content and provide a comprehensive summary:
            
            Subject: {subject or 'General'}
            Session Content: {session_content}
            
            Please provide:
            1. Key topics covered
            2. Main concepts learned
            3. Practice exercises mentioned
            4. Homework assignments
            5. Next steps/recommendations
            
            Format the response as JSON with the following structure:
            {{
                "key_topics": ["topic1", "topic2"],
                "main_concepts": ["concept1", "concept2"],
                "practice_exercises": ["exercise1", "exercise2"],
                "homework": ["homework1", "homework2"],
                "next_steps": ["step1", "step2"],
                "summary": "Brief summary of the session"
            }}
            """
            
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'You are an expert educational assistant that summarizes tutoring sessions.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 500,
                'temperature': 0.3
            }
            
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=data)
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                try:
                    summary_data = json.loads(content)
                    return {
                        'success': True,
                        'summary': summary_data.get('summary', ''),
                        'key_topics': summary_data.get('key_topics', []),
                        'main_concepts': summary_data.get('main_concepts', []),
                        'practice_exercises': summary_data.get('practice_exercises', []),
                        'homework': summary_data.get('homework', []),
                        'next_steps': summary_data.get('next_steps', [])
                    }
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {
                        'success': True,
                        'summary': content,
                        'key_topics': [],
                        'main_concepts': [],
                        'practice_exercises': [],
                        'homework': [],
                        'next_steps': []
                    }
            else:
                return self._generate_simple_summary(session_content, subject)
                
        except Exception as e:
            current_app.logger.error(f"Error generating lesson summary: {str(e)}")
            return self._generate_simple_summary(session_content, subject)
    
    def _generate_simple_summary(self, content: str, subject: str = None) -> Dict:
        """Generate simple summary without AI"""
        try:
            # Extract key sentences and topics
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            
            # Simple keyword extraction
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
            
            words = re.findall(r'\b[a-zA-Z]+\b', content.lower())
            word_freq = {}
            for word in words:
                if word not in common_words and len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            key_topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            key_topics = [topic[0].title() for topic in key_topics]
            
            return {
                'success': True,
                'summary': f"Session covered topics including: {', '.join(key_topics)}. {len(sentences)} main points were discussed.",
                'key_topics': key_topics,
                'main_concepts': key_topics[:3],
                'practice_exercises': [],
                'homework': [],
                'next_steps': ['Review key concepts', 'Practice exercises']
            }
            
        except Exception as e:
            current_app.logger.error(f"Error generating simple summary: {str(e)}")
            return {
                'success': False,
                'error': 'Unable to generate summary'
            }
    
    def check_plagiarism(self, text: str) -> Dict:
        """
        Basic plagiarism detection (simplified implementation)
        
        Args:
            text: Text to check for plagiarism
            
        Returns:
            Dictionary with plagiarism analysis
        """
        try:
            # This is a simplified plagiarism detection
            # In production, you would integrate with services like Turnitin, Grammarly, etc.
            
            # Remove common words and create n-grams
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            words = [w.lower() for w in re.findall(r'\b\w+\b', text) if w.lower() not in common_words]
            
            # Create 4-grams
            ngrams = []
            for i in range(len(words) - 3):
                ngram = ' '.join(words[i:i+4])
                ngrams.append(ngram)
            
            # Calculate uniqueness score (simplified)
            unique_ngrams = len(set(ngrams))
            total_ngrams = len(ngrams)
            uniqueness_score = unique_ngrams / total_ngrams if total_ngrams > 0 else 1.0
            
            # Check for common phrases that might indicate copying
            suspicious_phrases = [
                'according to wikipedia',
                'as mentioned in',
                'based on research',
                'research shows that',
                'studies have shown',
                'it is well known that'
            ]
            
            suspicious_count = sum(1 for phrase in suspicious_phrases if phrase.lower() in text.lower())
            
            plagiarism_score = max(0, (1.0 - uniqueness_score) + (suspicious_count * 0.1))
            
            return {
                'success': True,
                'plagiarism_score': round(plagiarism_score, 3),
                'uniqueness_score': round(uniqueness_score, 3),
                'is_suspicious': plagiarism_score > 0.3,
                'suspicious_phrases_found': suspicious_count,
                'recommendation': 'Original content' if plagiarism_score < 0.3 else 'Review for originality'
            }
            
        except Exception as e:
            current_app.logger.error(f"Error checking plagiarism: {str(e)}")
            return {
                'success': False,
                'error': 'Plagiarism check failed'
            }
    
    def generate_session_transcript(self, audio_file_path: str) -> Dict:
        """
        Generate transcript from audio file (placeholder implementation)
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Dictionary with transcript result
        """
        try:
            # This is a placeholder implementation
            # In production, you would integrate with speech-to-text services
            # like Google Speech-to-Text, Azure Speech, or OpenAI Whisper
            
            return {
                'success': False,
                'error': 'Speech-to-text service not configured',
                'message': 'Audio transcription requires integration with speech recognition service'
            }
            
        except Exception as e:
            current_app.logger.error(f"Error generating transcript: {str(e)}")
            return {
                'success': False,
                'error': 'Transcription failed'
            }
