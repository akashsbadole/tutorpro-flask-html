from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.main import bp
from app.utils.decorators import roles_required, admin_required, tutor_required, learner_required

@bp.route('/')
def index():
    """
    Home page
    """
    return render_template('main/index.html', title='Home')


@bp.route('/dashboard')
@login_required
def dashboard():
    """
    User dashboard based on role
    """
    if current_user.is_admin():
        # Redirect to actual admin dashboard
        return redirect(url_for('admin.dashboard'))
    elif current_user.is_tutor():
        # Temporary redirect for tutor dashboard
        flash('Tutor dashboard is under development. Redirecting to home page.', 'info')
        return redirect(url_for('main.index'))
    elif current_user.is_learner():
        # Temporary redirect for learner dashboard
        flash('Learner dashboard is under development. Redirecting to home page.', 'info')
        return redirect(url_for('main.index'))
    else:
        flash('Invalid user role. Please contact support.', 'warning')
        return redirect(url_for('main.index'))


@bp.route('/about')
def about():
    """
    About page
    """
    return render_template('main/about.html', title='About Us')


@bp.route('/contact')
def contact():
    """
    Contact page
    """
    return render_template('main/contact.html', title='Contact Us')


@bp.route('/search')
def search():
    """
    Search functionality
    """
    query = request.args.get('q', '')
    if not query:
        flash('Please enter a search term', 'warning')
        return redirect(url_for('main.index'))
    
    # TODO: Implement search functionality
    return render_template('main/search.html', title='Search', query=query)


@bp.route('/privacy')
def privacy():
    """
    Privacy policy page
    """
    return render_template('main/privacy.html', title='Privacy Policy')


@bp.route('/terms')
def terms():
    """
    Terms of service page
    """
    return render_template('main/terms.html', title='Terms of Service')


@bp.route('/help')
def help():
    """
    Help page
    """
    return render_template('main/help.html', title='Help Center')


@bp.route('/courses')
def courses():
    """
    Courses page - displays available courses
    """
    # For now, redirect to admin courses since that's where the courses functionality is
    # In a full implementation, this would show a public view of courses
    return redirect(url_for('admin.courses'))


@bp.route('/tutors')
def tutors():
    """
    Legacy tutors page - redirects to new tutor discovery
    """
    return redirect(url_for('main.tutor_discovery'))


@bp.route('/discover')
def tutor_discovery():
    """
    Advanced tutor discovery page with search and filtering
    """
    return render_template('main/tutor_discovery.html', title='Find Tutors - TutorPro Marketplace')


@bp.route('/profile')
@login_required
def profile():
    """
    User profile page
    """
    return render_template('main/profile.html', title='My Profile')


@bp.route('/offline')
def offline():
    """
    Offline page for PWA functionality
    """
    return render_template('offline.html', title='Offline - TutorPro')


@bp.route('/api/health')
def health_check():
    """
    Health check endpoint for PWA connectivity testing
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'TutorPro PWA'
    }), 200