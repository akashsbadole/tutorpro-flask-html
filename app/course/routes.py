from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
import os
import json
from datetime import datetime
from app import db
from app.utils.file_utils import save_uploaded_file, delete_file, secure_course_material_path, secure_assignment_path
from app.course import bp
from app.course.forms import (
    CourseForm, SyllabusForm, SyllabusTopicForm, CourseMaterialForm, 
    AssignmentForm, AssignmentSubmissionForm, AssignmentGradingForm,
    RubricCriteriaForm, RubricScoreForm, DiscussionBoardForm, DiscussionPostForm,
    QuizForm, QuizQuestionForm, QuizOptionForm, QuizAttemptForm,
    AchievementForm, CourseEnrollmentForm, ProgressUpdateForm, SearchForm
)
from app.models.course import (
    Course, CourseSyllabus, SyllabusTopic, CourseMaterial, CourseEnrollment,
    Assignment, AssignmentSubmission, AssignmentRubric, RubricCriteria, RubricScore,
    StudentProgress, DiscussionBoard, DiscussionPost, Quiz, QuizQuestion, QuizOption,
    QuizAttempt, QuizAnswer, Achievement, EarnedAchievement, Subject
)
from app.models.user import User
from app.utils.decorators import tutor_required, admin_required, role_required


# Course Management Routes
@bp.route('/courses')
def courses():
    """Browse all courses"""
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    
    # Start with base query
    query = Course.query
    
    # Apply filters if form is submitted
    if form.validate():
        if form.query.data:
            query = query.filter(Course.title.contains(form.query.data))
        if form.subject.data:
            query = query.filter(Course.subject_id == form.subject.data)
        if form.level.data:
            query = query.filter(Course.level == form.level.data)
        if form.min_price.data:
            query = query.filter(Course.price >= form.min_price.data)
        if form.max_price.data:
            query = query.filter(Course.price <= form.max_price.data)
    
    courses = query.order_by(Course.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)
    
    return render_template('course/courses.html', courses=courses, form=form, title='All Courses')


@bp.route('/courses/<int:course_id>')
def course_detail(course_id):
    """View course details"""
    course = Course.query.get_or_404(course_id)
    is_enrolled = False
    enrollment = None
    
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None
    
    return render_template('course/course_detail.html', course=course, 
                          is_enrolled=is_enrolled, enrollment=enrollment)


@bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
@tutor_required
def create_course():
    """Create a new course"""
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            title=form.title.data,
            description=form.description.data,
            subject_id=form.subject_id.data,
            level=form.level.data,
            price=float(form.price.data),
            duration_hours=form.duration_hours.data,
            thumbnail_url=form.thumbnail_url.data
        )
        db.session.add(course)
        db.session.commit()
        flash('Course created successfully!', 'success')
        return redirect(url_for('course.course_detail', course_id=course.id))
    
    return render_template('course/create_course.html', form=form, title='Create Course')


@bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@tutor_required
def edit_course(course_id):
    """Edit an existing course"""
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    
    if form.validate_on_submit():
        course.title = form.title.data
        course.description = form.description.data
        course.subject_id = form.subject_id.data
        course.level = form.level.data
        course.price = float(form.price.data)
        course.duration_hours = form.duration_hours.data
        course.thumbnail_url = form.thumbnail_url.data
        course.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('course.course_detail', course_id=course.id))
    
    return render_template('course/edit_course.html', form=form, course=course, title='Edit Course')


@bp.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_course(course_id):
    """Enroll in a course"""
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing_enrollment = CourseEnrollment.query.filter_by(
        course_id=course_id, student_id=current_user.id).first()
    
    if existing_enrollment:
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('course.course_detail', course_id=course_id))
    
    # Create new enrollment
    enrollment = CourseEnrollment(
        course_id=course_id,
        student_id=current_user.id
    )
    db.session.add(enrollment)
    db.session.commit()
    
    flash('You have been enrolled in the course!', 'success')
    return redirect(url_for('course.course_detail', course_id=course_id))


# Syllabus Management Routes
@bp.route('/courses/<int:course_id>/syllabus')
@login_required
def course_syllabus(course_id):
    """View course syllabus"""
    course = Course.query.get_or_404(course_id)
    syllabus_items = CourseSyllabus.query.filter_by(course_id=course_id).order_by(CourseSyllabus.order_index).all()
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    enrollment = None
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to view the syllabus.', 'warning')
        return redirect(url_for('course.course_detail', course_id=course_id))
    
    return render_template('course/syllabus.html', course=course, syllabus_items=syllabus_items, 
                          enrollment=enrollment, title=f'{course.title} - Syllabus')


@bp.route('/courses/<int:course_id>/syllabus/create', methods=['GET', 'POST'])
@login_required
@tutor_required
def create_syllabus(course_id):
    """Create a new syllabus module"""
    course = Course.query.get_or_404(course_id)
    form = SyllabusForm()
    
    if form.validate_on_submit():
        # Process prerequisites
        prerequisites = None
        if form.prerequisites.data:
            try:
                prerequisites = json.dumps([int(x.strip()) for x in form.prerequisites.data.split(',') if x.strip()])
            except ValueError:
                prerequisites = None
        
        syllabus = CourseSyllabus(
            course_id=course_id,
            title=form.title.data,
            description=form.description.data,
            content=form.content.data,
            order_index=form.order_index.data,
            is_milestone=form.is_milestone.data,
            estimated_hours=form.estimated_hours.data,
            prerequisites=prerequisites
        )
        db.session.add(syllabus)
        db.session.commit()
        flash('Syllabus module created successfully!', 'success')
        return redirect(url_for('course.course_syllabus', course_id=course_id))
    
    return render_template('course/create_syllabus.html', form=form, course=course, title='Create Syllabus Module')


@bp.route('/syllabus/<int:syllabus_id>/edit', methods=['GET', 'POST'])
@login_required
@tutor_required
def edit_syllabus(syllabus_id):
    """Edit a syllabus module"""
    syllabus = CourseSyllabus.query.get_or_404(syllabus_id)
    form = SyllabusForm(obj=syllabus)
    
    # Convert prerequisites from JSON to comma-separated string
    if syllabus.prerequisites:
        try:
            prereq_list = json.loads(syllabus.prerequisites)
            form.prerequisites.data = ', '.join(map(str, prereq_list))
        except (ValueError, TypeError):
            form.prerequisites.data = ''
    
    if form.validate_on_submit():
        syllabus.title = form.title.data
        syllabus.description = form.description.data
        syllabus.content = form.content.data
        syllabus.order_index = form.order_index.data
        syllabus.is_milestone = form.is_milestone.data
        syllabus.estimated_hours = form.estimated_hours.data
        
        # Process prerequisites
        if form.prerequisites.data:
            try:
                syllabus.prerequisites = json.dumps([int(x.strip()) for x in form.prerequisites.data.split(',') if x.strip()])
            except ValueError:
                syllabus.prerequisites = None
        else:
            syllabus.prerequisites = None
        
        syllabus.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Syllabus module updated successfully!', 'success')
        return redirect(url_for('course.course_syllabus', course_id=syllabus.course_id))
    
    return render_template('course/edit_syllabus.html', form=form, syllabus=syllabus, title='Edit Syllabus Module')


# Topic Management Routes
@bp.route('/syllabus/<int:syllabus_id>/topics')
@login_required
def syllabus_topics(syllabus_id):
    """View topics in a syllabus module"""
    syllabus = CourseSyllabus.query.get_or_404(syllabus_id)
    topics = SyllabusTopic.query.filter_by(syllabus_id=syllabus_id).order_by(SyllabusTopic.order_index).all()
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=syllabus.course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to view topics.', 'warning')
        return redirect(url_for('course.course_detail', course_id=syllabus.course_id))
    
    return render_template('course/topics.html', syllabus=syllabus, topics=topics, title=f'{syllabus.title} - Topics')


@bp.route('/syllabus/<int:syllabus_id>/topics/create', methods=['GET', 'POST'])
@login_required
@tutor_required
def create_topic(syllabus_id):
    """Create a new topic in a syllabus module"""
    syllabus = CourseSyllabus.query.get_or_404(syllabus_id)
    form = SyllabusTopicForm()
    
    if form.validate_on_submit():
        topic = SyllabusTopic(
            syllabus_id=syllabus_id,
            title=form.title.data,
            description=form.description.data,
            content=form.content.data,
            order_index=form.order_index.data,
            is_required=form.is_required.data,
            estimated_minutes=form.estimated_minutes.data
        )
        db.session.add(topic)
        db.session.commit()
        flash('Topic created successfully!', 'success')
        return redirect(url_for('course.syllabus_topics', syllabus_id=syllabus_id))
    
    return render_template('course/create_topic.html', form=form, syllabus=syllabus, title='Create Topic')


# Course Materials Routes
@bp.route('/syllabus/<int:syllabus_id>/materials')
@login_required
def course_materials(syllabus_id):
    """View course materials for a syllabus module"""
    syllabus = CourseSyllabus.query.get_or_404(syllabus_id)
    materials = CourseMaterial.query.filter_by(syllabus_id=syllabus_id).order_by(CourseMaterial.order_index).all()
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=syllabus.course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to view materials.', 'warning')
        return redirect(url_for('course.course_detail', course_id=syllabus.course_id))
    
    return render_template('course/materials.html', syllabus=syllabus, materials=materials, 
                          title=f'{syllabus.title} - Materials')


@bp.route('/syllabus/<int:syllabus_id>/materials/create', methods=['GET', 'POST'])
@login_required
@tutor_required
def create_material(syllabus_id):
    """Create a new course material"""
    syllabus = CourseSyllabus.query.get_or_404(syllabus_id)
    form = CourseMaterialForm()
    
    if form.validate_on_submit():
        material = CourseMaterial(
            syllabus_id=syllabus_id,
            title=form.title.data,
            description=form.description.data,
            file_type=form.file_type.data,
            file_url=form.file_url.data,
            is_downloadable=form.is_downloadable.data,
            order_index=form.order_index.data
        )
        
        # Handle file upload
        if form.file_path.data:
            upload_result = save_uploaded_file(
                file=form.file_path.data,
                upload_folder=current_app.config['COURSE_MATERIALS_FOLDER'],
                allowed_extensions=current_app.config['ALLOWED_MATERIAL_EXTENSIONS'],
                max_size=current_app.config['MAX_MATERIAL_SIZE']
            )
            
            if upload_result['success']:
                material.file_path = upload_result['file_path']
                material.file_size = upload_result['file_size']
            else:
                flash(f'Error uploading file: {upload_result["message"]}', 'danger')
                return render_template('course/create_material.html', form=form, syllabus=syllabus, title='Add Material')
        
        db.session.add(material)
        db.session.commit()
        flash('Material added successfully!', 'success')
        return redirect(url_for('course.course_materials', syllabus_id=syllabus_id))
    
    return render_template('course/create_material.html', form=form, syllabus=syllabus, title='Add Material')


@bp.route('/materials/<int:material_id>/download')
@login_required
def download_material(material_id):
    """Download a course material"""
    material = CourseMaterial.query.get_or_404(material_id)
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=material.syllabus.course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to download materials.', 'warning')
        return redirect(url_for('course.course_detail', course_id=material.syllabus.course_id))
    
    if not material.is_downloadable:
        flash('This material cannot be downloaded.', 'warning')
        return redirect(url_for('course.course_materials', syllabus_id=material.syllabus_id))
    
    if material.file_path and os.path.exists(material.file_path) and secure_course_material_path(material.file_path):
        return send_from_directory(os.path.dirname(material.file_path),
                                  os.path.basename(material.file_path))
    elif material.file_url:
        return redirect(material.file_url)
    else:
        flash('Material file not found.', 'danger')
        return redirect(url_for('course.course_materials', syllabus_id=material.syllabus_id))


# Progress Tracking Routes
@bp.route('/courses/<int:course_id>/progress')
@login_required
def course_progress(course_id):
    """View course progress"""
    course = Course.query.get_or_404(course_id)
    enrollment = CourseEnrollment.query.filter_by(
        course_id=course_id, student_id=current_user.id).first()
    
    if not enrollment and not current_user.is_tutor() and not current_user.is_admin():
        flash('You must be enrolled in this course to view progress.', 'warning')
        return redirect(url_for('course.course_detail', course_id=course_id))
    
    # Get progress data
    progress_data = []
    syllabus_items = CourseSyllabus.query.filter_by(course_id=course_id).order_by(CourseSyllabus.order_index).all()
    
    for syllabus in syllabus_items:
        progress = StudentProgress.query.filter_by(
            enrollment_id=enrollment.id, syllabus_id=syllabus.id).first()
        
        progress_data.append({
            'syllabus': syllabus,
            'progress': progress,
            'completed': progress.is_completed if progress else False,
            'percentage': progress.progress_percentage if progress else 0
        })
    
    return render_template('course/progress.html', course=course, enrollment=enrollment, 
                          progress_data=progress_data, title=f'{course.title} - Progress')


@bp.route('/progress/<int:progress_id>/update', methods=['POST'])
@login_required
def update_progress(progress_id):
    """Update student progress"""
    progress = StudentProgress.query.get_or_404(progress_id)
    
    # Check if user owns this progress or is tutor/admin
    if progress.enrollment.student_id != current_user.id and not current_user.is_tutor() and not current_user.is_admin():
        flash('You do not have permission to update this progress.', 'danger')
        return redirect(url_for('course.course_progress', course_id=progress.syllabus.course_id))
    
    form = ProgressUpdateForm()
    if form.validate_on_submit():
        progress.is_completed = form.is_completed.data
        progress.notes = form.notes.data
        progress.time_spent_minutes = form.time_spent_minutes.data
        progress.last_accessed = datetime.utcnow()
        
        if form.is_completed.data and not progress.completion_date:
            progress.completion_date = datetime.utcnow()
            progress.progress_percentage = 100.0
        
        db.session.commit()
        flash('Progress updated successfully!', 'success')
    
    return redirect(url_for('course.course_progress', course_id=progress.syllabus.course_id))


# Assignment Management Routes
@bp.route('/courses/<int:course_id>/assignments')
@login_required
def course_assignments(course_id):
    """View course assignments"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    enrollment = None
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to view assignments.', 'warning')
        return redirect(url_for('course.course_detail', course_id=course_id))
    
    assignments = Assignment.query.join(CourseSyllabus).filter(
        CourseSyllabus.course_id == course_id).order_by(Assignment.order_index).all()
    
    return render_template('course/assignments.html', course=course, assignments=assignments, 
                          enrollment=enrollment, title=f'{course.title} - Assignments')


@bp.route('/syllabus/<int:syllabus_id>/assignments/create', methods=['GET', 'POST'])
@login_required
@tutor_required
def create_assignment(syllabus_id):
    """Create a new assignment"""
    syllabus = CourseSyllabus.query.get_or_404(syllabus_id)
    form = AssignmentForm()
    
    if form.validate_on_submit():
        assignment = Assignment(
            syllabus_id=syllabus_id,
            title=form.title.data,
            description=form.description.data,
            instructions=form.instructions.data,
            assignment_type=form.assignment_type.data,
            max_score=form.max_score.data,
            passing_score=form.passing_score.data,
            due_date=form.due_date.data,
            is_published=form.is_published.data,
            allow_late_submission=form.allow_late_submission.data,
            late_penalty_percentage=form.late_penalty_percentage.data,
            max_attempts=form.max_attempts.data,
            time_limit_minutes=form.time_limit_minutes.data,
            order_index=form.order_index.data
        )
        db.session.add(assignment)
        db.session.commit()
        flash('Assignment created successfully!', 'success')
        return redirect(url_for('course.course_assignments', course_id=syllabus.course_id))
    
    return render_template('course/create_assignment.html', form=form, syllabus=syllabus, title='Create Assignment')


@bp.route('/assignments/<int:assignment_id>')
@login_required
def assignment_detail(assignment_id):
    """View assignment details"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    enrollment = None
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=assignment.syllabus.course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to view assignments.', 'warning')
        return redirect(url_for('course.course_detail', course_id=assignment.syllabus.course_id))
    
    # Get submission for this student
    submission = None
    if enrollment:
        submission = AssignmentSubmission.query.filter_by(
            assignment_id=assignment_id, enrollment_id=enrollment.id).first()
    
    return render_template('course/assignment_detail.html', assignment=assignment, 
                          enrollment=enrollment, submission=submission, title=assignment.title)


@bp.route('/assignments/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
def submit_assignment(assignment_id):
    """Submit an assignment"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if user is enrolled
    enrollment = CourseEnrollment.query.filter_by(
        course_id=assignment.syllabus.course_id, student_id=current_user.id).first()
    
    if not enrollment:
        flash('You must be enrolled in this course to submit assignments.', 'warning')
        return redirect(url_for('course.course_detail', course_id=assignment.syllabus.course_id))
    
    form = AssignmentSubmissionForm()
    
    if form.validate_on_submit():
        # Check if submission is late
        is_late = assignment.due_date and datetime.utcnow() > assignment.due_date
        
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            enrollment_id=enrollment.id,
            submission_text=form.submission_text.data,
            is_late=is_late
        )
        
        # Handle file upload
        if form.file_path.data:
            upload_result = save_uploaded_file(
                file=form.file_path.data,
                upload_folder=current_app.config['ASSIGNMENT_SUBMISSIONS_FOLDER'],
                allowed_extensions=current_app.config['ALLOWED_ASSIGNMENT_EXTENSIONS'],
                max_size=current_app.config['MAX_ASSIGNMENT_SIZE']
            )
            
            if upload_result['success']:
                submission.file_path = upload_result['file_path']
            else:
                flash(f'Error uploading file: {upload_result["message"]}', 'danger')
                return render_template('course/submit_assignment.html', form=form, assignment=assignment,
                                      enrollment=enrollment, title='Submit Assignment')
        
        db.session.add(submission)
        db.session.commit()
        flash('Assignment submitted successfully!', 'success')
        return redirect(url_for('course.assignment_detail', assignment_id=assignment_id))
    
    return render_template('course/submit_assignment.html', form=form, assignment=assignment, 
                          enrollment=enrollment, title='Submit Assignment')


@bp.route('/submissions/<int:submission_id>/grade', methods=['GET', 'POST'])
@login_required
@tutor_required
def grade_submission(submission_id):
    """Grade an assignment submission"""
    submission = AssignmentSubmission.query.get_or_404(submission_id)
    form = AssignmentGradingForm()
    
    if form.validate_on_submit():
        submission.score = form.score.data
        submission.feedback = form.feedback.data
        submission.is_graded = True
        submission.graded_at = datetime.utcnow()
        submission.graded_by = current_user.id
        
        db.session.commit()
        flash('Assignment graded successfully!', 'success')
        return redirect(url_for('course.assignment_detail', assignment_id=submission.assignment_id))
    
    return render_template('course/grade_submission.html', form=form, submission=submission, 
                          title='Grade Submission')


# Discussion Board Routes
@bp.route('/courses/<int:course_id>/discussions')
@login_required
def course_discussions(course_id):
    """View course discussion boards"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to view discussions.', 'warning')
        return redirect(url_for('course.course_detail', course_id=course_id))
    
    discussions = DiscussionBoard.query.filter_by(course_id=course_id).order_by(
        DiscussionBoard.is_pinned.desc(), DiscussionBoard.created_at.desc()).all()
    
    return render_template('course/discussions.html', course=course, discussions=discussions, 
                          title=f'{course.title} - Discussions')


@bp.route('/courses/<int:course_id>/discussions/create', methods=['GET', 'POST'])
@login_required
def create_discussion(course_id):
    """Create a new discussion board"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to create discussions.', 'warning')
        return redirect(url_for('course.course_detail', course_id=course_id))
    
    form = DiscussionBoardForm()
    
    if form.validate_on_submit():
        discussion = DiscussionBoard(
            course_id=course_id,
            title=form.title.data,
            description=form.description.data,
            is_pinned=form.is_pinned.data,
            created_by=current_user.id
        )
        db.session.add(discussion)
        db.session.commit()
        flash('Discussion created successfully!', 'success')
        return redirect(url_for('course.course_discussions', course_id=course_id))
    
    return render_template('course/create_discussion.html', form=form, course=course, title='Create Discussion')


@bp.route('/discussions/<int:discussion_id>')
@login_required
def discussion_detail(discussion_id):
    """View discussion board details"""
    discussion = DiscussionBoard.query.get_or_404(discussion_id)
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=discussion.course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to view discussions.', 'warning')
        return redirect(url_for('course.course_detail', course_id=discussion.course_id))
    
    posts = DiscussionPost.query.filter_by(board_id=discussion_id, parent_id=None).order_by(
        DiscussionPost.is_pinned.desc(), DiscussionPost.created_at.asc()).all()
    
    return render_template('course/discussion_detail.html', discussion=discussion, posts=posts, 
                          title=discussion.title)


@bp.route('/discussions/<int:discussion_id>/post', methods=['POST'])
@login_required
def create_post(discussion_id):
    """Create a new discussion post"""
    discussion = DiscussionBoard.query.get_or_404(discussion_id)
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=discussion.course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to post in discussions.', 'warning')
        return redirect(url_for('course.course_detail', course_id=discussion.course_id))
    
    form = DiscussionPostForm()
    
    if form.validate_on_submit():
        post = DiscussionPost(
            board_id=discussion_id,
            parent_id=form.parent_id.data if form.parent_id.data else None,
            author_id=current_user.id,
            content=form.content.data
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
    
    return redirect(url_for('course.discussion_detail', discussion_id=discussion_id))


# Quiz Routes
@bp.route('/syllabus/<int:syllabus_id>/quizzes')
@login_required
def syllabus_quizzes(syllabus_id):
    """View quizzes for a syllabus module"""
    syllabus = CourseSyllabus.query.get_or_404(syllabus_id)
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=syllabus.course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to view quizzes.', 'warning')
        return redirect(url_for('course.course_detail', course_id=syllabus.course_id))
    
    quizzes = Quiz.query.filter_by(syllabus_id=syllabus_id).order_by(Quiz.created_at.desc()).all()
    
    return render_template('course/quizzes.html', syllabus=syllabus, quizzes=quizzes, 
                          title=f'{syllabus.title} - Quizzes')


@bp.route('/syllabus/<int:syllabus_id>/quizzes/create', methods=['GET', 'POST'])
@login_required
@tutor_required
def create_quiz(syllabus_id):
    """Create a new quiz"""
    syllabus = CourseSyllabus.query.get_or_404(syllabus_id)
    form = QuizForm()
    
    if form.validate_on_submit():
        quiz = Quiz(
            syllabus_id=syllabus_id,
            title=form.title.data,
            description=form.description.data,
            time_limit_minutes=form.time_limit_minutes.data,
            max_attempts=form.max_attempts.data,
            passing_score=form.passing_score.data,
            is_published=form.is_published.data,
            shuffle_questions=form.shuffle_questions.data,
            show_correct_answers=form.show_correct_answers.data
        )
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz created successfully!', 'success')
        return redirect(url_for('course.syllabus_quizzes', syllabus_id=syllabus_id))
    
    return render_template('course/create_quiz.html', form=form, syllabus=syllabus, title='Create Quiz')


@bp.route('/quizzes/<int:quiz_id>')
@login_required
def quiz_detail(quiz_id):
    """View quiz details"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if user is enrolled or is the tutor
    is_enrolled = False
    enrollment = None
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=quiz.syllabus.course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        flash('You must be enrolled in this course to view quizzes.', 'warning')
        return redirect(url_for('course.course_detail', course_id=quiz.syllabus.course_id))
    
    # Get questions
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).order_by(QuizQuestion.order_index).all()
    
    # Get previous attempts
    attempts = []
    if enrollment:
        attempts = QuizAttempt.query.filter_by(
            quiz_id=quiz_id, enrollment_id=enrollment.id).order_by(QuizAttempt.attempt_number.desc()).all()
    
    return render_template('course/quiz_detail.html', quiz=quiz, questions=questions, 
                          enrollment=enrollment, attempts=attempts, title=quiz.title)


# Achievement Routes
@bp.route('/achievements')
@login_required
def achievements():
    """View user achievements"""
    earned = EarnedAchievement.query.filter_by(student_id=current_user.id).order_by(
        EarnedAchievement.earned_at.desc()).all()
    
    return render_template('course/achievements.html', earned=earned, title='My Achievements')


# My Courses Route
@bp.route('/my-courses')
@login_required
def my_courses():
    """View user's enrolled courses"""
    enrollments = CourseEnrollment.query.filter_by(student_id=current_user.id).order_by(
        CourseEnrollment.enrollment_date.desc()).all()
    
    return render_template('course/my_courses.html', enrollments=enrollments, title='My Courses')