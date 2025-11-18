from flask import render_template, request
from app import create_app

app = create_app()

def page_not_found(e):
    """
    Custom 404 error handler
    """
    return render_template('errors/404.html'), 404

def internal_server_error(e):
    """
    Custom 500 error handler
    """
    return render_template('errors/500.html'), 500