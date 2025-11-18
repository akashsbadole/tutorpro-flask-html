from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
import os
import uuid
from datetime import datetime
from sqlalchemy import or_
from app.tutor import bp
from app.utils.decorators import tutor_required
from app.models.user import User, UserProfile
from app.models.tutor import TutorProfile
from app.models.course import Subject, Course, TutorSubject
from app.models.booking import Booking, TutorAvailability
from app.tutor.forms import ProfileForm, AvailabilityForm, BulkAvailabilityForm
from app import db
from app.utils.errors import ValidationError
import csv
import io


@bp.route('/profile')
@login_required
@tutor_required
def profile():
    """View and edit tutor profile"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        # Create tutor profile if it doesn't exist
        tutor_profile = TutorProfile(user_id=current_user.id)
        db.session.add(tutor_profile)
        db.session.commit()
    
    # Get user profile
    user_profile = current_user.user_profile
    if not user_profile:
        user_profile = UserProfile(user_id=current_user.id)
        db.session.add(user_profile)
        db.session.commit()
    
    # Get subjects for selection
    subjects = Subject.query.all()
    
    return render_template('tutor/profile.html', 
                          tutor_profile=tutor_profile,
                          user_profile=user_profile,
                          subjects=subjects)


@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@tutor_required
def edit_profile():
    """Edit tutor profile"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        # Create tutor profile if it doesn't exist
        tutor_profile = TutorProfile(user_id=current_user.id)
        db.session.add(tutor_profile)
        db.session.commit()
    
    # Get user profile
    user_profile = current_user.user_profile
    if not user_profile:
        user_profile = UserProfile(user_id=current_user.id)
        db.session.add(user_profile)
        db.session.commit()
    
    # Get subjects for selection
    subjects = Subject.query.all()
    
    form = ProfileForm(obj=tutor_profile)
    if user_profile:
        form.first_name.data = user_profile.first_name or ''
        form.last_name.data = user_profile.last_name or ''
        form.phone.data = user_profile.phone or ''
        form.timezone.data = user_profile.timezone or 'UTC'
    
    # Populate subjects field with current subjects
    current_subjects = [ts.subject_id for ts in tutor_profile.subjects]
    form.subjects.choices = [(s.id, s.name) for s in subjects]
    
    if form.validate_on_submit():
        # Update user profile
        user_profile.first_name = form.first_name.data
        user_profile.last_name = form.last_name.data
        user_profile.phone = form.phone.data
        user_profile.timezone = form.timezone.data
        
        # Update tutor profile
        tutor_profile.title = form.title.data
        tutor_profile.description = form.bio.data
        tutor_profile.hourly_rate = form.hourly_rate.data
        tutor_profile.currency = form.currency.data
        tutor_profile.video_intro_url = form.video_intro_url.data
        
        # Update payment information
        tutor_profile.upi_id = form.upi_id.data
        tutor_profile.preferred_payment_method = form.preferred_payment_method.data
        tutor_profile.bank_account_name = form.bank_account_name.data
        tutor_profile.bank_account_number = form.bank_account_number.data
        tutor_profile.bank_ifsc_code = form.bank_ifsc_code.data
        
        # Handle profile picture upload
        if form.profile_picture.data:
            # Delete old picture if exists
            if user_profile.avatar_url:
                try:
                    old_filename = os.path.basename(user_profile.avatar_url)
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', old_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except Exception as e:
                    current_app.logger.error(f"Error deleting old avatar: {str(e)}")
            
            # Save new picture
            file = form.profile_picture.data
            filename = secure_filename(file.filename)
            if filename:
                # Generate unique filename
                file_ext = filename.rsplit('.', 1)[1].lower()
                new_filename = f"{uuid.uuid4().hex}.{file_ext}"
                
                # Create directory if it doesn't exist
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save file
                file_path = os.path.join(upload_dir, new_filename)
                file.save(file_path)
                
                # Resize image
                try:
                    img = Image.open(file_path)
                    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    img.save(file_path)
                except Exception as e:
                    current_app.logger.error(f"Error resizing image: {str(e)}")
                
                # Update avatar URL
                user_profile.avatar_url = url_for('static', f'uploads/avatars/{new_filename}')
        
        # Handle additional information
        user_profile.bio = form.expertise.data
        tutor_profile.education = form.education.data
        tutor_profile.experience = form.experience.data
        user_profile.languages = form.languages.data
        user_profile.timezone = form.timezone.data
        
        # Update subjects
        selected_subjects = form.subjects.data
        # Remove existing subjects that are not selected
        for ts in tutor_profile.subjects:
            if ts.subject_id not in selected_subjects:
                db.session.delete(ts)
        
        # Add new subjects
        for subject_id in selected_subjects:
            if not any(ts.subject_id == subject_id for ts in tutor_profile.subjects):
                ts = TutorSubject(
                    tutor_id=tutor_profile.id,
                    subject_id=subject_id,
                    proficiency_level=form.proficiency_level.data
                )
                db.session.add(ts)
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('tutor.profile'))
    
    return render_template('tutor/edit_profile.html', 
                          form=form,
                          tutor_profile=tutor_profile,
                          user_profile=user_profile,
                          subjects=subjects)


@bp.route('/profile/upload-picture', methods=['POST'])
@login_required
@tutor_required
def upload_profile_picture():
    """Upload profile picture via AJAX"""
    if 'profile_picture' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['profile_picture']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        try:
            # Get user profile
            user_profile = current_user.user_profile
            if not user_profile:
                user_profile = UserProfile(user_id=current_user.id)
                db.session.add(user_profile)
                db.session.commit()
            
            # Delete old picture if exists
            if user_profile.avatar_url:
                try:
                    old_filename = os.path.basename(user_profile.avatar_url)
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', old_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except Exception as e:
                    current_app.logger.error(f"Error deleting old avatar: {str(e)}")
            
            # Save new picture
            filename = secure_filename(file.filename)
            if filename:
                # Generate unique filename
                file_ext = filename.rsplit('.', 1)[1].lower()
                new_filename = f"{uuid.uuid4().hex}.{file_ext}"
                
                # Create directory if it doesn't exist
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save file
                file_path = os.path.join(upload_dir, new_filename)
                file.save(file_path)
                
                # Resize image
                try:
                    img = Image.open(file_path)
                    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    img.save(file_path)
                except Exception as e:
                    current_app.logger.error(f"Error resizing image: {str(e)}")
                
                # Update avatar URL
                user_profile.avatar_url = url_for('static', f'uploads/avatars/{new_filename}')
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'avatar_url': user_profile.avatar_url
                })
            
        except Exception as e:
            current_app.logger.error(f"Error uploading profile picture: {str(e)}")
            return jsonify({'error': 'Error uploading file'}), 500
    
    return jsonify({'error': 'Error uploading file'}), 500


@bp.route('/profile/availability')
@login_required
@tutor_required
def availability():
    """Manage tutor availability"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    # Get availability
    availabilities = TutorAvailability.query.filter_by(tutor_id=tutor_profile.id).all()
    
    # Get bookings for the next 7 days
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=7)
    
    bookings = Booking.query.filter(
        Booking.tutor_id == tutor_profile.id,
        Booking.scheduled_time >= start_date,
        Booking.scheduled_time <= end_date
    ).order_by(Booking.scheduled_time.asc()).all()
    
    return render_template('tutor/availability.html', 
                           availabilities=availabilities,
                           bookings=bookings,
                           start_date=start_date,
                           end_date=end_date)


@bp.route('/profile/availability/update', methods=['POST'])
@login_required
@tutor_required
def update_availability():
    """Update tutor availability"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    form = AvailabilityForm()
    
    if form.validate_on_submit():
        # Check if availability already exists
        availability = TutorAvailability.query.filter_by(
            tutor_id=tutor_profile.id,
            day_of_week=form.day_of_week.data
        ).first()
        
        if availability:
            # Update existing availability
            availability.start_time = form.start_time.data
            availability.end_time = form.end_time.data
            availability.is_available = form.is_available.data
        else:
            # Create new availability
            availability = TutorAvailability(
                tutor_id=tutor_profile.id,
                day_of_week=form.day_of_week.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                is_available=form.is_available.data
            )
            db.session.add(availability)
        
        db.session.commit()
        flash('Availability updated successfully', 'success')
        return redirect(url_for('tutor.availability'))
    
    return render_template('tutor/availability.html', 
                           form=form,
                           error=True)


@bp.route('/profile/availability/bulk-import', methods=['POST'])
@login_required
@tutor_required
def bulk_import_availability():
    """Import availability from CSV"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    form = BulkAvailabilityForm()
    
    if form.validate_on_submit():
        csv_file = form.csv_file.data
        if csv_file:
            try:
                # Read CSV file
                stream = io.StringIO(csv_file.stream.read().decode('utf-8'))
                csv_reader = csv.DictReader(stream)
                
                # Process each row
                for row in csv_reader:
                    day_of_week = int(row.get('day_of_week', 0))
                    start_time = datetime.strptime(row.get('start_time', '00:00'), '%H:%M').time()
                    end_time = datetime.strptime(row.get('end_time', '00:00'), '%H:%M').time()
                    is_available = row.get('is_available', 'true').lower() == 'true'
                    
                    # Check if availability already exists
                    availability = TutorAvailability.query.filter_by(
                        tutor_id=tutor_profile.id,
                        day_of_week=day_of_week
                    ).first()
                    
                    if availability:
                        # Update existing availability
                        availability.start_time = start_time
                        availability.end_time = end_time
                        availability.is_available = is_available
                    else:
                        # Create new availability
                        availability = TutorAvailability(
                            tutor_id=tutor_profile.id,
                            day_of_week=day_of_week,
                            start_time=start_time,
                            end_time=end_time,
                            is_available=is_available
                        )
                        db.session.add(availability)
                
                db.session.commit()
                return jsonify({'success': True, 'message': 'Availability imported successfully'})
            
            except Exception as e:
                current_app.logger.error(f"Error importing availability: {str(e)}")
                return jsonify({'error': 'Error importing availability'}), 500
    
    return jsonify({'error': 'Invalid form data'}), 400


@bp.route('/profile/availability/bulk-export')
@login_required
@tutor_required
def bulk_export_availability():
    """Export availability to CSV"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        return jsonify({'error': 'Tutor profile not found'}), 404
    
    # Get availability
    availabilities = TutorAvailability.query.filter_by(tutor_id=tutor_profile.id).all()
    
    # Create CSV content
    output = io.StringIO()
    fieldnames = ['day_of_week', 'day_name', 'start_time', 'end_time', 'is_available']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    # Write header
    writer.writeheader()
    
    # Write data
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for availability in availabilities:
        writer.writerow({
            'day_of_week': availability.day_of_week,
            'day_name': day_names[availability.day_of_week],
            'start_time': availability.start_time.strftime('%H:%M'),
            'end_time': availability.end_time.strftime('%H:%M'),
            'is_available': availability.is_available
        })
    
    # Create response
    output.seek(0)
    response = current_app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=availability.csv'}
    )
    
    return response


@bp.route('/profile/availability/delete/<int:availability_id>', methods=['POST'])
@login_required
@tutor_required
def delete_availability(availability_id):
    """Delete tutor availability"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    availability = TutorAvailability.query.get_or_404(availability_id)
    
    if availability.tutor_id != tutor_profile.id:
        flash('You do not have permission to delete this availability', 'danger')
        return redirect(url_for('tutor.availability'))
    
    db.session.delete(availability)
    db.session.commit()
    flash('Availability deleted successfully', 'success')
    
    return redirect(url_for('tutor.availability'))


@bp.route('/profile/preview')
@login_required
@tutor_required
def profile_preview():
    """Preview tutor profile as students would see it"""
    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash('Please complete your tutor profile first', 'warning')
        return redirect(url_for('tutor.profile'))
    
    # Get user profile
    user_profile = current_user.user_profile
    
    # Get subjects
    subjects = tutor_profile.subjects
    
    # Get upcoming bookings
    upcoming_bookings = Booking.query.filter(
        Booking.tutor_id == tutor_profile.id,
        Booking.scheduled_time > datetime.utcnow(),
        Booking.status == 'Confirmed'
    ).order_by(Booking.scheduled_time.asc()).limit(5).all()
    
    return render_template('tutor/profile_preview.html', 
                          tutor_profile=tutor_profile,
                          user_profile=user_profile,
                          subjects=subjects,
                          upcoming_bookings=upcoming_bookings)