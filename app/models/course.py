from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db


class Subject(db.Model):
    """
    Subject model for categorizing courses
    """
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    courses = db.relationship('Course', backref='subject', lazy=True)
    tutor_subjects = db.relationship('TutorSubject', backref='subject', lazy=True)
    
    def __repr__(self):
        return f'<Subject {self.name}>'


class Course(db.Model):
    """
    Course model with syllabus, description, and pricing
    """
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    level = db.Column(db.Enum('Beginner', 'Intermediate', 'Advanced', name='course_levels'), 
                     nullable=False, default='Beginner')
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_hours = db.Column(db.Integer, nullable=False)
    thumbnail_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    syllabus = db.relationship('CourseSyllabus', backref='course', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.title}>'


class CourseSyllabus(db.Model):
    """
    CourseSyllabus model for tracking course content
    """
    __tablename__ = 'course_syllabus'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    order_index = db.Column(db.Integer, nullable=False)
    is_milestone = db.Column(db.Boolean, default=False)
    estimated_hours = db.Column(db.Float, default=0.0)
    prerequisites = db.Column(db.Text)  # JSON string of prerequisite syllabus IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    topics = db.relationship('SyllabusTopic', backref='syllabus', lazy=True, cascade='all, delete-orphan')
    materials = db.relationship('CourseMaterial', backref='syllabus', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='syllabus', lazy=True)
    
    def __repr__(self):
        return f'<CourseSyllabus {self.title}>'


class TutorSubject(db.Model):
    """
    Many-to-many relationship between tutors and subjects
    """
    __tablename__ = 'tutor_subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    proficiency_level = db.Column(db.Enum('Beginner', 'Intermediate', 'Advanced', 'Expert', name='proficiency_levels'), 
                                 nullable=False, default='Intermediate')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate tutor-subject combinations
    __table_args__ = (db.UniqueConstraint('tutor_id', 'subject_id', name='unique_tutor_subject'),)
    
    def __repr__(self):
        return f'<TutorSubject {self.tutor.user.email} - {self.subject.name}>'


class SyllabusTopic(db.Model):
    """
    SyllabusTopic model for individual topics within a syllabus module
    """
    __tablename__ = 'syllabus_topics'
    
    id = db.Column(db.Integer, primary_key=True)
    syllabus_id = db.Column(db.Integer, db.ForeignKey('course_syllabus.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    order_index = db.Column(db.Integer, nullable=False)
    is_required = db.Column(db.Boolean, default=True)
    estimated_minutes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SyllabusTopic {self.title}>'


class CourseMaterial(db.Model):
    """
    CourseMaterial model for storing course files and resources
    """
    __tablename__ = 'course_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    syllabus_id = db.Column(db.Integer, db.ForeignKey('course_syllabus.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_type = db.Column(db.Enum('PDF', 'Video', 'Document', 'Image', 'Link', 'Other', name='material_types'),
                         nullable=False, default='Document')
    file_url = db.Column(db.String(500))
    file_path = db.Column(db.String(500))  # For uploaded files
    file_size = db.Column(db.Integer)  # In bytes
    is_downloadable = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseMaterial {self.title}>'


class CourseEnrollment(db.Model):
    """
    CourseEnrollment model for tracking student enrollments in courses
    """
    __tablename__ = 'course_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    progress_percentage = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    certificate_issued = db.Column(db.Boolean, default=False)
    certificate_url = db.Column(db.String(500))
    
    # Relationships
    progress = db.relationship('StudentProgress', backref='enrollment', lazy=True, cascade='all, delete-orphan')
    assignment_submissions = db.relationship('AssignmentSubmission', backref='enrollment', lazy=True)
    
    # Unique constraint to prevent duplicate enrollments
    __table_args__ = (db.UniqueConstraint('course_id', 'student_id', name='unique_course_enrollment'),)
    
    def __repr__(self):
        return f'<CourseEnrollment {self.course.title} - {self.student.email}>'


class Assignment(db.Model):
    """
    Assignment model for course assignments
    """
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    syllabus_id = db.Column(db.Integer, db.ForeignKey('course_syllabus.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)
    assignment_type = db.Column(db.Enum('Homework', 'Quiz', 'Project', 'Exam', 'Discussion', name='assignment_types'),
                               nullable=False, default='Homework')
    max_score = db.Column(db.Float, nullable=False, default=100.0)
    passing_score = db.Column(db.Float, default=60.0)
    due_date = db.Column(db.DateTime)
    is_published = db.Column(db.Boolean, default=False)
    allow_late_submission = db.Column(db.Boolean, default=True)
    late_penalty_percentage = db.Column(db.Float, default=10.0)
    max_attempts = db.Column(db.Integer, default=1)
    time_limit_minutes = db.Column(db.Integer)  # For timed assignments
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy=True, cascade='all, delete-orphan')
    rubric = db.relationship('AssignmentRubric', backref='assignment', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Assignment {self.title}>'


class AssignmentSubmission(db.Model):
    """
    AssignmentSubmission model for tracking student assignment submissions
    """
    __tablename__ = 'assignment_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('course_enrollments.id'), nullable=False)
    submission_text = db.Column(db.Text)
    file_url = db.Column(db.String(500))
    file_path = db.Column(db.String(500))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_late = db.Column(db.Boolean, default=False)
    attempt_number = db.Column(db.Integer, default=1)
    
    # Grading fields
    score = db.Column(db.Float)
    is_graded = db.Column(db.Boolean, default=False)
    graded_at = db.Column(db.DateTime)
    graded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    feedback = db.Column(db.Text)
    plagiarism_score = db.Column(db.Float)
    
    # Relationships
    grader = db.relationship('User', foreign_keys=[graded_by], backref='graded_submissions')
    rubric_scores = db.relationship('RubricScore', backref='submission', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AssignmentSubmission {self.assignment.title} - Attempt {self.attempt_number}>'


class AssignmentRubric(db.Model):
    """
    AssignmentRubric model for assignment grading criteria
    """
    __tablename__ = 'assignment_rubrics'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    max_score = db.Column(db.Float, nullable=False, default=100.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    criteria = db.relationship('RubricCriteria', backref='rubric', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AssignmentRubric {self.title}>'


class RubricCriteria(db.Model):
    """
    RubricCriteria model for individual grading criteria
    """
    __tablename__ = 'rubric_criteria'
    
    id = db.Column(db.Integer, primary_key=True)
    rubric_id = db.Column(db.Integer, db.ForeignKey('assignment_rubrics.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    max_points = db.Column(db.Float, nullable=False, default=10.0)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    scores = db.relationship('RubricScore', backref='criteria', lazy=True)
    
    def __repr__(self):
        return f'<RubricCriteria {self.title}>'


class RubricScore(db.Model):
    """
    RubricScore model for storing rubric scores for submissions
    """
    __tablename__ = 'rubric_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('assignment_submissions.id'), nullable=False)
    criteria_id = db.Column(db.Integer, db.ForeignKey('rubric_criteria.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RubricScore {self.criteria.title}: {self.score}>'


class StudentProgress(db.Model):
    """
    StudentProgress model for tracking student progress through course content
    """
    __tablename__ = 'student_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('course_enrollments.id'), nullable=False)
    syllabus_id = db.Column(db.Integer, db.ForeignKey('course_syllabus.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('syllabus_topics.id'))
    is_completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime)
    time_spent_minutes = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    progress_percentage = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    
    # Relationships
    topic = db.relationship('SyllabusTopic', backref='progress_records')
    
    # Unique constraint to prevent duplicate progress records
    __table_args__ = (db.UniqueConstraint('enrollment_id', 'syllabus_id', 'topic_id', name='unique_progress_record'),)
    
    def __repr__(self):
        return f'<StudentProgress {self.enrollment.student.email} - {self.syllabus.title}>'


class DiscussionBoard(db.Model):
    """
    DiscussionBoard model for course discussions
    """
    __tablename__ = 'discussion_boards'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    syllabus_id = db.Column(db.Integer, db.ForeignKey('course_syllabus.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('DiscussionPost', backref='board', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_discussions')
    
    def __repr__(self):
        return f'<DiscussionBoard {self.title}>'


class DiscussionPost(db.Model):
    """
    DiscussionPost model for discussion board posts
    """
    __tablename__ = 'discussion_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('discussion_boards.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('discussion_posts.id'))  # For replies
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_edited = db.Column(db.Boolean, default=False)
    edited_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', foreign_keys=[author_id], backref='discussion_posts')
    replies = db.relationship('DiscussionPost', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def __repr__(self):
        return f'<DiscussionPost by {self.author.email}>'


class Quiz(db.Model):
    """
    Quiz model for interactive assessments
    """
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    syllabus_id = db.Column(db.Integer, db.ForeignKey('course_syllabus.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    time_limit_minutes = db.Column(db.Integer)
    max_attempts = db.Column(db.Integer, default=1)
    passing_score = db.Column(db.Float, default=60.0)
    is_published = db.Column(db.Boolean, default=False)
    shuffle_questions = db.Column(db.Boolean, default=False)
    show_correct_answers = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Quiz {self.title}>'


class QuizQuestion(db.Model):
    """
    QuizQuestion model for individual quiz questions
    """
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.Enum('Multiple Choice', 'True/False', 'Short Answer', 'Essay', name='question_types'),
                             nullable=False, default='Multiple Choice')
    points = db.Column(db.Float, nullable=False, default=1.0)
    explanation = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    options = db.relationship('QuizOption', backref='question', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<QuizQuestion {self.question_text[:50]}...>'


class QuizOption(db.Model):
    """
    QuizOption model for multiple choice options
    """
    __tablename__ = 'quiz_options'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    option_text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<QuizOption {self.option_text[:30]}...>'


class QuizAttempt(db.Model):
    """
    QuizAttempt model for tracking student quiz attempts
    """
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('course_enrollments.id'), nullable=False)
    attempt_number = db.Column(db.Integer, default=1)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    score = db.Column(db.Float)
    is_passed = db.Column(db.Boolean)
    time_taken_minutes = db.Column(db.Integer)
    
    # Relationships
    answers = db.relationship('QuizAnswer', backref='attempt', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<QuizAttempt {self.quiz.title} - Attempt {self.attempt_number}>'


class QuizAnswer(db.Model):
    """
    QuizAnswer model for storing student quiz answers
    """
    __tablename__ = 'quiz_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('quiz_options.id'))
    text_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    points_earned = db.Column(db.Float, default=0.0)
    
    # Relationships
    selected_option = db.relationship('QuizOption', backref='answers')
    
    def __repr__(self):
        return f'<QuizAnswer for Question {self.question_id}>'


class Achievement(db.Model):
    """
    Achievement model for student achievements and badges
    """
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon_url = db.Column(db.String(500))
    badge_color = db.Column(db.String(7), default='#007bff')  # Hex color
    points = db.Column(db.Integer, default=0)
    achievement_type = db.Column(db.Enum('Course Completion', 'Assignment Excellence', 'Perfect Score',
                                        'Quick Learner', 'Discussion Leader', 'Consistency', name='achievement_types'),
                               nullable=False, default='Course Completion')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    earned_achievements = db.relationship('EarnedAchievement', backref='achievement', lazy=True)
    
    def __repr__(self):
        return f'<Achievement {self.title}>'


class EarnedAchievement(db.Model):
    """
    EarnedAchievement model for tracking achievements earned by students
    """
    __tablename__ = 'earned_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User', backref='earned_achievements')
    course = db.relationship('Course', backref='earned_achievements')
    
    # Unique constraint to prevent duplicate achievements
    __table_args__ = (db.UniqueConstraint('achievement_id', 'student_id', 'course_id', name='unique_earned_achievement'),)
    
    def __repr__(self):
        return f'<EarnedAchievement {self.achievement.title} by {self.student.email}>'