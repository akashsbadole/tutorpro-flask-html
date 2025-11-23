"""
Demo Booking Routes for TutorPro Marketplace
Demo session booking and management routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import joinedload

from app import db
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.category import Subject
from app.models.demo import (
    DemoSession, DemoAvailability, DemoTemplate, DemoFeedback, DemoAnalytics,
    DemoSessionStatus, DemoSessionType
)
from app.models.student import LearnerProfile
from app.services.demo_booking import DemoBookingService

demo_bp = Blueprint('demo', __name__, url_prefix='/demo')

@demo_bp.route('/book')
@login_required
def book_demo():
    """Book a demo session page"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get subjects for dropdown
        subjects = Subject.query.filter_by(is_active=True).order_by('name').all()
        
        # Get popular tutors (for recommendations)
        popular_tutors = TutorProfile.query.filter_by(is_active=True).filter(
            TutorProfile.rating >= 4.0
        ).options(joinedload(TutorProfile.user)).limit(6).all()
        
        return render_template('demo/book_demo.html',
                            subjects=subjects,
                            popular_tutors=popular_tutors)
    
    except Exception as e:
        current_app.logger.error(f"Error loading demo booking page: {str(e)}")
        flash('Error loading demo booking page. Please try again.', 'danger')
        return redirect(url_for('main.index'))

@demo_bp.route('/tutors/<int:tutor_id>')
@login_required
def tutor_demo_info(tutor_id):
    """Tutor demo information and availability page"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get tutor profile
        tutor = User.query.filter_by(id=tutor_id, role='Tutor').first()
        if not tutor:
            flash('Tutor not found.', 'error')
            return redirect(url_for('demo.book_demo'))
        
        tutor_profile = TutorProfile.query.filter_by(user_id=tutor_id).first()
        if not tutor_profile or not tutor_profile.is_active:
            flash('Tutor profile not available.', 'error')
            return redirect(url_for('demo.book_demo'))
        
        # Get subjects tutor teaches
        subjects = [tutor_subject.subject for tutor_subject in tutor_profile.subjects if tutor_subject.is_active]
        
        # Get demo templates
        demo_templates = DemoTemplate.query.filter_by(
            tutor_id=tutor_id, is_active=True
        ).options(joinedload(DemoTemplate.subject)).all()
        
        # Get availability for next 14 days
        demo_service = DemoBookingService()
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=14)
        availability = demo_service.get_tutor_demo_availability(tutor_id, start_date, end_date)
        
        # Get demo reviews
        demo_reviews = DemoFeedback.query.join(DemoSession).filter(
            and_(
                DemoSession.tutor_id == tutor_id,
                DemoSession.status == DemoSessionStatus.COMPLETED,
                DemoFeedback.provider_role == 'student'
            )
        ).order_by(desc(DemoFeedback.submitted_at)).limit(5).all()
        
        return render_template('demo/tutor_demo_info.html',
                            tutor=tutor,
                            tutor_profile=tutor_profile,
                            subjects=subjects,
                            demo_templates=demo_templates,
                            availability=availability,
                            demo_reviews=demo_reviews)
    
    except Exception as e:
        current_app.logger.error(f"Error loading tutor demo info: {str(e)}")
        flash('Error loading tutor information. Please try again.', 'danger')
        return redirect(url_for('demo.book_demo'))

@demo_bp.route('/request', methods=['POST'])
@login_required
def request_demo():
    """Request a demo session"""
    if not current_user.is_learner():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        # Get form data
        tutor_id = int(request.form.get('tutor_id'))
        subject_id = int(request.form.get('subject_id'))
        requested_datetime = datetime.fromisoformat(request.form.get('requested_datetime'))
        
        # Build session data
        session_data = {
            'session_title': request.form.get('session_title'),
            'session_description': request.form.get('session_description', ''),
            'session_type': request.form.get('session_type', 'One-on-One'),
            'duration_minutes': int(request.form.get('duration_minutes', 30)),
            'timezone': request.form.get('timezone', 'UTC'),
            'location_type': request.form.get('location_type', 'online'),
            'topics_to_cover': request.form.getlist('topics_to_cover'),
            'learning_objectives': request.form.get('learning_objectives', ''),
            'materials_needed': request.form.getlist('materials_needed')
        }
        
        # Request demo session
        demo_service = DemoBookingService()
        success, message, demo_session = demo_service.request_demo_session(
            current_user.id, tutor_id, subject_id, requested_datetime, session_data
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'demo_session_id': demo_session.id,
                'redirect_url': url_for('demo.request_success', demo_id=demo_session.id)
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
    
    except Exception as e:
        current_app.logger.error(f"Error requesting demo: {str(e)}")
        return jsonify({'success': False, 'message': 'Error requesting demo session'}), 500

@demo_bp.route('/request-success/<int:demo_id>')
@login_required
def request_success(demo_id):
    """Demo request success page"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get demo session
        demo_session = DemoSession.query.filter_by(id=demo_id, student_id=current_user.id).first()
        if not demo_session:
            flash('Demo session not found.', 'error')
            return redirect(url_for('demo.book_demo'))
        
        return render_template('demo/request_success.html', demo_session=demo_session)
    
    except Exception as e:
        current_app.logger.error(f"Error loading request success page: {str(e)}")
        flash('Error loading page. Please try again.', 'danger')
        return redirect(url_for('demo.book_demo'))

@demo_bp.route('/manage')
@login_required
def manage_demos():
    """Manage demo sessions page"""
    if not current_user.is_learner():
        flash('Access denied. This page is for students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get filter parameters
        status_filter = request.args.get('status', '')
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Get demo sessions
        demo_service = DemoBookingService()
        demo_sessions = demo_service.get_student_demo_sessions(current_user.id, status_filter)
        
        # Apply pagination (manual since we're getting all and filtering)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_sessions = demo_sessions[start:end]
        
        # Create pagination object
        class Pagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
            
            def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
                last = 0
                for num in range(1, self.pages + 1):
                    if num <= left_edge or (num > self.page - left_current - 1 and num < self.page + right_current) or num > self.pages - right_edge:
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
        
        pagination = Pagination(paginated_sessions, page, per_page, len(demo_sessions))
        
        return render_template('demo/manage_demos.html',
                            pagination=pagination,
                            demo_sessions=paginated_sessions,
                            status_filter=status_filter)
    
    except Exception as e:
        current_app.logger.error(f"Error managing demos: {str(e)}")
        flash('Error loading demo sessions. Please try again.', 'danger')
        return redirect(url_for('student.dashboard'))

@demo_bp.route('/view/<int:demo_id>')
@login_required
def view_demo(demo_id):
    """View demo session details"""
    try:
        # Get demo session
        demo_session = DemoSession.query.filter_by(id=demo_id).first()
        if not demo_session:
            flash('Demo session not found.', 'error')
            return redirect(url_for('demo.manage_demos'))
        
        # Check permissions
        if current_user.id not in [demo_session.student_id, demo_session.tutor_id]:
            flash('Access denied.', 'danger')
            return redirect(url_for('demo.manage_demos'))
        
        # Get related data
        demo_service = DemoBookingService()
        
        # Get feedback if completed
        feedback = None
        if demo_session.status == DemoSessionStatus.COMPLETED:
            feedback = DemoFeedback.query.filter_by(
                demo_session_id=demo_id, provided_by=current_user.id
            ).first()
        
        # Get template if used
        template = None
        if demo_session.session_title:
            template = DemoTemplate.query.filter_by(
                tutor_id=demo_session.tutor_id,
                session_title=demo_session.session_title
            ).first()
        
        return render_template('demo/view_demo.html',
                            demo_session=demo_session,
                            feedback=feedback,
                            template=template)
    
    except Exception as e:
        current_app.logger.error(f"Error viewing demo: {str(e)}")
        flash('Error loading demo session. Please try again.', 'danger')
        return redirect(url_for('demo.manage_demos'))

@demo_bp.route('/confirm/<int:demo_id>', methods=['POST'])
@login_required
def confirm_demo(demo_id):
    """Confirm a demo session"""
    try:
        demo_service = DemoBookingService()
        success, message = demo_service.confirm_demo_session(demo_id, current_user.id)
        
        if success:
            flash('Demo session confirmed successfully!', 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('demo.view_demo', demo_id=demo_id))
    
    except Exception as e:
        current_app.logger.error(f"Error confirming demo: {str(e)}")
        flash('Error confirming demo session. Please try again.', 'danger')
        return redirect(url_for('demo.view_demo', demo_id=demo_id))

@demo_bp.route('/cancel/<int:demo_id>', methods=['POST'])
@login_required
def cancel_demo(demo_id):
    """Cancel a demo session"""
    try:
        # Get demo session
        demo_session = DemoSession.query.filter_by(id=demo_id).first()
        if not demo_session:
            return jsonify({'success': False, 'message': 'Demo session not found'}), 404
        
        # Check permissions
        if current_user.id not in [demo_session.student_id, demo_session.tutor_id]:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Get cancellation details
        cancellation_reason = request.form.get('cancellation_reason', '')
        initiated_by = 'student' if current_user.id == demo_session.student_id else 'tutor'
        
        # Cancel demo
        demo_service = DemoBookingService()
        success, message = demo_service.cancel_demo_session(
            demo_id, current_user.id, cancellation_reason, initiated_by
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
    
    except Exception as e:
        current_app.logger.error(f"Error cancelling demo: {str(e)}")
        return jsonify({'success': False, 'message': 'Error cancelling demo session'}), 500

@demo_bp.route('/reschedule/<int:demo_id>', methods=['POST'])
@login_required
def reschedule_demo(demo_id):
    """Reschedule a demo session"""
    try:
        # Get demo session
        demo_session = DemoSession.query.filter_by(id=demo_id).first()
        if not demo_session:
            return jsonify({'success': False, 'message': 'Demo session not found'}), 404
        
        # Check permissions
        if current_user.id not in [demo_session.student_id, demo_session.tutor_id]:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Get reschedule details
        new_datetime = datetime.fromisoformat(request.form.get('new_datetime'))
        reason = request.form.get('reason', '')
        
        # Reschedule demo
        demo_service = DemoBookingService()
        success, message = demo_service.reschedule_demo_session(
            demo_id, current_user.id, new_datetime, reason
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
    
    except Exception as e:
        current_app.logger.error(f"Error rescheduling demo: {str(e)}")
        return jsonify({'success': False, 'message': 'Error rescheduling demo session'}), 500

@demo_bp.route('/complete/<int:demo_id>', methods=['POST'])
@login_required
def complete_demo(demo_id):
    """Mark demo session as completed"""
    try:
        # Get demo session
        demo_session = DemoSession.query.filter_by(id=demo_id).first()
        if not demo_session:
            return jsonify({'success': False, 'message': 'Demo session not found'}), 404
        
        # Check permissions
        if current_user.id not in [demo_session.student_id, demo_session.tutor_id]:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Get completion data
        completion_data = {
            'tutor_feedback' if current_user.id == demo_session.tutor_id else 'student_feedback': request.form.get('feedback', ''),
            'conversion_potential': request.form.get('conversion_potential', 'unknown'),
            'follow_up_actions': request.form.getlist('follow_up_actions')
        }
        
        # Complete demo
        demo_service = DemoBookingService()
        success, message = demo_service.complete_demo_session(demo_id, current_user.id, completion_data)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
    
    except Exception as e:
        current_app.logger.error(f"Error completing demo: {str(e)}")
        return jsonify({'success': False, 'message': 'Error completing demo session'}), 500

@demo_bp.route('/feedback/<int:demo_id>', methods=['GET', 'POST'])
@login_required
def submit_feedback(demo_id):
    """Submit feedback for demo session"""
    try:
        # Get demo session
        demo_session = DemoSession.query.filter_by(id=demo_id).first()
        if not demo_session:
            flash('Demo session not found.', 'error')
            return redirect(url_for('demo.manage_demos'))
        
        # Check permissions
        if current_user.id not in [demo_session.student_id, demo_session.tutor_id]:
            flash('Access denied.', 'danger')
            return redirect(url_for('demo.manage_demos'))
        
        # Check if demo is completed
        if demo_session.status != DemoSessionStatus.COMPLETED:
            flash('Feedback can only be submitted for completed demos.', 'error')
            return redirect(url_for('demo.view_demo', demo_id=demo_id))
        
        # Check if feedback already exists
        existing_feedback = DemoFeedback.query.filter_by(
            demo_session_id=demo_id, provided_by=current_user.id
        ).first()
        if existing_feedback:
            flash('You have already submitted feedback for this demo.', 'info')
            return redirect(url_for('demo.view_demo', demo_id=demo_id))
        
        if request.method == 'POST':
            # Get feedback data
            feedback_data = {
                'overall_rating': int(request.form.get('overall_rating')),
                'would_recommend': request.form.get('would_recommend') == 'true',
                'would_book_paid': request.form.get('would_book_paid') == 'true',
                'content_quality': int(request.form.get('content_quality')) if request.form.get('content_quality') else None,
                'tutor_expertise': int(request.form.get('tutor_expertise')) if request.form.get('tutor_expertise') else None,
                'session_pace': int(request.form.get('session_pace')) if request.form.get('session_pace') else None,
                'interaction_level': int(request.form.get('interaction_level')) if request.form.get('interaction_level') else None,
                'technical_quality': int(request.form.get('technical_quality')) if request.form.get('technical_quality') else None,
                'what_went_well': request.form.get('what_went_well', ''),
                'what_could_improve': request.form.get('what_could_improve', ''),
                'most_valuable_aspect': request.form.get('most_valuable_aspect', ''),
                'suggestions_for_future': request.form.get('suggestions_for_future', ''),
                'main_decision_factors': request.form.getlist('main_decision_factors'),
                'concerns_raised': request.form.getlist('concerns_raised'),
                'price_sensitivity': request.form.get('price_sensitivity', ''),
                'preferred_follow_up_method': request.form.get('preferred_follow_up_method', ''),
                'best_contact_time': request.form.get('best_contact_time', ''),
                'additional_questions': request.form.get('additional_questions', ''),
                'is_anonymous': request.form.get('is_anonymous') == 'true'
            }
            
            # Submit feedback
            demo_service = DemoBookingService()
            success, message = demo_service.submit_demo_feedback(demo_id, current_user.id, feedback_data)
            
            if success:
                flash('Feedback submitted successfully! Thank you for your input.', 'success')
                return redirect(url_for('demo.view_demo', demo_id=demo_id))
            else:
                flash(message, 'error')
        
        return render_template('demo/submit_feedback.html', demo_session=demo_session)
    
    except Exception as e:
        current_app.logger.error(f"Error submitting feedback: {str(e)}")
        flash('Error submitting feedback. Please try again.', 'danger')
        return redirect(url_for('demo.view_demo', demo_id=demo_id))

@demo_bp.route('/availability/<int:tutor_id>')
@login_required
def tutor_availability(tutor_id):
    """Get tutor availability for demo booking (AJAX endpoint)"""
    try:
        # Get date range from request
        start_date = datetime.fromisoformat(request.args.get('start_date'))
        end_date = datetime.fromisoformat(request.args.get('end_date'))
        
        # Get availability
        demo_service = DemoBookingService()
        availability = demo_service.get_tutor_demo_availability(tutor_id, start_date, end_date)
        
        return jsonify({'success': True, 'availability': availability})
    
    except Exception as e:
        current_app.logger.error(f"Error getting tutor availability: {str(e)}")
        return jsonify({'success': False, 'message': 'Error getting availability'}), 500

@demo_bp.route('/templates/<int:tutor_id>')
@login_required
def demo_templates(tutor_id):
    """Get demo templates for tutor (AJAX endpoint)"""
    try:
        subject_id = request.args.get('subject_id', type=int)
        
        # Get templates
        demo_service = DemoBookingService()
        templates = demo_service.get_demo_templates(tutor_id, subject_id)
        
        return jsonify({'success': True, 'templates': templates})
    
    except Exception as e:
        current_app.logger.error(f"Error getting demo templates: {str(e)}")
        return jsonify({'success': False, 'message': 'Error getting templates'}), 500

# Tutor-specific routes

@demo_bp.route('/tutor/manage')
@login_required
def tutor_manage_demos():
    """Tutor demo management page"""
    if not current_user.is_tutor():
        flash('Access denied. This page is for tutors only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get filter parameters
        status_filter = request.args.get('status', '')
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Get demo sessions
        demo_service = DemoBookingService()
        demo_sessions = demo_service.get_tutor_demo_sessions(current_user.id, status_filter)
        
        # Apply pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_sessions = demo_sessions[start:end]
        
        # Create pagination object
        class Pagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
        
        pagination = Pagination(paginated_sessions, page, per_page, len(demo_sessions))
        
        return render_template('demo/tutor_manage_demos.html',
                            pagination=pagination,
                            demo_sessions=paginated_sessions,
                            status_filter=status_filter)
    
    except Exception as e:
        current_app.logger.error(f"Error managing tutor demos: {str(e)}")
        flash('Error loading demo sessions. Please try again.', 'danger')
        return redirect(url_for('tutor.dashboard'))

@demo_bp.route('/tutor/accept/<int:demo_id>', methods=['POST'])
@login_required
def accept_demo(demo_id):
    """Accept a demo session request (tutor only)"""
    if not current_user.is_tutor():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        # Get demo session
        demo_session = DemoSession.query.filter_by(id=demo_id, tutor_id=current_user.id).first()
        if not demo_session:
            return jsonify({'success': False, 'message': 'Demo session not found'}), 404
        
        # Get acceptance details
        scheduled_datetime = datetime.fromisoformat(request.form.get('scheduled_datetime'))
        meeting_data = {
            'meeting_link': request.form.get('meeting_link', ''),
            'meeting_password': request.form.get('meeting_password', ''),
            'physical_address': request.form.get('physical_address', '')
        }
        
        # Accept demo
        demo_service = DemoBookingService()
        success, message = demo_service.accept_demo_session(demo_id, current_user.id, scheduled_datetime, meeting_data)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
    
    except Exception as e:
        current_app.logger.error(f"Error accepting demo: {str(e)}")
        return jsonify({'success': False, 'message': 'Error accepting demo session'}), 500

@demo_bp.route('/tutor/availability')
@login_required
def tutor_availability_settings():
    """Tutor availability settings page"""
    if not current_user.is_tutor():
        flash('Access denied. This page is for tutors only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get current availability
        availability = DemoAvailability.query.filter_by(
            tutor_id=current_user.id, is_active=True
        ).all()
        
        # Get subjects tutor teaches
        tutor_profile = TutorProfile.query.filter_by(user_id=current_user.id).first()
        subjects = [tutor_subject.subject for tutor_subject in tutor_profile.subjects if tutor_subject.is_active] if tutor_profile else []
        
        return render_template('demo/tutor_availability.html',
                            availability=availability,
                            subjects=subjects)
    
    except Exception as e:
        current_app.logger.error(f"Error loading availability settings: {str(e)}")
        flash('Error loading availability settings. Please try again.', 'danger')
        return redirect(url_for('tutor.dashboard'))

@demo_bp.route('/tutor/analytics')
@login_required
def tutor_analytics():
    """Tutor demo analytics page"""
    if not current_user.is_tutor():
        flash('Access denied. This page is for tutors only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get analytics for different time periods
        today = datetime.now(timezone.utc).date()
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        
        # Daily analytics for last 7 days
        daily_analytics = DemoAnalytics.query.filter(
            and_(
                DemoAnalytics.tutor_id == current_user.id,
                DemoAnalytics.analytics_date >= last_week,
                DemoAnalytics.period_type == 'daily'
            )
        ).order_by(desc(DemoAnalytics.analytics_date)).all()
        
        # Monthly analytics for last 6 months
        monthly_analytics = DemoAnalytics.query.filter(
            and_(
                DemoAnalytics.tutor_id == current_user.id,
                DemoAnalytics.analytics_date >= last_month,
                DemoAnalytics.period_type == 'monthly'
            )
        ).order_by(desc(DemoAnalytics.analytics_date)).all()
        
        # Recent feedback
        recent_feedback = DemoFeedback.query.join(DemoSession).filter(
            and_(
                DemoSession.tutor_id == current_user.id,
                DemoSession.status == DemoSessionStatus.COMPLETED,
                DemoFeedback.provider_role == 'student'
            )
        ).order_by(desc(DemoFeedback.submitted_at)).limit(10).all()
        
        return render_template('demo/tutor_analytics.html',
                            daily_analytics=daily_analytics,
                            monthly_analytics=monthly_analytics,
                            recent_feedback=recent_feedback)
    
    except Exception as e:
        current_app.logger.error(f"Error loading demo analytics: {str(e)}")
        flash('Error loading analytics. Please try again.', 'danger')
        return redirect(url_for('tutor.dashboard'))