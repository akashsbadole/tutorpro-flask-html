from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.demo import bp
from app.demo.forms import (DemoRequestForm, DemoClassForm, DemoFeedbackForm, DemoMaterialForm,
                          DemoFollowUpForm, DemoTemplateForm, DemoSearchForm, DemoRescheduleForm,
                          DemoConversionForm)
from app.models.demo import (DemoClass, DemoFeedback, DemoMaterial, DemoFollowUp,
                           DemoTemplate, DemoAnalytics, DemoRequest)
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.course import Course
from app.utils.decorators import tutor_required, admin_required
from app import db
from sqlalchemy import func, desc, or_
from datetime import datetime, timedelta
import json


@bp.route('/')
@login_required
def index():
    """Demo dashboard"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
    query = DemoClass.query
    
    # Filter by user role
    if current_user.is_tutor():
        tutor_profile = current_user.tutor_profile
        if tutor_profile:
            query = query.filter_by(tutor_id=tutor_profile.id)
    elif current_user.is_student():
        query = query.filter_by(student_id=current_user.id)
    elif current_user.is_admin():
        # Admins can see all demos
        pass
    else:
        query = query.filter_by(student_id=current_user.id)
    
    # Filter by status
    if status:
        query = query.filter_by(status=status)
    
    demos = query.order_by(DemoClass.scheduled_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('demo/index.html', demos=demos, status=status)


@bp.route('/request', methods=['GET', 'POST'])
@login_required
def request_demo():
    """Request a demo class"""
    form = DemoRequestForm()
    
    # Populate tutor choices
    tutors = TutorProfile.query.filter_by(is_verified=True).all()
    form.tutor_id.choices = [(t.id, t.user.user_profile.full_name if t.user.user_profile else t.user.email) for t in tutors]
    
    # Populate course choices
    courses = Course.query.all()
    form.course_id.choices = [(c.id, c.title) for c in courses]
    
    if form.validate_on_submit():
        demo_request = DemoRequest(
            student_id=current_user.id,
            tutor_id=form.tutor_id.data,
            course_id=form.course_id.data,
            preferred_date=form.preferred_date.data,
            preferred_time=form.preferred_time.data,
            alternative_dates=form.alternative_dates.data,
            duration_minutes=form.duration_minutes.data,
            timezone=form.timezone.data,
            learning_goals=form.learning_goals.data,
            current_level=form.current_level.data,
            specific_topics=form.specific_topics.data,
            questions_for_tutor=form.questions_for_tutor.data
        )
        
        db.session.add(demo_request)
        db.session.commit()
        
        flash('Demo request submitted successfully!', 'success')
        return redirect(url_for('demo.requests'))
    
    return render_template('demo/request.html', form=form)


@bp.route('/requests')
@login_required
def requests():
    """View demo requests"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
    query = DemoRequest.query
    
    # Filter by user role
    if current_user.is_tutor():
        tutor_profile = current_user.tutor_profile
        if tutor_profile:
            query = query.filter_by(tutor_id=tutor_profile.id)
    elif current_user.is_student():
        query = query.filter_by(student_id=current_user.id)
    elif current_user.is_admin():
        # Admins can see all requests
        pass
    
    # Filter by status
    if status:
        query = query.filter_by(status=status)
    
    demo_requests = query.order_by(DemoRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('demo/requests.html', requests=demo_requests, status=status)


@bp.route('/requests/<int:id>/review', methods=['GET', 'POST'])
@login_required
def review_request(id):
    """Review demo request"""
    demo_request = DemoRequest.query.get_or_404(id)
    
    # Check permissions
    if not _can_review_request(demo_request):
        flash('You do not have permission to review this request', 'danger')
        return redirect(url_for('demo.requests'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'accept':
            # Create demo class from request
            demo_class = DemoClass(
                title=f"Demo Class - {demo_request.course.title if demo_request.course else 'General'}",
                description=f"Demo class requested by {demo_request.student.email}",
                student_id=demo_request.student_id,
                tutor_id=demo_request.tutor_id,
                course_id=demo_request.course_id,
                scheduled_time=datetime.combine(demo_request.preferred_date, demo_request.preferred_time),
                duration_minutes=demo_request.duration_minutes,
                timezone=demo_request.timezone,
                status='Confirmed'
            )
            
            db.session.add(demo_class)
            
            # Update request status
            demo_request.status = 'Accepted'
            demo_request.reviewed_by = current_user.id
            demo_request.reviewed_at = datetime.utcnow()
            
            db.session.commit()
            
            # Create analytics record
            analytics = DemoAnalytics(demo_class_id=demo_class.id)
            db.session.add(analytics)
            db.session.commit()
            
            flash('Demo request accepted and scheduled!', 'success')
            return redirect(url_for('demo.details', id=demo_class.id))
            
        elif action == 'reject':
            demo_request.status = 'Rejected'
            demo_request.reviewed_by = current_user.id
            demo_request.reviewed_at = datetime.utcnow()
            demo_request.review_notes = request.form.get('review_notes', '')
            
            db.session.commit()
            
            flash('Demo request rejected', 'info')
            return redirect(url_for('demo.requests'))
    
    return render_template('demo/review_request.html', request=demo_request)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new demo class"""
    form = DemoClassForm()
    
    # Populate choices
    if current_user.is_tutor():
        tutor_profile = current_user.tutor_profile
        if tutor_profile:
            form.tutor_id.data = tutor_profile.id
    
    students = User.query.filter_by(role='Learner').all()
    form.student_id.choices = [(s.id, s.user_profile.full_name if s.user_profile else s.email) for s in students]
    
    tutors = TutorProfile.query.filter_by(is_verified=True).all()
    form.tutor_id.choices = [(t.id, t.user.user_profile.full_name if t.user.user_profile else t.user.email) for t in tutors]
    
    courses = Course.query.all()
    form.course_id.choices = [(0, 'Select Course')] + [(c.id, c.title) for c in courses]
    
    if form.validate_on_submit():
        demo_class = DemoClass(
            title=form.title.data,
            description=form.description.data,
            student_id=form.student_id.data,
            tutor_id=form.tutor_id.data,
            course_id=form.course_id.data if form.course_id.data != 0 else None,
            scheduled_time=form.scheduled_time.data,
            duration_minutes=form.duration_minutes.data,
            timezone=form.timezone.data,
            meeting_platform=form.meeting_platform.data,
            meeting_url=form.meeting_url.data,
            meeting_password=form.meeting_password.data,
            max_participants=form.max_participants.data,
            is_group_demo=form.is_group_demo.data,
            preparation_materials=form.preparation_materials.data,
            status='Scheduled'
        )
        
        db.session.add(demo_class)
        db.session.commit()
        
        # Create analytics record
        analytics = DemoAnalytics(demo_class_id=demo_class.id)
        db.session.add(analytics)
        db.session.commit()
        
        flash('Demo class created successfully!', 'success')
        return redirect(url_for('demo.details', id=demo_class.id))
    
    return render_template('demo/create.html', form=form)


@bp.route('/<int:id>')
@login_required
def details(id):
    """View demo class details"""
    demo_class = DemoClass.query.get_or_404(id)
    
    # Check permissions
    if not _can_view_demo(demo_class):
        flash('You do not have permission to view this demo class', 'danger')
        return redirect(url_for('demo.index'))
    
    # Get related data
    feedback = DemoFeedback.query.filter_by(demo_class_id=id).first()
    materials = DemoMaterial.query.filter_by(demo_class_id=id).order_by(DemoMaterial.order).all()
    follow_ups = DemoFollowUp.query.filter_by(demo_class_id=id).order_by(DemoFollowUp.scheduled_for.desc()).all()
    analytics = DemoAnalytics.query.filter_by(demo_class_id=id).first()
    
    return render_template('demo/details.html', 
                        demo_class=demo_class,
                        feedback=feedback,
                        materials=materials,
                        follow_ups=follow_ups,
                        analytics=analytics)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit demo class"""
    demo_class = DemoClass.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_demo(demo_class):
        flash('You do not have permission to edit this demo class', 'danger')
        return redirect(url_for('demo.details', id=id))
    
    form = DemoClassForm(obj=demo_class)
    
    # Populate choices
    students = User.query.filter_by(role='Learner').all()
    form.student_id.choices = [(s.id, s.user_profile.full_name if s.user_profile else s.email) for s in students]
    
    tutors = TutorProfile.query.filter_by(is_verified=True).all()
    form.tutor_id.choices = [(t.id, t.user.user_profile.full_name if t.user.user_profile else t.user.email) for t in tutors]
    
    courses = Course.query.all()
    form.course_id.choices = [(0, 'Select Course')] + [(c.id, c.title) for c in courses]
    
    if form.validate_on_submit():
        # Update demo class
        demo_class.title = form.title.data
        demo_class.description = form.description.data
        demo_class.student_id = form.student_id.data
        demo_class.tutor_id = form.tutor_id.data
        demo_class.course_id = form.course_id.data if form.course_id.data != 0 else None
        demo_class.scheduled_time = form.scheduled_time.data
        demo_class.duration_minutes = form.duration_minutes.data
        demo_class.timezone = form.timezone.data
        demo_class.meeting_platform = form.meeting_platform.data
        demo_class.meeting_url = form.meeting_url.data
        demo_class.meeting_password = form.meeting_password.data
        demo_class.max_participants = form.max_participants.data
        demo_class.is_group_demo = form.is_group_demo.data
        demo_class.preparation_materials = form.preparation_materials.data
        
        db.session.commit()
        
        flash('Demo class updated successfully!', 'success')
        return redirect(url_for('demo.details', id=id))
    
    return render_template('demo/edit.html', form=form, demo_class=demo_class)


@bp.route('/<int:id>/start', methods=['POST'])
@login_required
def start(id):
    """Start demo class"""
    demo_class = DemoClass.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_demo(demo_class):
        flash('You do not have permission to start this demo class', 'danger')
        return redirect(url_for('demo.details', id=id))
    
    demo_class.start_demo()
    
    flash('Demo class started!', 'success')
    return redirect(url_for('demo.details', id=id))


@bp.route('/<int:id>/complete', methods=['POST'])
@login_required
def complete(id):
    """Complete demo class"""
    demo_class = DemoClass.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_demo(demo_class):
        flash('You do not have permission to complete this demo class', 'danger')
        return redirect(url_for('demo.details', id=id))
    
    student_attended = request.form.get('student_attended') == 'true'
    demo_class.complete_demo(student_attended)
    
    flash('Demo class completed!', 'success')
    return redirect(url_for('demo.details', id=id))


@bp.route('/<int:id>/feedback', methods=['GET', 'POST'])
@login_required
def feedback(id):
    """Submit demo feedback"""
    demo_class = DemoClass.query.get_or_404(id)
    
    # Check permissions
    if not _can_provide_feedback(demo_class):
        flash('You cannot provide feedback for this demo class', 'danger')
        return redirect(url_for('demo.details', id=id))
    
    feedback = DemoFeedback.query.filter_by(demo_class_id=id).first()
    form = DemoFeedbackForm(obj=feedback)
    
    if form.validate_on_submit():
        if not feedback:
            feedback = DemoFeedback(demo_class_id=id)
            db.session.add(feedback)
        
        # Update feedback data
        feedback.student_rating = form.student_rating.data
        feedback.teaching_quality = form.teaching_quality.data
        feedback.communication = form.communication.data
        feedback.preparation = form.preparation.data
        feedback.content_quality = form.content_quality.data
        feedback.student_comments = form.student_comments.data
        feedback.would_recommend = form.would_recommend.data
        
        if current_user.is_tutor():
            feedback.tutor_rating = form.tutor_rating.data
            feedback.student_engagement = form.student_engagement.data
            feedback.student_participation = form.student_participation.data
            feedback.learning_potential = form.learning_potential.data
            feedback.tutor_comments = form.tutor_comments.data
            feedback.recommended_next_steps = form.recommended_next_steps.data
            feedback.suggested_course_level = form.suggested_course_level.data
            feedback.suggested_focus_areas = form.suggested_focus_areas.data
        
        db.session.commit()
        
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('demo.details', id=id))
    
    return render_template('demo/feedback.html', form=form, demo_class=demo_class)


@bp.route('/<int:id>/materials/add', methods=['GET', 'POST'])
@login_required
def add_material(id):
    """Add material to demo class"""
    demo_class = DemoClass.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_demo(demo_class):
        flash('You do not have permission to add materials', 'danger')
        return redirect(url_for('demo.details', id=id))
    
    form = DemoMaterialForm()
    
    if form.validate_on_submit():
        material = DemoMaterial(
            demo_class_id=id,
            title=form.title.data,
            description=form.description.data,
            material_type=form.material_type.data,
            file_url=form.file_url.data,
            file_name=form.file_name.data,
            is_required=form.is_required.data,
            order=form.order.data,
            student_accessible=form.student_accessible.data,
            accessible_before_demo=form.accessible_before_demo.data,
            accessible_after_demo=form.accessible_after_demo.data
        )
        
        db.session.add(material)
        db.session.commit()
        
        flash('Material added successfully!', 'success')
        return redirect(url_for('demo.details', id=id))
    
    return render_template('demo/add_material.html', form=form, demo_class=demo_class)


@bp.route('/<int:id>/followups/add', methods=['GET', 'POST'])
@login_required
def add_follow_up(id):
    """Add follow-up to demo class"""
    demo_class = DemoClass.query.get_or_404(id)
    
    # Check permissions
    if not _can_view_demo(demo_class):
        flash('You do not have permission to add follow-ups', 'danger')
        return redirect(url_for('demo.details', id=id))
    
    form = DemoFollowUpForm()
    
    # Populate assignee choices
    users = User.query.filter(User.role.in_(['Tutor', 'Admin'])).all()
    form.assigned_to.choices = [(0, 'Unassigned')] + [(u.id, u.user_profile.full_name if u.user_profile else u.email) for u in users]
    
    if form.validate_on_submit():
        follow_up = DemoFollowUp(
            demo_class_id=id,
            follow_up_type=form.follow_up_type.data,
            title=form.title.data,
            description=form.description.data,
            scheduled_for=form.scheduled_for.data,
            assigned_to=form.assigned_to.data if form.assigned_to.data != 0 else None
        )
        
        db.session.add(follow_up)
        db.session.commit()
        
        flash('Follow-up added successfully!', 'success')
        return redirect(url_for('demo.details', id=id))
    
    return render_template('demo/add_follow_up.html', form=form, demo_class=demo_class)


@bp.route('/<int:id>/convert', methods=['GET', 'POST'])
@login_required
def convert(id):
    """Convert demo to enrollment"""
    demo_class = DemoClass.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_demo(demo_class):
        flash('You do not have permission to convert this demo', 'danger')
        return redirect(url_for('demo.details', id=id))
    
    form = DemoConversionForm(obj=demo_class)
    
    if form.validate_on_submit():
        demo_class.conversion_status = form.conversion_status.data
        demo_class.conversion_notes = form.conversion_notes.data
        demo_class.follow_up_required = form.follow_up_required.data
        demo_class.follow_up_date = form.follow_up_date.data
        
        db.session.commit()
        
        flash('Conversion status updated!', 'success')
        return redirect(url_for('demo.details', id=id))
    
    return render_template('demo/convert.html', form=form, demo_class=demo_class)


@bp.route('/templates')
@login_required
def templates():
    """Demo templates"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = DemoTemplate.query
    
    # Show user's templates and public templates
    query = query.filter(
        or_(DemoTemplate.created_by == current_user.id,
             DemoTemplate.is_public == True)
    )
    
    templates = query.order_by(DemoTemplate.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('demo/templates.html', templates=templates)


@bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
def create_template():
    """Create demo template"""
    form = DemoTemplateForm()
    
    if form.validate_on_submit():
        template = DemoTemplate(
            name=form.name.data,
            description=form.description.data,
            default_duration=form.default_duration.data,
            default_platform=form.default_platform.data,
            agenda=form.agenda.data,
            objectives=form.objectives.data,
            materials_required=form.materials_required.data,
            welcome_message=form.welcome_message.data,
            introduction_script=form.introduction_script.data,
            closing_script=form.closing_script.data,
            created_by=current_user.id,
            is_public=form.is_public.data
        )
        
        db.session.add(template)
        db.session.commit()
        
        flash('Template created successfully!', 'success')
        return redirect(url_for('demo.templates'))
    
    return render_template('demo/create_template.html', form=form)


@bp.route('/calendar')
@login_required
def calendar():
    """Demo calendar view"""
    # Get demos for current month
    start_date = request.args.get('start', datetime.utcnow().replace(day=1).strftime('%Y-%m-%d'))
    end_date = request.args.get('end', (datetime.utcnow().replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d'))
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    query = DemoClass.query.filter(
        DemoClass.scheduled_time >= start_date,
        DemoClass.scheduled_time <= end_date
    )
    
    # Filter by user role
    if current_user.is_tutor():
        tutor_profile = current_user.tutor_profile
        if tutor_profile:
            query = query.filter_by(tutor_id=tutor_profile.id)
    elif current_user.is_student():
        query = query.filter_by(student_id=current_user.id)
    
    demos = query.order_by(DemoClass.scheduled_time.asc()).all()
    
    return render_template('demo/calendar.html', demos=demos)


@bp.route('/search')
@login_required
def search():
    """Search demo classes"""
    form = DemoSearchForm()
    demos = []
    
    if request.args.get('query'):
        form = DemoSearchForm(request.args)
        
        query = DemoClass.query
        
        # Filter by user role
        if current_user.is_tutor():
            tutor_profile = current_user.tutor_profile
            if tutor_profile:
                query = query.filter_by(tutor_id=tutor_profile.id)
        elif current_user.is_student():
            query = query.filter_by(student_id=current_user.id)
        
        # Apply filters
        if form.query.data:
            query = query.filter(
                or_(DemoClass.title.contains(form.query.data),
                     DemoClass.description.contains(form.query.data))
            )
        
        if form.status.data:
            query = query.filter_by(status=form.status.data)
        
        if form.conversion_status.data:
            query = query.filter_by(conversion_status=form.conversion_status.data)
        
        if form.date_from.data:
            query = query.filter(DemoClass.scheduled_time >= form.date_from.data)
        
        if form.date_to.data:
            query = query.filter(DemoClass.scheduled_time <= form.date_to.data)
        
        demos = query.order_by(DemoClass.scheduled_time.desc()).limit(50).all()
    
    return render_template('demo/search.html', form=form, demos=demos)


@bp.route('/<int:id>/reschedule', methods=['GET', 'POST'])
@login_required
def reschedule(id):
    """Reschedule demo class"""
    demo_class = DemoClass.query.get_or_404(id)
    
    # Check permissions
    if not _can_edit_demo(demo_class):
        flash('You do not have permission to reschedule this demo class', 'danger')
        return redirect(url_for('demo.details', id=id))
    
    form = DemoRescheduleForm()
    
    if form.validate_on_submit():
        old_time = demo_class.scheduled_time
        old_duration = demo_class.duration_minutes
        
        demo_class.scheduled_time = form.new_scheduled_time.data
        demo_class.duration_minutes = form.new_duration_minutes.data
        
        db.session.commit()
        
        # Notify student if requested
        if form.notify_student.data:
            _notify_reschedule(demo_class, old_time, old_duration, form.reason.data)
        
        flash('Demo class rescheduled successfully!', 'success')
        return redirect(url_for('demo.details', id=id))
    
    return render_template('demo/reschedule.html', form=form, demo_class=demo_class)


# Helper functions
def _can_view_demo(demo_class):
    """Check if current user can view demo class"""
    if current_user.is_admin():
        return True
    
    if demo_class.student_id == current_user.id:
        return True
    
    if current_user.is_tutor():
        tutor_profile = current_user.tutor_profile
        if tutor_profile and demo_class.tutor_id == tutor_profile.id:
            return True
    
    return False


def _can_edit_demo(demo_class):
    """Check if current user can edit demo class"""
    if current_user.is_admin():
        return True
    
    if current_user.is_tutor():
        tutor_profile = current_user.tutor_profile
        if tutor_profile and demo_class.tutor_id == tutor_profile.id:
            return True
    
    return False


def _can_review_request(demo_request):
    """Check if current user can review demo request"""
    if current_user.is_admin():
        return True
    
    if current_user.is_tutor():
        tutor_profile = current_user.tutor_profile
        if tutor_profile and demo_request.tutor_id == tutor_profile.id:
            return True
    
    return False


def _can_provide_feedback(demo_class):
    """Check if current user can provide feedback"""
    if demo_class.status != 'Completed':
        return False
    
    if demo_class.student_id == current_user.id:
        return True
    
    if current_user.is_tutor():
        tutor_profile = current_user.tutor_profile
        if tutor_profile and demo_class.tutor_id == tutor_profile.id:
            return True
    
    return False


def _notify_reschedule(demo_class, old_time, old_duration, reason):
    """Notify about demo reschedule"""
    # Send email notification (implementation depends on email service)
    pass