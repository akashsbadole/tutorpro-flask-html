from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from app.models.user import User, UserProfile
from datetime import datetime

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            user.update_last_login()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            
            flash(f'Welcome back, {user.email}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('auth/login.html', title='Sign In', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user
        user = User(
            email=form.email.data,
            password=form.password.data,
            role=form.role.data
        )
        
        # Create user profile
        profile = UserProfile(
            user=user,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        
        db.session.add(user)
        db.session.add(profile)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Create Account', form=form)


@bp.route('/logout')
@login_required
def logout():
    """
    Handle user logout
    """
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Handle password change
    """
    form = ChangePasswordForm(current_user)
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Your password has been changed successfully.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/change_password.html', title='Change Password', form=form)


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Handle forgot password request
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # TODO: Implement password reset email functionality
            flash('If your email is registered, you will receive a password reset link shortly.', 'info')
        else:
            flash('If your email is registered, you will receive a password reset link shortly.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', title='Forgot Password', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Handle password reset with token
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # TODO: Implement token verification
    flash('Password reset functionality is not yet implemented.', 'warning')
    return redirect(url_for('auth.login'))