from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.qa_system import Question, Answer, Tag, QuestionTag, QuestionVote, AnswerVote, QuestionFollow
from app.models.user import User
from app.models.subject import Subject
from app.models.course import Course
from app import db
from datetime import datetime

qa_bp = Blueprint('qa', __name__, url_prefix='/api/v1/qa')

# Question endpoints

@qa_bp.route('/questions', methods=['GET'])
def get_questions():
    """Get questions with filtering and pagination"""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        subject_id = request.args.get('subject_id', type=int)
        course_id = request.args.get('course_id', type=int)
        status = request.args.get('status', 'Open')
        question_type = request.args.get('question_type')
        difficulty = request.args.get('difficulty')
        sort_by = request.args.get('sort_by', 'latest')  # latest, popular, unanswered
        
        # Build query
        query = Question.query
        
        # Apply filters
        if subject_id:
            query = query.filter(Question.subject_id == subject_id)
        if course_id:
            query = query.filter(Question.course_id == course_id)
        if status:
            query = query.filter(Question.status == status)
        if question_type:
            query = query.filter(Question.question_type == question_type)
        if difficulty:
            query = query.filter(Question.difficulty_level == difficulty)
        
        # Only show public questions
        query = query.filter(Question.is_public == True)
        
        # Apply sorting
        if sort_by == 'popular':
            query = query.order_by(Question.upvote_count.desc())
        elif sort_by == 'unanswered':
            query = query.filter(Question.status == 'Open').order_by(Question.created_at.desc())
        else:  # latest
            query = query.order_by(Question.created_at.desc())
        
        # Paginate
        questions = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'questions': [question.to_dict() for question in questions.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': questions.total,
                    'pages': questions.pages,
                    'has_next': questions.has_next,
                    'has_prev': questions.has_prev
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting questions: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to retrieve questions'
            }
        }), 500


@qa_bp.route('/questions', methods=['POST'])
@jwt_required()
def create_question():
    """Create a new question"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('title') or not data.get('content'):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Title and content are required'
                }
            }), 400
        
        # Create question
        question = Question(
            title=data['title'],
            content=data['content'],
            student_id=user_id,
            subject_id=data.get('subject_id'),
            course_id=data.get('course_id'),
            question_type=data.get('question_type', 'General Inquiry'),
            difficulty_level=data.get('difficulty_level', 'Beginner'),
            priority=data.get('priority', 'Medium'),
            is_public=data.get('is_public', True),
            is_anonymous=data.get('is_anonymous', False)
        )
        
        db.session.add(question)
        db.session.flush()  # Get the question ID
        
        # Add tags if provided
        if 'tags' in data and data['tags']:
            for tag_name in data['tags']:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()
                
                question_tag = QuestionTag(question_id=question.id, tag_id=tag.id)
                db.session.add(question_tag)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': question.to_dict(),
            'message': 'Question created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating question: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to create question'
            }
        }), 500


@qa_bp.route('/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    """Get question details"""
    try:
        question = Question.query.get_or_404(question_id)
        
        # Increment view count
        question.view_count += 1
        question.last_activity_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': question.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting question: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to retrieve question'
            }
        }), 500


@qa_bp.route('/questions/<int:question_id>', methods=['PUT'])
@jwt_required()
def update_question(question_id):
    """Update question"""
    try:
        user_id = get_jwt_identity()
        question = Question.query.get_or_404(question_id)
        
        # Check if user owns the question
        if question.student_id != user_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'You can only update your own questions'
                }
            }), 403
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            question.title = data['title']
        if 'content' in data:
            question.content = data['content']
        if 'is_public' in data:
            question.is_public = data['is_public']
        
        question.updated_at = datetime.utcnow()
        question.last_activity_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': question.to_dict(),
            'message': 'Question updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating question: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to update question'
            }
        }), 500


@qa_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@jwt_required()
def delete_question(question_id):
    """Delete question"""
    try:
        user_id = get_jwt_identity()
        question = Question.query.get_or_404(question_id)
        
        # Check if user owns the question
        if question.student_id != user_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'You can only delete your own questions'
                }
            }), 403
        
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Question deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting question: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to delete question'
            }
        }), 500


# Answer endpoints

@qa_bp.route('/questions/<int:question_id>/answers', methods=['GET'])
def get_answers(question_id):
    """Get answers for a question"""
    try:
        question = Question.query.get_or_404(question_id)
        
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        sort_by = request.args.get('sort_by', 'latest')  # latest, popular, accepted
        
        # Build query
        query = Answer.query.filter_by(question_id=question_id)
        
        # Apply sorting
        if sort_by == 'popular':
            query = query.order_by(Answer.upvote_count.desc())
        elif sort_by == 'accepted':
            query = query.filter(Answer.is_accepted == True)
        else:  # latest
            query = query.order_by(Answer.created_at.desc())
        
        # Paginate
        answers = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'answers': [answer.to_dict() for answer in answers.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': answers.total,
                    'pages': answers.pages,
                    'has_next': answers.has_next,
                    'has_prev': answers.has_prev
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting answers: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to retrieve answers'
            }
        }), 500


@qa_bp.route('/questions/<int:question_id>/answers', methods=['POST'])
@jwt_required()
def create_answer(question_id):
    """Create a new answer"""
    try:
        user_id = get_jwt_identity()
        question = Question.query.get_or_404(question_id)
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('content'):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Answer content is required'
                }
            }), 400
        
        # Check if user is a tutor
        user = User.query.get(user_id)
        if not user or user.role != 'tutor':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'Only tutors can answer questions'
                }
            }), 403
        
        # Create answer
        answer = Answer(
            content=data['content'],
            question_id=question_id,
            tutor_id=user_id
        )
        
        db.session.add(answer)
        
        # Update question status and activity
        question.status = 'Answered'
        question.last_activity_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': answer.to_dict(),
            'message': 'Answer created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating answer: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to create answer'
            }
        }), 500


@qa_bp.route('/answers/<int:answer_id>/accept', methods=['POST'])
@jwt_required()
def accept_answer(answer_id):
    """Accept an answer"""
    try:
        user_id = get_jwt_identity()
        answer = Answer.query.get_or_404(answer_id)
        question = answer.question
        
        # Check if user owns the question
        if question.student_id != user_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'You can only accept answers to your own questions'
                }
            }), 403
        
        # Update answer and question
        answer.is_accepted = True
        answer.accepted_at = datetime.utcnow()
        answer.accepted_by = user_id
        
        question.accepted_answer_id = answer_id
        question.status = 'Answered'
        question.resolved_at = datetime.utcnow()
        question.last_activity_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': answer.to_dict(),
            'message': 'Answer accepted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error accepting answer: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to accept answer'
            }
        }), 500


# Voting endpoints

@qa_bp.route('/questions/<int:question_id>/vote', methods=['POST'])
@jwt_required()
def vote_question(question_id):
    """Vote on a question"""
    try:
        user_id = get_jwt_identity()
        question = Question.query.get_or_404(question_id)
        data = request.get_json()
        
        vote_type = data.get('vote_type')
        if vote_type not in ['Upvote', 'Downvote']:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid vote type'
                }
            }), 400
        
        # Check if user already voted
        existing_vote = QuestionVote.query.filter_by(
            question_id=question_id,
            user_id=user_id
        ).first()
        
        if existing_vote:
            # Update existing vote
            if existing_vote.vote_type == vote_type:
                # Remove vote
                db.session.delete(existing_vote)
                if vote_type == 'Upvote':
                    question.upvote_count -= 1
                else:
                    question.downvote_count -= 1
            else:
                # Change vote type
                existing_vote.vote_type = vote_type
                if vote_type == 'Upvote':
                    question.upvote_count += 1
                    question.downvote_count -= 1
                else:
                    question.downvote_count += 1
                    question.upvote_count -= 1
        else:
            # Create new vote
            vote = QuestionVote(
                question_id=question_id,
                user_id=user_id,
                vote_type=vote_type
            )
            db.session.add(vote)
            
            if vote_type == 'Upvote':
                question.upvote_count += 1
            else:
                question.downvote_count += 1
        
        question.last_activity_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'upvote_count': question.upvote_count,
                'downvote_count': question.downvote_count,
                'vote_score': question.get_vote_score()
            },
            'message': 'Vote recorded successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error voting on question: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to record vote'
            }
        }), 500


@qa_bp.route('/answers/<int:answer_id>/vote', methods=['POST'])
@jwt_required()
def vote_answer(answer_id):
    """Vote on an answer"""
    try:
        user_id = get_jwt_identity()
        answer = Answer.query.get_or_404(answer_id)
        data = request.get_json()
        
        vote_type = data.get('vote_type')
        if vote_type not in ['Upvote', 'Downvote']:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid vote type'
                }
            }), 400
        
        # Check if user already voted
        existing_vote = AnswerVote.query.filter_by(
            answer_id=answer_id,
            user_id=user_id
        ).first()
        
        if existing_vote:
            # Update existing vote
            if existing_vote.vote_type == vote_type:
                # Remove vote
                db.session.delete(existing_vote)
                if vote_type == 'Upvote':
                    answer.upvote_count -= 1
                else:
                    answer.downvote_count -= 1
            else:
                # Change vote type
                existing_vote.vote_type = vote_type
                if vote_type == 'Upvote':
                    answer.upvote_count += 1
                    answer.downvote_count -= 1
                else:
                    answer.downvote_count += 1
                    answer.upvote_count -= 1
        else:
            # Create new vote
            vote = AnswerVote(
                answer_id=answer_id,
                user_id=user_id,
                vote_type=vote_type
            )
            db.session.add(vote)
            
            if vote_type == 'Upvote':
                answer.upvote_count += 1
            else:
                answer.downvote_count += 1
        
        answer.question.last_activity_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'upvote_count': answer.upvote_count,
                'downvote_count': answer.downvote_count,
                'vote_score': answer.get_vote_score()
            },
            'message': 'Vote recorded successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error voting on answer: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to record vote'
            }
        }), 500


# Follow endpoints

@qa_bp.route('/questions/<int:question_id>/follow', methods=['POST'])
@jwt_required()
def follow_question(question_id):
    """Follow a question"""
    try:
        user_id = get_jwt_identity()
        question = Question.query.get_or_404(question_id)
        data = request.get_json()
        
        # Check if already following
        existing_follow = QuestionFollow.query.filter_by(
            question_id=question_id,
            user_id=user_id
        ).first()
        
        if existing_follow:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ALREADY_FOLLOWING',
                    'message': 'You are already following this question'
                }
            }), 400
        
        # Create follow
        follow = QuestionFollow(
            question_id=question_id,
            user_id=user_id,
            notification_enabled=data.get('notification_enabled', True)
        )
        db.session.add(follow)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': follow.to_dict(),
            'message': 'Question followed successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error following question: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to follow question'
            }
        }), 500


@qa_bp.route('/questions/<int:question_id>/follow', methods=['DELETE'])
@jwt_required()
def unfollow_question(question_id):
    """Unfollow a question"""
    try:
        user_id = get_jwt_identity()
        
        follow = QuestionFollow.query.filter_by(
            question_id=question_id,
            user_id=user_id
        ).first_or_404()
        
        db.session.delete(follow)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Question unfollowed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error unfollowing question: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to unfollow question'
            }
        }), 500


# Tag endpoints

@qa_bp.route('/tags', methods=['GET'])
def get_tags():
    """Get popular tags"""
    try:
        tags = Tag.query.filter_by(is_active=True).order_by(Tag.question_count.desc()).limit(50).all()
        
        return jsonify({
            'success': True,
            'data': [tag.to_dict() for tag in tags]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting tags: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to retrieve tags'
            }
        }), 500


@qa_bp.route('/tags', methods=['POST'])
@jwt_required()
def create_tag():
    """Create a new tag"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('name'):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Tag name is required'
                }
            }), 400
        
        # Check if tag already exists
        existing_tag = Tag.query.filter_by(name=data['name']).first()
        if existing_tag:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TAG_EXISTS',
                    'message': 'Tag already exists'
                }
            }), 400
        
        # Create tag
        tag = Tag(
            name=data['name'],
            description=data.get('description'),
            color=data.get('color', '#007bff'),
            icon=data.get('icon')
        )
        
        db.session.add(tag)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': tag.to_dict(),
            'message': 'Tag created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating tag: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Failed to create tag'
            }
        }), 500