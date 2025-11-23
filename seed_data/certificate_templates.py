"""
Seed data for certificate templates
"""
from datetime import datetime
from app.models.certificate import CertificateTemplate

def create_certificate_templates():
    """Create default certificate templates"""
    
    templates = [
        {
            'name': 'Course Completion Standard',
            'description': 'Standard template for course completion certificates',
            'template_type': 'Course Completion',
            'background_color': '#FFFFFF',
            'text_color': '#000000',
            'accent_color': '#FFD700',
            'layout_style': 'Traditional',
            'header_text': 'Certificate of Completion',
            'body_template': 'This is to certify that <strong>{{recipient_name}}</strong> has successfully completed the course <strong>{{course_name}}</strong> with a grade of <strong>{{grade}}</strong>.',
            'footer_text': 'Awarded on {{completion_date}}',
            'is_default': True,
            'is_active': True,
            'font_family': 'Georgia',
            'font_size': 16
        },
        {
            'name': 'Achievement Excellence',
            'description': 'Template for outstanding achievement certificates',
            'template_type': 'Achievement',
            'background_color': '#F8F8F8',
            'text_color': '#2C3E50',
            'accent_color': '#E74C3C',
            'layout_style': 'Modern',
            'header_text': 'Certificate of Achievement',
            'body_template': 'This certificate is proudly awarded to <strong>{{recipient_name}}</strong> in recognition of outstanding achievement in <strong>{{course_name}}</strong>.',
            'footer_text': 'Presented on {{completion_date}}',
            'is_default': False,
            'is_active': True,
            'font_family': 'Arial',
            'font_size': 14
        },
        {
            'name': 'Excellence Award',
            'description': 'Premium template for excellence awards',
            'template_type': 'Excellence',
            'background_color': '#1A1A1A',
            'text_color': '#FFFFFF',
            'accent_color': '#FFD700',
            'layout_style': 'Creative',
            'header_text': 'Certificate of Excellence',
            'body_template': 'In recognition of exceptional performance and dedication, this certificate is awarded to <strong>{{recipient_name}}</strong> for excellence in <strong>{{course_name}}</strong>.',
            'footer_text': 'Awarded with distinction on {{completion_date}}',
            'is_default': False,
            'is_active': True,
            'font_family': 'Times New Roman',
            'font_size': 18
        },
        {
            'name': 'Participation Certificate',
            'description': 'Simple template for participation certificates',
            'template_type': 'Participation',
            'background_color': '#F5F5F5',
            'text_color': '#333333',
            'accent_color': '#3498DB',
            'layout_style': 'Minimal',
            'header_text': 'Certificate of Participation',
            'body_template': 'This certificate acknowledges that <strong>{{recipient_name}}</strong> has participated in <strong>{{course_name}}</strong>.',
            'footer_text': 'Issued on {{completion_date}}',
            'is_default': False,
            'is_active': True,
            'font_family': 'Helvetica',
            'font_size': 14
        },
        {
            'name': 'Custom Professional',
            'description': 'Customizable professional template',
            'template_type': 'Custom',
            'background_color': '#FFFFFF',
            'text_color': '#2C3E50',
            'accent_color': '#34495E',
            'layout_style': 'Professional',
            'header_text': 'Professional Certificate',
            'body_template': 'This certifies that <strong>{{recipient_name}}</strong> has successfully completed the requirements for <strong>{{course_name}}</strong>.',
            'footer_text': 'Verified on {{completion_date}}',
            'is_default': False,
            'is_active': True,
            'font_family': 'Calibri',
            'font_size': 15
        }
    ]
    
    created_templates = []
    for template_data in templates:
        template = CertificateTemplate(
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
        existing_count = CertificateTemplate.query.count()
        if existing_count == 0:
            templates = create_certificate_templates()
            for template in templates:
                db.session.add(template)
            db.session.commit()
            print(f"Created {len(templates)} certificate templates")
        else:
            print(f"Certificate templates already exist ({existing_count} found)")