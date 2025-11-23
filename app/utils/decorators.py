from functools import wraps
from flask import flash, redirect, url_for, abort, jsonify, g, request
from flask_login import current_user
from time import time
import collections

def rate_limit(limit=100, period=3600):
    """
    Rate limiting decorator for API endpoints
    Usage: @rate_limit(limit=100, period=3600)  # 100 requests per hour
    """
    def decorator(f):
        # Simple in-memory rate limiter
        # In production, use Redis or other distributed cache
        if not hasattr(rate_limit, 'requests'):
            rate_limit.requests = collections.defaultdict(list)
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier (IP address or user ID)
            if current_user.is_authenticated:
                key = f"user:{current_user.id}"
            else:
                key = f"ip:{request.remote_addr}"
            
            now = time()
            # Remove old requests outside the period
            rate_limit.requests[key] = [
                req_time for req_time in rate_limit.requests[key]
                if now - req_time < period
            ]
            
            # Check if limit exceeded
            if len(rate_limit.requests[key]) >= limit:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {limit} per {period} seconds.'
                }), 429
            
            # Add current request
            rate_limit.requests[key].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorator to require admin role for access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def tutor_required(f):
    """
    Decorator to require tutor role for access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_tutor():
            flash('You need tutor privileges to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def learner_required(f):
    """
    Decorator to require learner role for access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_learner():
            flash('You need learner privileges to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def roles_required(*roles):
    """
    Decorator to require specific roles for access
    Usage: @roles_required('Admin', 'Tutor')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('You need to be logged in to access this page.', 'danger')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('You do not have the required privileges to access this page.', 'danger')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def roles_except(*roles):
    """
    Decorator to deny access to specific roles
    Usage: @roles_except('Learner')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('You need to be logged in to access this page.', 'danger')
                return redirect(url_for('auth.login'))
            
            if current_user.role in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(role):
    """
    Decorator to require a specific role for access
    Usage: @role_required('Admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('You need to be logged in to access this page.', 'danger')
                return redirect(url_for('auth.login'))
            
            if current_user.role != role:
                flash('You do not have required privileges to access this page.', 'danger')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator