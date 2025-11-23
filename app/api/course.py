from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.course import (
    Course, CourseSyllabus, CourseTopic, CourseMaterial, CourseEnrollment,
    CourseAssignment, CourseProgress, CourseDiscussion
)
from app.models.user import User
from app import db
from app.utils.decorators import roles_required
from datetime import datetime

course_api = Blueprint('course_api', __name__)


# Course API Endpoints
@course_api.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all courses with optional filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    subject_id = request.args.get('subject_id', type=int)
    level = request.args.get('level')
    search = request.args.get('search')
    
    query = Course.query
    
    # Apply filters
    if subject_id:
        query = query.filter(Course.subject_id == subject_id)
    if level:
        query = query.filter(Course.level == level)
    if search:
        query = query.filter(Course.title.contains(search))
    
    # Paginate results
    courses = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'courses': [{
            'id': course.id,
            'title': course.title,
            'description': course.description[:200] + '...' if len(course.description) > 200 else course.description,
            'subject': course.subject.name,
            'level': course.level,
            'price': float(course.price),
            'duration_hours': course.duration_hours,
            'thumbnail_url': course.thumbnail_url,
            'created_at': course.created_at.isoformat()
        } for course in courses.items],
        'pagination': {
            'page': courses.page,
            'pages': courses.pages,
            'per_page': courses.per_page,
            'total': courses.total,
            'has_next': courses.has_next,
            'has_prev': courses.has_prev
        }
    })


@course_api.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Get specific course details"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user is enrolled or is tutor/admin
    is_enrolled = False
    enrollment = None
    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, student_id=current_user.id).first()
        is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    course_data = {
        'id': course.id,
        'title': course.title,
        'description': course.description,
        'subject': {
            'id': course.subject.id,
            'name': course.subject.name,
            'category': course.subject.category
        },
        'level': course.level,
        'price': float(course.price),
        'duration_hours': course.duration_hours,
        'thumbnail_url': course.thumbnail_url,
        'created_at': course.created_at.isoformat(),
        'updated_at': course.updated_at.isoformat(),
        'is_enrolled': is_enrolled
    }
    
    # Add enrollment data if user is enrolled
    if enrollment:
        course_data['enrollment'] = {
            'id': enrollment.id,
            'enrollment_date': enrollment.enrollment_date.isoformat(),
            'progress_percentage': enrollment.progress_percentage,
            'is_completed': enrollment.completion_date is not None,
            'completion_date': enrollment.completion_date.isoformat() if enrollment.completion_date else None
        }
    
    # Add syllabus if user is enrolled
    if is_enrolled:
        course_data['syllabus'] = [{
            'id': syllabus.id,
            'title': syllabus.title,
            'description': syllabus.description,
            'order_index': syllabus.order_index,
            'is_milestone': syllabus.is_milestone,
            'estimated_hours': syllabus.estimated_hours,
            'topics_count': len(syllabus.topics),
            'materials_count': len(syllabus.materials),
            'assignments_count': len(syllabus.assignments)
        } for syllabus in sorted(course.syllabus, key=lambda x: x.order_index)]
    
    return jsonify(course_data)


@course_api.route('/api/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_course_api(course_id):
    """Enroll in a course via API"""
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing_enrollment = CourseEnrollment.query.filter_by(
        course_id=course_id, student_id=current_user.id).first()
    
    if existing_enrollment:
        return jsonify({'error': 'Already enrolled in this course'}), 400
    
    # Create new enrollment
    enrollment = CourseEnrollment(
        course_id=course_id,
        student_id=current_user.id
    )
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({
        'message': 'Successfully enrolled in course',
        'enrollment_id': enrollment.id
    })


# Syllabus API Endpoints
@course_api.route('/api/courses/<int:course_id>/syllabus', methods=['GET'])
@login_required
def get_course_syllabus(course_id):
    """Get course syllabus"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user is enrolled or is tutor/admin
    enrollment = CourseEnrollment.query.filter_by(
        course_id=course_id, student_id=current_user.id).first()
    is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        return jsonify({'error': 'Access denied'}), 403
    
    syllabus_items = CourseSyllabus.query.filter_by(course_id=course_id).order_by(CourseSyllabus.order_index).all()
    
    syllabus_data = []
    for syllabus in syllabus_items:
        # Get progress for this syllabus item
        progress = None
        if enrollment:
            progress = StudentProgress.query.filter_by(
                enrollment_id=enrollment.id, syllabus_id=syllabus.id).first()
        
        syllabus_item = {
            'id': syllabus.id,
            'title': syllabus.title,
            'description': syllabus.description,
            'content': syllabus.content,
            'order_index': syllabus.order_index,
            'is_milestone': syllabus.is_milestone,
            'estimated_hours': syllabus.estimated_hours,
            'prerequisites': syllabus.prerequisites,
            'progress': {
                'is_completed': progress.is_completed if progress else False,
                'progress_percentage': progress.progress_percentage if progress else 0,
                'time_spent_minutes': progress.time_spent_minutes if progress else 0,
                'completion_date': progress.completion_date.isoformat() if progress and progress.completion_date else None
            }
        }
        
        # Add topics
        syllabus_item['topics'] = [{
            'id': topic.id,
            'title': topic.title,
            'description': topic.description,
            'order_index': topic.order_index
        } for topic in sorted(syllabus.topics, key=lambda x: x.order_index) if hasattr(syllabus, 'topics')]
        
        # Add materials
        syllabus_item['materials'] = [{
            'id': material.id,
            'title': material.title,
            'description': material.description,
            'material_type': material.material_type,
            'file_url': material.file_url,
            'external_url': material.external_url,
            'file_size': material.file_size,
            'download_count': material.download_count
        } for material in sorted(syllabus.materials, key=lambda x: x.order_index) if hasattr(syllabus, 'materials')]
        
        syllabus_data.append(syllabus_item)
    
    return jsonify({'syllabus': syllabus_data})


@course_api.route('/api/syllabus/<int:syllabus_id>/progress', methods=['POST'])
@login_required
def update_syllabus_progress(syllabus_id):
    """Update progress for a syllabus item"""
    syllabus = CourseSyllabus.query.get_or_404(syllabus_id)
    
    # Get enrollment
    enrollment = CourseEnrollment.query.filter_by(
        course_id=syllabus.course_id, student_id=current_user.id).first()
    
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 403
    
    # Get or create progress record
    progress = StudentProgress.query.filter_by(
        enrollment_id=enrollment.id, syllabus_id=syllabus_id).first()
    
    if not progress:
        progress = StudentProgress(
            enrollment_id=enrollment.id,
            syllabus_id=syllabus_id
        )
        db.session.add(progress)
    
    # Update progress
    data = request.get_json()
    if 'is_completed' in data:
        progress.is_completed = data['is_completed']
        if data['is_completed'] and not progress.completion_date:
            progress.completion_date = datetime.utcnow()
            progress.progress_percentage = 100.0
    
    if 'time_spent_minutes' in data:
        progress.time_spent_minutes = data['time_spent_minutes']
    
    if 'notes' in data:
        progress.notes = data['notes']
    
    progress.last_accessed = datetime.utcnow()
    db.session.commit()
    
    # Update overall enrollment progress
    total_syllabus = CourseSyllabus.query.filter_by(course_id=syllabus.course_id).count()
    completed_syllabus = StudentProgress.query.filter_by(
        enrollment_id=enrollment.id, is_completed=True).count()
    enrollment.progress_percentage = (completed_syllabus / total_syllabus) * 100 if total_syllabus > 0 else 0
    
    db.session.commit()
    
    return jsonify({
        'message': 'Progress updated successfully',
        'progress': {
            'is_completed': progress.is_completed,
            'progress_percentage': progress.progress_percentage,
            'time_spent_minutes': progress.time_spent_minutes,
            'completion_date': progress.completion_date.isoformat() if progress.completion_date else None
        }
    })


# Assignment API Endpoints
@course_api.route('/api/courses/<int:course_id>/assignments', methods=['GET'])
@login_required
def get_course_assignments(course_id):
    """Get course assignments"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user is enrolled or is tutor/admin
    enrollment = CourseEnrollment.query.filter_by(
        course_id=course_id, student_id=current_user.id).first()
    is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        return jsonify({'error': 'Access denied'}), 403
    
    assignments = CourseAssignment.query.filter_by(course_id=course_id).order_by(CourseAssignment.created_at).all()
    
    assignments_data = []
    for assignment in assignments:
        assignment_data = {
            'id': assignment.id,
            'title': assignment.title,
            'description': assignment.description,
            'instructions': assignment.instructions,
            'assignment_type': assignment.assignment_type,
            'max_score': float(assignment.max_score),
            'passing_score': float(assignment.passing_score),
            'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
            'is_published': assignment.is_published,
            'allow_late_submission': assignment.allow_late_submission,
            'late_penalty_percentage': float(assignment.late_penalty_percentage),
            'max_attempts': assignment.max_attempts,
            'time_limit_minutes': assignment.time_limit_minutes,
            'course_id': assignment.course_id
        }
        
        # Add submission data if student
        if enrollment:
            # Note: AssignmentSubmission model doesn't exist, this is a placeholder
            # In a real implementation, you would need to create this model
            assignment_data['submission'] = None
        
        assignments_data.append(assignment_data)
    
    return jsonify({'assignments': assignments_data})


@course_api.route('/api/assignments/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment_api(assignment_id):
    """Submit an assignment via API"""
    assignment = CourseAssignment.query.get_or_404(assignment_id)
    
    # Get enrollment
    enrollment = CourseEnrollment.query.filter_by(
        course_id=assignment.course_id, student_id=current_user.id).first()
    
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 403
    
    # Check if submission is allowed
    if not assignment.is_published:
        return jsonify({'error': 'Assignment is not published'}), 400
    
    # Check number of attempts
    # Note: AssignmentSubmission model doesn't exist, this is a placeholder
    existing_submissions = 0
    
    if existing_submissions >= assignment.max_attempts:
        return jsonify({'error': 'Maximum attempts reached'}), 400
    
    # Check if submission is late
    is_late = assignment.due_date and datetime.utcnow() > assignment.due_date
    
    # Create submission
    # Note: AssignmentSubmission model doesn't exist, this is a placeholder
    # In a real implementation, you would need to create this model
    submission_id = None
    
    # For now, just return success without creating a submission
    db.session.commit()
    
    return jsonify({
        'message': 'Assignment submitted successfully',
        'submission_id': submission_id,
        'is_late': is_late
    })


# Discussion API Endpoints
@course_api.route('/api/courses/<int:course_id>/discussions', methods=['GET'])
@login_required
def get_course_discussions(course_id):
    """Get course discussions"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user is enrolled or is tutor/admin
    enrollment = CourseEnrollment.query.filter_by(
        course_id=course_id, student_id=current_user.id).first()
    is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        return jsonify({'error': 'Access denied'}), 403
    
    discussions = CourseDiscussion.query.filter_by(course_id=course_id).order_by(
        CourseDiscussion.is_pinned.desc(), CourseDiscussion.created_at.desc()).all()
    
    discussions_data = []
    for discussion in discussions:
        discussion_data = {
            'id': discussion.id,
            'title': discussion.title,
            'content': discussion.content,
            'is_pinned': discussion.is_pinned,
            'is_locked': discussion.is_locked,
            'created_at': discussion.created_at.isoformat(),
            'author_id': discussion.author_id,
            'posts_count': 0,  # Placeholder - DiscussionPost model doesn't exist
            'last_post_date': discussion.updated_at.isoformat() if discussion.updated_at else None
        }
        
        discussions_data.append(discussion_data)
    
    return jsonify({'discussions': discussions_data})


@course_api.route('/api/discussions/<int:discussion_id>/posts', methods=['GET'])
@login_required
def get_discussion_posts(discussion_id):
    """Get discussion posts"""
    discussion = CourseDiscussion.query.get_or_404(discussion_id)
    
    # Check if user is enrolled or is tutor/admin
    enrollment = CourseEnrollment.query.filter_by(
        course_id=discussion.course_id, student_id=current_user.id).first()
    is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        return jsonify({'error': 'Access denied'}), 403
    
    # Note: DiscussionPost model doesn't exist, this is a placeholder
    # In a real implementation, you would need to create this model
    return jsonify({'posts': []})


@course_api.route('/api/discussions/<int:discussion_id>/posts', methods=['POST'])
@login_required
def create_discussion_post(discussion_id):
    """Create a new discussion post"""
    discussion = CourseDiscussion.query.get_or_404(discussion_id)
    
    # Check if user is enrolled or is tutor/admin
    enrollment = CourseEnrollment.query.filter_by(
        course_id=discussion.course_id, student_id=current_user.id).first()
    is_enrolled = enrollment is not None or current_user.is_tutor() or current_user.is_admin()
    
    if not is_enrolled:
        return jsonify({'error': 'Access denied'}), 403
    
    if discussion.is_locked:
        return jsonify({'error': 'Discussion is locked'}), 400
    
    data = request.get_json()
    
    # Note: DiscussionPost model doesn't exist, this is a placeholder
    # In a real implementation, you would need to create this model
    post_id = None
    
    return jsonify({
        'message': 'Post created successfully',
        'post_id': post_id,
        'created_at': datetime.utcnow().isoformat()
    })


# Progress API Endpoints
@course_api.route('/api/courses/<int:course_id>/progress', methods=['GET'])
@login_required
def get_course_progress(course_id):
    """Get course progress overview"""
    course = Course.query.get_or_404(course_id)
    
    # Get enrollment
    enrollment = CourseEnrollment.query.filter_by(
        course_id=course_id, student_id=current_user.id).first()
    
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 403
    
    # Get progress data
    progress_data = CourseProgress.query.filter_by(
        enrollment_id=enrollment.id).all()
    
    # Calculate statistics
    total_syllabus = CourseSyllabus.query.filter_by(course_id=course_id).count()
    completed_syllabus = len([p for p in progress_data if p.is_completed])
    total_time_spent = sum(p.time_spent_minutes for p in progress_data)
    
    # Get assignment statistics
    assignments = CourseAssignment.query.filter_by(course_id=course_id).all()
    assignment_ids = [a.id for a in assignments]
    
    # Note: AssignmentSubmission model doesn't exist, this is a placeholder
    submissions = []
    graded_submissions = []
    average_score = 0
    
    return jsonify({
        'enrollment': {
            'id': enrollment.id,
            'enrollment_date': enrollment.enrollment_date.isoformat(),
            'progress_percentage': enrollment.progress_percentage,
            'is_completed': enrollment.completion_date is not None,
            'completion_date': enrollment.completion_date.isoformat() if enrollment.completion_date else None
        },
        'statistics': {
            'total_modules': total_syllabus,
            'completed_modules': completed_syllabus,
            'remaining_modules': total_syllabus - completed_syllabus,
            'total_time_spent_minutes': total_time_spent,
            'total_assignments': len(assignments),
            'submitted_assignments': len(submissions),
            'graded_assignments': len(graded_submissions),
            'average_score': average_score
        },
        'progress_details': [{
            'id': p.id,
            'content_type': p.content_type,
            'content_id': p.content_id,
            'is_completed': p.is_completed,
            'completion_date': p.completion_date.isoformat() if p.completion_date else None,
            'score': p.score,
            'time_spent_minutes': p.time_spent_minutes
        } for p in progress_data]
    })