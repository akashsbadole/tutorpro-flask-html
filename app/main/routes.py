from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
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
        # Temporary redirect for admin dashboard
        flash('Admin dashboard is under development. Redirecting to home page.', 'info')
        return redirect(url_for('main.index'))
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


@bp.route('/profile')
@login_required
def profile():
    """
    User profile page
    """
    return render_template('main/profile.html', title='My Profile')