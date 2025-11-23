"""
Seed data for email templates
"""
from datetime import datetime
from app.models.email_notification import EmailTemplate

def create_email_templates():
    """Create default email templates"""
    
    templates = [
        {
            'name': 'Booking Confirmation',
            'description': 'Template for booking confirmation emails',
            'template_type': 'Booking Confirmation',
            'subject_template': 'Booking Confirmed - {{session_title}} with {{tutor_name}}',
            'body_template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2C3E50;">Booking Confirmed!</h2>
                <p>Dear {{student_name}},</p>
                <p>Your booking has been confirmed with the following details:</p>
                <div style="background-color: #F8F9FA; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>{{session_title}}</h3>
                    <p><strong>Date:</strong> {{booking_date}}</p>
                    <p><strong>Time:</strong> {{booking_time}}</p>
                    <p><strong>Duration:</strong> {{duration}}</p>
                    <p><strong>Tutor:</strong> {{tutor_name}}</p>
                    <p><strong>Location:</strong> {{location}}</p>
                </div>
                <p>Please arrive 5 minutes before the scheduled time. If you need to reschedule, you can do so from your dashboard.</p>
                <p>Best regards,<br>The TutorPro Team</p>
            </div>
            ''',
            'text_template': '''
            Booking Confirmed!
            
            Dear {{student_name}},
            
            Your booking has been confirmed with the following details:
            
            {{session_title}}
            Date: {{booking_date}}
            Time: {{booking_time}}
            Duration: {{duration}}
            Tutor: {{tutor_name}}
            Location: {{location}}
            
            Please arrive 5 minutes before the scheduled time. If you need to reschedule, you can do so from your dashboard.
            
            Best regards,
            The TutorPro Team
            ''',
            'header_style': 'Professional',
            'footer_style': 'Professional',
            'is_default': True,
            'is_active': True
        },
        {
            'name': 'Booking Reminder',
            'description': 'Template for booking reminder emails',
            'template_type': 'Booking Reminder',
            'subject_template': 'Reminder: {{session_title}} tomorrow at {{booking_time}}',
            'body_template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #E67E22;">Booking Reminder</h2>
                <p>Hi {{student_name}},</p>
                <p>This is a friendly reminder about your upcoming session:</p>
                <div style="background-color: #FFF3E0; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>{{session_title}}</h3>
                    <p><strong>Tomorrow:</strong> {{booking_date}}</p>
                    <p><strong>Time:</strong> {{booking_time}}</p>
                    <p><strong>Duration:</strong> {{duration}}</p>
                    <p><strong>Tutor:</strong> {{tutor_name}}</p>
                    <p><strong>Location:</strong> {{location}}</p>
                </div>
                <p>Please make sure you're prepared for the session. If you need to cancel or reschedule, please do so at least 2 hours in advance.</p>
                <p>See you soon!<br>The TutorPro Team</p>
            </div>
            ''',
            'header_style': 'Friendly',
            'footer_style': 'Friendly',
            'is_default': True,
            'is_active': True
        },
        {
            'name': 'Payment Confirmation',
            'description': 'Template for payment confirmation emails',
            'template_type': 'Payment Confirmation',
            'subject_template': 'Payment Confirmation - Order #{{order_id}}',
            'body_template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #27AE60;">Payment Confirmed</h2>
                <p>Dear {{customer_name}},</p>
                <p>Your payment has been successfully processed. Here are the details:</p>
                <div style="background-color: #E8F8F5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Order #{{order_id}}</h3>
                    <p><strong>Amount:</strong> ${{amount}}</p>
                    <p><strong>Payment Method:</strong> {{payment_method}}</p>
                    <p><strong>Date:</strong> {{payment_date}}</p>
                    <p><strong>Description:</strong> {{description}}</p>
                </div>
                <p>A receipt has been generated and can be downloaded from your account dashboard.</p>
                <p>Thank you for your payment!<br>The TutorPro Team</p>
            </div>
            ''',
            'header_style': 'Professional',
            'footer_style': 'Professional',
            'is_default': True,
            'is_active': True
        },
        {
            'name': 'Course Enrollment',
            'description': 'Template for course enrollment confirmation',
            'template_type': 'Course Enrollment',
            'subject_template': 'Welcome to {{course_name}}!',
            'body_template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #3498DB;">Welcome to {{course_name}}!</h2>
                <p>Hi {{student_name}},</p>
                <p>Congratulations on enrolling in {{course_name}}! We're excited to have you join us.</p>
                <div style="background-color: #EBF5FB; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Course Details</h3>
                    <p><strong>Course:</strong> {{course_name}}</p>
                    <p><strong>Instructor:</strong> {{instructor_name}}</p>
                    <p><strong>Duration:</strong> {{course_duration}}</p>
                    <p><strong>Start Date:</strong> {{start_date}}</p>
                    <p><strong>Enrollment Date:</strong> {{enrollment_date}}</p>
                </div>
                <p>You can now access the course materials from your dashboard. Get started by watching the introduction video and reviewing the course syllabus.</p>
                <p>If you have any questions, don't hesitate to reach out to your instructor.</p>
                <p>Happy learning!<br>The TutorPro Team</p>
            </div>
            ''',
            'header_style': 'Modern',
            'footer_style': 'Modern',
            'is_default': True,
            'is_active': True
        },
        {
            'name': 'Review Request',
            'description': 'Template for requesting reviews after course completion',
            'template_type': 'Review Request',
            'subject_template': 'How was your experience with {{tutor_name}}?',
            'body_template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #9B59B6;">Share Your Experience</h2>
                <p>Hi {{student_name}},</p>
                <p>We hope you had a great learning experience with {{tutor_name}}! Your feedback helps us improve and helps other students make informed decisions.</p>
                <div style="background-color: #F4ECF7; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Course: {{course_name}}</h3>
                    <p><strong>Tutor:</strong> {{tutor_name}}</p>
                    <p><strong>Completion Date:</strong> {{completion_date}}</p>
                </div>
                <p>Please take a moment to share your experience by leaving a review:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{review_link}}" style="background-color: #9B59B6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Leave a Review</a>
                </div>
                <p>Your feedback is valuable to us and the TutorPro community.</p>
                <p>Thank you!<br>The TutorPro Team</p>
            </div>
            ''',
            'header_style': 'Friendly',
            'footer_style': 'Friendly',
            'is_default': True,
            'is_active': True
        },
        {
            'name': 'Security Alert',
            'description': 'Template for security alert notifications',
            'template_type': 'Security Alert',
            'subject_template': 'Security Alert: {{alert_type}}',
            'body_template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #E74C3C;">Security Alert</h2>
                <p>Hi {{user_name}},</p>
                <p>We detected a {{alert_type}} on your account:</p>
                <div style="background-color: #FADBD8; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>{{alert_title}}</h3>
                    <p><strong>Date:</strong> {{alert_date}}</p>
                    <p><strong>Time:</strong> {{alert_time}}</p>
                    <p><strong>IP Address:</strong> {{ip_address}}</p>
                    <p><strong>Location:</strong> {{location}}</p>
                    <p><strong>Device:</strong> {{device_info}}</p>
                </div>
                <p>If this was you, you can safely ignore this message. If you don't recognize this activity, please:</p>
                <ol>
                    <li>Change your password immediately</li>
                    <li>Enable two-factor authentication</li>
                    <li>Review your account activity</li>
                </ol>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{security_link}}" style="background-color: #E74C3C; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Secure Your Account</a>
                </div>
                <p>Stay safe!<br>The TutorPro Security Team</p>
            </div>
            ''',
            'header_style': 'Professional',
            'footer_style': 'Professional',
            'is_default': True,
            'is_active': True
        }
    ]
    
    created_templates = []
    for template_data in templates:
        template = EmailTemplate(
            **template_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        created_templates.append(template)
    
    return created_templates

if __name__ == '__main__':
    from app import create_app, db
    
    app = create_app()
    with app.app_context():
        # Check if templates already exist
        existing_count = EmailTemplate.query.count()
        if existing_count == 0:
            templates = create_email_templates()
            for template in templates:
                db.session.add(template)
            db.session.commit()
            print(f"Created {len(templates)} email templates")
        else:
            print(f"Email templates already exist ({existing_count} found)")