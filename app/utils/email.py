"""
Email utilities for TutorPro Marketplace
Basic email sending functionality
"""

from flask import current_app, render_template
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

def send_email(to: str, subject: str, template: Optional[str] = None, 
               template_data: Optional[Dict] = None, html_body: Optional[str] = None,
               text_body: Optional[str] = None) -> bool:
    """
    Send an email using the configured email service
    
    Args:
        to: Recipient email address
        subject: Email subject
        template: Template file to use (optional)
        template_data: Data for template rendering (optional)
        html_body: HTML body content (optional)
        text_body: Plain text body content (optional)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # This is a placeholder implementation
        # In production, you would integrate with a real email service like SendGrid, SES, etc.
        
        if template:
            html_body = render_template(template, **(template_data or {}))
        
        if not html_body and not text_body:
            logger.error("No email content provided")
            return False
        
        # Log email for debugging (in production, use actual email service)
        logger.info(f"Email to: {to}")
        logger.info(f"Subject: {subject}")
        logger.info(f"HTML body: {html_body[:200] if html_body else 'None'}...")
        logger.info(f"Text body: {text_body[:200] if text_body else 'None'}...")
        
        # Placeholder for actual email sending
        # In production, you would use something like:
        # from flask_mail import Message
        # from app import mail
        # msg = Message(subject, recipients=[to], html=html_body, body=text_body)
        # mail.send(msg)
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def send_password_reset_email(user_email: str, reset_token: str) -> bool:
    """Send password reset email"""
    try:
        reset_url = f"{current_app.config.get('FRONTEND_URL', '')}/reset-password?token={reset_token}"
        return send_email(
            to=user_email,
            subject="Password Reset Request",
            template="auth/password_reset_email.html",
            template_data={'reset_url': reset_url}
        )
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        return False

def send_verification_email(user_email: str, verification_token: str) -> bool:
    """Send email verification email"""
    try:
        verification_url = f"{current_app.config.get('FRONTEND_URL', '')}/verify-email?token={verification_token}"
        return send_email(
            to=user_email,
            subject="Verify Your Email Address",
            template="auth/email_verification.html",
            template_data={'verification_url': verification_url}
        )
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
        return False