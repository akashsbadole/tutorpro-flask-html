from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, IntegerField, DateTimeField, BooleanField, FileField, FieldList, FormField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL, ValidationError
from wtforms.widgets import TextArea
from flask_wtf.file import FileAllowed, FileRequired
from app.models.course import Subject, Course
from datetime import datetime


class CourseForm(FlaskForm):
    """Form for creating and editing courses"""
    title = StringField('Course Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Course Description', validators=[DataRequired(), Length(min=10)])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    level = SelectField('Course Level', choices=[
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced')
    ], validators=[DataRequired()])
    price = FloatField('Price ($)', validators=[DataRequired(), NumberRange(min=0)])
    duration_hours = IntegerField('Duration (hours)', validators=[DataRequired(), NumberRange(min=1)])
    thumbnail_url = StringField('Thumbnail URL', validators=[Optional(), URL()])
    submit = SubmitField('Save Course')
    
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        self.subject_id.choices = [(subject.id, subject.name) for subject in Subject.query.order_by('name').all()]


class SyllabusForm(FlaskForm):
    """Form for creating and editing course syllabus modules"""
    title = StringField('Module Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Module Description', validators=[Optional()])
    content = TextAreaField('Module Content', validators=[Optional()])
    order_index = IntegerField('Order', validators=[DataRequired(), NumberRange(min=1)])
    is_milestone = BooleanField('Mark as Milestone')
    estimated_hours = FloatField('Estimated Hours', validators=[Optional(), NumberRange(min=0)])
    prerequisites = TextAreaField('Prerequisites (comma-separated module IDs)', validators=[Optional()])
    submit = SubmitField('Save Module')


class SyllabusTopicForm(FlaskForm):
    """Form for creating and editing syllabus topics"""
    title = StringField('Topic Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Topic Description', validators=[Optional()])
    content = TextAreaField('Topic Content', validators=[Optional()])
    order_index = IntegerField('Order', validators=[DataRequired(), NumberRange(min=1)])
    is_required = BooleanField('Required Topic')
    estimated_minutes = IntegerField('Estimated Minutes', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Save Topic')


class CourseMaterialForm(FlaskForm):
    """Form for adding course materials"""
    title = StringField('Material Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Material Description', validators=[Optional()])
    file_type = SelectField('Material Type', choices=[
        ('PDF', 'PDF Document'),
        ('Video', 'Video File'),
        ('Document', 'Document'),
        ('Image', 'Image'),
        ('Link', 'External Link'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    file_url = StringField('File URL', validators=[Optional(), URL()])
    file_path = FileField('Upload File', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'ppt', 'pptx', 'mp4', 'avi', 'mov', 'jpg', 'jpeg', 'png', 'gif'], 
                   'PDFs, documents, videos, and images only!')
    ])
    is_downloadable = BooleanField('Allow Download')
    order_index = IntegerField('Order', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Add Material')


class AssignmentForm(FlaskForm):
    """Form for creating and editing assignments"""
    title = StringField('Assignment Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Assignment Description', validators=[DataRequired(), Length(min=10)])
    instructions = TextAreaField('Instructions', validators=[Optional()])
    assignment_type = SelectField('Assignment Type', choices=[
        ('Homework', 'Homework'),
        ('Quiz', 'Quiz'),
        ('Project', 'Project'),
        ('Exam', 'Exam'),
        ('Discussion', 'Discussion')
    ], validators=[DataRequired()])
    max_score = FloatField('Maximum Score', validators=[DataRequired(), NumberRange(min=0)])
    passing_score = FloatField('Passing Score', validators=[Optional(), NumberRange(min=0)])
    due_date = DateTimeField('Due Date', format='%Y-%m-%d %H:%M', validators=[Optional()])
    is_published = BooleanField('Publish Assignment')
    allow_late_submission = BooleanField('Allow Late Submission')
    late_penalty_percentage = FloatField('Late Penalty (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    max_attempts = IntegerField('Maximum Attempts', validators=[Optional(), NumberRange(min=1)])
    time_limit_minutes = IntegerField('Time Limit (minutes)', validators=[Optional(), NumberRange(min=1)])
    order_index = IntegerField('Order', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Save Assignment')


class AssignmentSubmissionForm(FlaskForm):
    """Form for submitting assignments"""
    submission_text = TextAreaField('Submission Text', validators=[Optional()])
    file_path = FileField('Upload File', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'zip', 'rar'], 
                   'PDFs, documents, text files, and archives only!')
    ])
    submit = SubmitField('Submit Assignment')


class AssignmentGradingForm(FlaskForm):
    """Form for grading assignments"""
    score = FloatField('Score', validators=[DataRequired(), NumberRange(min=0)])
    feedback = TextAreaField('Feedback', validators=[Optional()])
    submit = SubmitField('Grade Submission')


class RubricCriteriaForm(FlaskForm):
    """Form for rubric criteria"""
    title = StringField('Criteria Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Criteria Description', validators=[Optional()])
    max_points = FloatField('Maximum Points', validators=[DataRequired(), NumberRange(min=0)])
    order_index = IntegerField('Order', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Add Criteria')


class RubricScoreForm(FlaskForm):
    """Form for scoring rubric criteria"""
    score = FloatField('Score', validators=[DataRequired(), NumberRange(min=0)])
    feedback = TextAreaField('Feedback', validators=[Optional()])
    submit = SubmitField('Save Score')


class DiscussionBoardForm(FlaskForm):
    """Form for creating discussion boards"""
    title = StringField('Discussion Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Discussion Description', validators=[Optional()])
    is_pinned = BooleanField('Pin Discussion')
    submit = SubmitField('Create Discussion')


class DiscussionPostForm(FlaskForm):
    """Form for discussion posts"""
    content = TextAreaField('Post Content', validators=[DataRequired(), Length(min=5)])
    parent_id = HiddenField('Reply To')
    submit = SubmitField('Post')


class QuizForm(FlaskForm):
    """Form for creating quizzes"""
    title = StringField('Quiz Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Quiz Description', validators=[Optional()])
    time_limit_minutes = IntegerField('Time Limit (minutes)', validators=[Optional(), NumberRange(min=1)])
    max_attempts = IntegerField('Maximum Attempts', validators=[Optional(), NumberRange(min=1)])
    passing_score = FloatField('Passing Score (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    is_published = BooleanField('Publish Quiz')
    shuffle_questions = BooleanField('Shuffle Questions')
    show_correct_answers = BooleanField('Show Correct Answers')
    submit = SubmitField('Save Quiz')


class QuizQuestionForm(FlaskForm):
    """Form for quiz questions"""
    question_text = TextAreaField('Question', validators=[DataRequired(), Length(min=5)])
    question_type = SelectField('Question Type', choices=[
        ('Multiple Choice', 'Multiple Choice'),
        ('True/False', 'True/False'),
        ('Short Answer', 'Short Answer'),
        ('Essay', 'Essay')
    ], validators=[DataRequired()])
    points = FloatField('Points', validators=[DataRequired(), NumberRange(min=0)])
    explanation = TextAreaField('Explanation', validators=[Optional()])
    order_index = IntegerField('Order', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Save Question')


class QuizOptionForm(FlaskForm):
    """Form for quiz options"""
    option_text = StringField('Option Text', validators=[DataRequired(), Length(min=1)])
    is_correct = BooleanField('Correct Answer')
    order_index = IntegerField('Order', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Add Option')


class QuizAttemptForm(FlaskForm):
    """Form for quiz attempts"""
    submit = SubmitField('Submit Quiz')


class AchievementForm(FlaskForm):
    """Form for creating achievements"""
    title = StringField('Achievement Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Achievement Description', validators=[DataRequired(), Length(min=10)])
    icon_url = StringField('Icon URL', validators=[Optional(), URL()])
    badge_color = StringField('Badge Color (hex)', validators=[Optional(), Length(min=7, max=7)])
    points = IntegerField('Points', validators=[Optional(), NumberRange(min=0)])
    achievement_type = SelectField('Achievement Type', choices=[
        ('Course Completion', 'Course Completion'),
        ('Assignment Excellence', 'Assignment Excellence'),
        ('Perfect Score', 'Perfect Score'),
        ('Quick Learner', 'Quick Learner'),
        ('Discussion Leader', 'Discussion Leader'),
        ('Consistency', 'Consistency')
    ], validators=[DataRequired()])
    submit = SubmitField('Create Achievement')


class CourseEnrollmentForm(FlaskForm):
    """Form for course enrollment"""
    submit = SubmitField('Enroll in Course')


class ProgressUpdateForm(FlaskForm):
    """Form for updating progress"""
    is_completed = BooleanField('Mark as Completed')
    notes = TextAreaField('Notes', validators=[Optional()])
    time_spent_minutes = IntegerField('Time Spent (minutes)', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Update Progress')


class SearchForm(FlaskForm):
    """Form for searching courses"""
    query = StringField('Search', validators=[Optional()])
    subject = SelectField('Subject', coerce=int, validators=[Optional()])
    level = SelectField('Level', choices=[
        ('', 'All Levels'),
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced')
    ], validators=[Optional()])
    min_price = FloatField('Min Price', validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField('Max Price', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Search')
    
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.subject.choices = [(0, 'All Subjects')] + [(subject.id, subject.name) for subject in Subject.query.order_by('name').all()]


class FileUploadForm(FlaskForm):
    """General file upload form"""
    file = FileField('Select File', validators=[FileRequired()])
    submit = SubmitField('Upload')