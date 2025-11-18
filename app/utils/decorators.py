from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

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