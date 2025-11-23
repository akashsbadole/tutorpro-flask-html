"""
Student Routes for TutorPro Marketplace
Student dashboard and profile management routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import joinedload

from app import db
from app.models.user import User
from app.models.student import (
    LearnerProfile, StudentLearningGoal, StudentSubjectPreference, 
    StudentWishlist, LearningProgress, ProgressEntry, LearningMilestone,
    StudentComparison
)
from app.models.tutor import TutorProfile
from app.models.category import Subject
from app.models.booking import Booking
from app.models.demo import DemoSession, DemoSessionStatus
from app.models.verification import TutorRating, Review
from app.services.student_matching import StudentMatchingService
from app.services.demo_booking import DemoBookingService

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard with learning progress and recommendations"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get student profile
        learner_profile = LearnerProfile.query.filter_by(user_id=current_user.id).first()
        
        # Get dashboard statistics
        stats = get_dashboard_stats(current_user.id)
        
        # Get learning progress
        learning_progress = get_learning_progress(current_user.id, limit=5)
        
        # Get upcoming sessions (both bookings and demos)
        upcoming_sessions = get_upcoming_sessions(current_user.id, limit=5)
        
        # Get recommended tutors
        recommended_tutors = get_recommended_tutors(current_user.id, limit=3)
        
        # Get active learning goals
        learning_goals = get_active_learning_goals(current_user.id, limit=3)
        
        # Get recent achievements
        achievements = get_recent_achievements(current_user.id, limit=6)
        
        return render_template('student/dashboard.html',
                            stats=stats,
                            learning_progress=learning_progress,
                            upcoming_sessions=upcoming_sessions,
                            recommended_tutors=recommended_tutors,
                            learning_goals=learning_goals,
                            achievements=achievements)
    
    except Exception as e:
        current_app.logger.error(f"Error loading student dashboard: {str(e)}")
        flash('Error loading dashboard. Please try again.', 'danger')
        return redirect(url_for('main.index'))

@student_bp.route('/profile')
@login_required
def profile():
    """Student profile page"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        learner_profile = LearnerProfile.query.filter_by(user_id=current_user.id).first()
        
        if not learner_profile:
            # Create default profile
            learner_profile = LearnerProfile(user_id=current_user.id)
            db.session.add(learner_profile)
            db.session.commit()
        
        # Get subject preferences
        subject_preferences = StudentSubjectPreference.query.filter_by(
            learner_profile_id=learner_profile.id, is_active=True
        ).options(joinedload(StudentSubjectPreference.subject)).all()
        
        # Get learning goals
        learning_goals = StudentLearningGoal.query.filter_by(
            learner_profile_id=learner_profile.id, is_active=True
        ).options(joinedload(StudentLearningGoal.subject)).all()
        
        return render_template('student/profile.html',
                            learner_profile=learner_profile,
                            subject_preferences=subject_preferences,
                            learning_goals=learning_goals)
    
    except Exception as e:
        current_app.logger.error(f"Error loading student profile: {str(e)}")
        flash('Error loading profile. Please try again.', 'danger')
        return redirect(url_for('student.dashboard'))

@student_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit student profile"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        learner_profile = LearnerProfile.query.filter_by(user_id=current_user.id).first()
        
        if not learner_profile:
            learner_profile = LearnerProfile(user_id=current_user.id)
            db.session.add(learner_profile)
        
        if request.method == 'POST':
            # Update profile fields
            learner_profile.bio = request.form.get('bio')
            learner_profile.timezone = request.form.get('timezone', 'UTC')
            learner_profile.learning_style = request.form.get('learning_style')
            learner_profile.experience_level = request.form.get('experience_level')
            learner_profile.preferred_tutor_gender = request.form.get('preferred_tutor_gender', 'Any')
            learner_profile.preferred_session_duration = int(request.form.get('preferred_session_duration', 60))
            learner_profile.preferred_session_frequency = request.form.get('preferred_session_frequency', 'Weekly')
            learner_profile.flexible_scheduling = 'flexible_scheduling' in request.form
            learner_profile.budget_range_min = float(request.form.get('budget_range_min')) if request.form.get('budget_range_min') else None
            learner_profile.budget_range_max = float(request.form.get('budget_range_max')) if request.form.get('budget_range_max') else None
            learner_profile.city = request.form.get('city')
            learner_profile.state = request.form.get('state')
            learner_profile.country = request.form.get('country')
            learner_profile.preferred_contact_method = request.form.get('preferred_contact_method', 'email')
            learner_profile.communication_frequency = request.form.get('communication_frequency', 'moderate')
            learner_profile.profile_visibility = request.form.get('profile_visibility', 'public')
            learner_profile.show_real_name = 'show_real_name' in request.form
            learner_profile.allow_contact_requests = 'allow_contact_requests' in request.form
            
            # Handle JSON fields
            preferred_languages = request.form.getlist('preferred_languages')
            learner_profile.preferred_languages = preferred_languages if preferred_languages else []
            
            preferred_teaching_modes = request.form.getlist('preferred_teaching_modes')
            learner_profile.preferred_teaching_modes = preferred_teaching_modes if preferred_teaching_modes else ['online']
            
            availability_days = request.form.getlist('availability_days')
            availability_times = {}
            for day in availability_days:
                time_field = f'availability_time_{day}'
                if request.form.get(time_field):
                    availability_times[day] = request.form.get(time_field)
            learner_profile.availability = availability_times if availability_times else {}
            
            # Update completion percentage
            learner_profile.update_profile_completion()
            
            db.session.commit()
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('student.profile'))
        
        # Get available subjects for preferences
        subjects = Subject.query.filter_by(is_active=True).order_by('name').all()
        
        return render_template('student/edit_profile.html',
                            learner_profile=learner_profile,
                            subjects=subjects)
    
    except Exception as e:
        current_app.logger.error(f"Error editing student profile: {str(e)}")
        flash('Error updating profile. Please try again.', 'danger')
        return redirect(url_for('student.profile'))

@student_bp.route('/progress')
@login_required
def progress():
    """Detailed learning progress page"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get all learning progress
        learning_progress = get_learning_progress(current_user.id)
        
        # Get progress entries for detailed view
        progress_entries = ProgressEntry.query.join(LearningProgress).filter(
            LearningProgress.learner_profile_id == current_user.id
        ).order_by(desc(ProgressEntry.entry_date)).limit(20).all()
        
        return render_template('student/progress.html',
                            learning_progress=learning_progress,
                            progress_entries=progress_entries)
    
    except Exception as e:
        current_app.logger.error(f"Error loading progress page: {str(e)}")
        flash('Error loading progress. Please try again.', 'danger')
        return redirect(url_for('student.dashboard'))

@student_bp.route('/learning-goals')
@login_required
def learning_goals():
    """Learning goals management page"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        learner_profile = LearnerProfile.query.filter_by(user_id=current_user.id).first()
        
        if not learner_profile:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('student.edit_profile'))
        
        # Get learning goals
        goals = StudentLearningGoal.query.filter_by(
            learner_profile_id=learner_profile.id
        ).options(joinedload(StudentLearningGoal.subject),
                 joinedload(StudentLearningGoal.milestones)).all()
        
        # Get available subjects
        subjects = Subject.query.filter_by(is_active=True).order_by('name').all()
        
        return render_template('student/learning_goals.html',
                            goals=goals,
                            subjects=subjects)
    
    except Exception as e:
        current_app.logger.error(f"Error loading learning goals: {str(e)}")
        flash('Error loading learning goals. Please try again.', 'danger')
        return redirect(url_for('student.dashboard'))

@student_bp.route('/learning-goals/add', methods=['POST'])
@login_required
def add_learning_goal():
    """Add new learning goal"""
    if not current_user.is_learner():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        learner_profile = LearnerProfile.query.filter_by(user_id=current_user.id).first()
        if not learner_profile:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
        
        goal = StudentLearningGoal(
            learner_profile_id=learner_profile.id,
            goal_type=request.form.get('goal_type'),
            subject_id=int(request.form.get('subject_id')) if request.form.get('subject_id') else None,
            title=request.form.get('title'),
            description=request.form.get('description'),
            target_date=datetime.fromisoformat(request.form.get('target_date')) if request.form.get('target_date') else None,
            priority=request.form.get('priority', 'medium')
        )
        
        db.session.add(goal)
        db.session.commit()
        
        return jsonify({'success': True, 'goal': goal.to_dict()})
    
    except Exception as e:
        current_app.logger.error(f"Error adding learning goal: {str(e)}")
        return jsonify({'success': False, 'message': 'Error adding goal'}), 500

@student_bp.route('/wishlist')
@login_required
def wishlist():
    """Student wishlist page"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        learner_profile = LearnerProfile.query.filter_by(user_id=current_user.id).first()
        
        if not learner_profile:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('student.edit_profile'))
        
        # Get wishlist items
        wishlist_items = StudentWishlist.query.filter_by(
            learner_profile_id=learner_profile.id, is_active=True
        ).options(joinedload(StudentWishlist.tutor)).all()
        
        return render_template('student/wishlist.html', wishlist_items=wishlist_items)
    
    except Exception as e:
        current_app.logger.error(f"Error loading wishlist: {str(e)}")
        flash('Error loading wishlist. Please try again.', 'danger')
        return redirect(url_for('student.dashboard'))

@student_bp.route('/wishlist/add/<int:tutor_id>', methods=['POST'])
@login_required
def add_to_wishlist(tutor_id):
    """Add tutor to wishlist"""
    if not current_user.is_learner():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        learner_profile = LearnerProfile.query.filter_by(user_id=current_user.id).first()
        if not learner_profile:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
        
        # Check if already in wishlist
        existing = StudentWishlist.query.filter_by(
            learner_profile_id=learner_profile.id,
            tutor_id=tutor_id,
            is_active=True
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Already in wishlist'}), 400
        
        # Add to wishlist
        wishlist_item = StudentWishlist(
            learner_profile_id=learner_profile.id,
            tutor_id=tutor_id,
            notes=request.form.get('notes', ''),
            priority=request.form.get('priority', 'medium')
        )
        
        db.session.add(wishlist_item)
        db.session.commit()
        
        return jsonify({'success': True, 'wishlist_item': wishlist_item.to_dict()})
    
    except Exception as e:
        current_app.logger.error(f"Error adding to wishlist: {str(e)}")
        return jsonify({'success': False, 'message': 'Error adding to wishlist'}), 500

@student_bp.route('/compare')
@login_required
def compare():
    """Tutor comparison page"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        learner_profile = LearnerProfile.query.filter_by(user_id=current_user.id).first()
        
        if not learner_profile:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('student.edit_profile'))
        
        # Get tutor IDs from request
        tutor_ids = request.args.get('tutors', '').split(',')
        tutor_ids = [int(tid) for tid in tutor_ids if tid.isdigit()]
        
        if len(tutor_ids) < 2:
            flash('Please select at least 2 tutors to compare.', 'info')
            return redirect(url_for('search.tutor_discovery'))
        
        # Get tutor profiles
        tutors = TutorProfile.query.filter(
            TutorProfile.user_id.in_(tutor_ids)
        ).options(joinedload(TutorProfile.user),
                 joinedload(TutorProfile.subjects),
                 joinedload(TutorProfile.rating_summary)).all()
        
        if len(tutors) < 2:
            flash('One or more tutors not found.', 'warning')
            return redirect(url_for('search.tutor_discovery'))
        
        return render_template('student/compare.html', tutors=tutors)
    
    except Exception as e:
        current_app.logger.error(f"Error loading comparison page: {str(e)}")
        flash('Error loading comparison. Please try again.', 'danger')
        return redirect(url_for('student.dashboard'))

@student_bp.route('/bookings')
@login_required
def bookings():
    """Student bookings page"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get filter parameters
        status_filter = request.args.get('status', '')
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Build query
        query = Booking.query.filter_by(student_id=current_user.id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # Add pagination
        bookings = query.options(
            joinedload(Booking.tutor),
            joinedload(Booking.subject)
        ).order_by(desc(Booking.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('student/bookings.html', bookings=bookings)
    
    except Exception as e:
        current_app.logger.error(f"Error loading bookings: {str(e)}")
        flash('Error loading bookings. Please try again.', 'danger')
        return redirect(url_for('student.dashboard'))

@student_bp.route('/achievements')
@login_required
def achievements():
    """Student achievements page"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        learner_profile = LearnerProfile.query.filter_by(user_id=current_user.id).first()
        
        if not learner_profile:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('student.edit_profile'))
        
        # Get achievements from learning progress
        achievements = get_student_achievements(current_user.id)
        
        return render_template('student/achievements.html', achievements=achievements)
    
    except Exception as e:
        current_app.logger.error(f"Error loading achievements: {str(e)}")
        flash('Error loading achievements. Please try again.', 'danger')
        return redirect(url_for('student.dashboard'))

# Helper functions

def get_dashboard_stats(student_id):
    """Get dashboard statistics for student"""
    try:
        # Total sessions completed
        total_sessions = Booking.query.filter_by(
            student_id=student_id, status='completed'
        ).count()
        
        # Active subjects
        active_subjects = db.session.query(func.count(func.distinct(Booking.subject_id))).filter_by(
            student_id=student_id, status='completed'
        ).scalar() or 0
        
        # Learning hours
        learning_hours = db.session.query(func.sum(Booking.duration_minutes)).filter_by(
            student_id=student_id, status='completed'
        ).scalar() or 0
        learning_hours = learning_hours / 60  # Convert to hours
        
        # Achievements (simplified count)
        achievements = get_student_achievements(student_id)
        achievement_count = len(achievements)
        
        return {
            'total_sessions': total_sessions,
            'active_subjects': active_subjects,
            'learning_hours': round(learning_hours, 1),
            'achievements': achievement_count
        }
    
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {str(e)}")
        return {
            'total_sessions': 0,
            'active_subjects': 0,
            'learning_hours': 0,
            'achievements': 0
        }

def get_learning_progress(student_id, limit=None):
    """Get student's learning progress"""
    try:
        learner_profile = LearnerProfile.query.filter_by(user_id=student_id).first()
        if not learner_profile:
            return []
        
        query = LearningProgress.query.filter_by(
            learner_profile_id=learner_profile.id, is_active=True
        ).options(joinedload(LearningProgress.subject))
        
        if limit:
            query = query.limit(limit)
        
        return query.order_by(desc(LearningProgress.last_updated)).all()
    
    except Exception as e:
        current_app.logger.error(f"Error getting learning progress: {str(e)}")
        return []

def get_upcoming_sessions(student_id, limit=None):
    """Get upcoming sessions for student"""
    try:
        now = datetime.now(timezone.utc)
        
        # Get upcoming bookings
        booking_query = Booking.query.filter(
            and_(
                Booking.student_id == student_id,
                Booking.scheduled_start_time > now,
                Booking.status.in_(['confirmed', 'upcoming'])
            )
        ).options(joinedload(Booking.tutor), joinedload(Booking.subject))
        
        # Get upcoming demo sessions
        demo_query = DemoSession.query.filter(
            and_(
                DemoSession.student_id == student_id,
                DemoSession.scheduled_date_time > now,
                DemoSession.status.in_([DemoSessionStatus.ACCEPTED, DemoSessionStatus.SCHEDULED])
            )
        ).options(joinedload(DemoSession.tutor), joinedload(DemoSession.subject))
        
        # Combine and sort
        sessions = []
        
        # Add bookings
        bookings = booking_query.all()
        for booking in bookings:
            sessions.append({
                'type': 'booking',
                'id': booking.id,
                'tutor': booking.tutor,
                'subject': booking.subject,
                'scheduled_start_time': booking.scheduled_start_time,
                'meeting_link': booking.meeting_link
            })
        
        # Add demos
        demos = demo_query.all()
        for demo in demos:
            sessions.append({
                'type': 'demo',
                'id': demo.id,
                'tutor': demo.tutor,
                'subject': demo.subject,
                'scheduled_start_time': demo.scheduled_date_time,
                'meeting_link': demo.meeting_link
            })
        
        # Sort by start time
        sessions.sort(key=lambda x: x['scheduled_start_time'])
        
        if limit:
            sessions = sessions[:limit]
        
        return sessions
    
    except Exception as e:
        current_app.logger.error(f"Error getting upcoming sessions: {str(e)}")
        return []

def get_recommended_tutors(student_id, limit=3):
    """Get recommended tutors for student"""
    try:
        matching_service = StudentMatchingService()
        matches = matching_service.find_best_matches(student_id, limit=limit)
        
        return [match['tutor'] for match in matches]
    
    except Exception as e:
        current_app.logger.error(f"Error getting recommended tutors: {str(e)}")
        return []

def get_active_learning_goals(student_id, limit=None):
    """Get active learning goals for student"""
    try:
        learner_profile = LearnerProfile.query.filter_by(user_id=student_id).first()
        if not learner_profile:
            return []
        
        query = StudentLearningGoal.query.filter_by(
            learner_profile_id=learner_profile.id, is_active=True
        ).options(joinedload(StudentLearningGoal.subject))
        
        if limit:
            query = query.limit(limit)
        
        return query.order_by(StudentLearningGoal.priority.desc(), StudentLearningGoal.created_at.desc()).all()
    
    except Exception as e:
        current_app.logger.error(f"Error getting learning goals: {str(e)}")
        return []

def get_recent_achievements(student_id, limit=6):
    """Get recent achievements for student"""
    try:
        # This is a simplified version - in production would have a proper achievements system
        achievements = []
        
        # Check for various achievement types based on student activity
        learner_profile = LearnerProfile.query.filter_by(user_id=student_id).first()
        if not learner_profile:
            return achievements
        
        # Session milestones
        total_sessions = Booking.query.filter_by(
            student_id=student_id, status='completed'
        ).count()
        
        if total_sessions >= 1:
            achievements.append({
                'id': 'first_session',
                'title': 'First Session',
                'icon_class': 'fas fa-graduation-cap',
                'description': 'Completed your first learning session'
            })
        
        if total_sessions >= 10:
            achievements.append({
                'id': 'ten_sessions',
                'title': 'Dedicated Learner',
                'icon_class': 'fas fa-star',
                'description': 'Completed 10 learning sessions'
            })
        
        # Learning hours milestones
        total_hours = db.session.query(func.sum(Booking.duration_minutes)).filter_by(
            student_id=student_id, status='completed'
        ).scalar() or 0
        total_hours = total_hours / 60
        
        if total_hours >= 10:
            achievements.append({
                'id': 'ten_hours',
                'title': '10 Hours Learned',
                'icon_class': 'fas fa-clock',
                'description': 'Accumulated 10 hours of learning'
            })
        
        # Subject diversity
        subject_count = db.session.query(func.count(func.distinct(Booking.subject_id))).filter_by(
            student_id=student_id, status='completed'
        ).scalar() or 0
        
        if subject_count >= 3:
            achievements.append({
                'id': 'multi_subject',
                'title': 'Multi-Subject Learner',
                'icon_class': 'fas fa-book',
                'description': 'Studied 3 or more subjects'
            })
        
        return achievements[:limit]
    
    except Exception as e:
        current_app.logger.error(f"Error getting achievements: {str(e)}")
        return []

def get_student_achievements(student_id):
    """Get all achievements for student"""
    return get_recent_achievements(student_id, limit=50)