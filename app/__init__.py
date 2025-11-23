from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_mail import Mail
try:
    from flask_caching import Cache
except ImportError:
    # Fallback if flask_caching is not installed
    class Cache:
        def __init__(self):
            pass
        def init_app(self, app):
            pass
from config import config

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
mail = Mail()
cache = Cache()

def create_app(config_name='default'):
    """
    Application factory function that creates and configures the Flask app
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cache.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp)
    
    from app.tutor import bp as tutor_bp
    app.register_blueprint(tutor_bp)
    
    from app.student import bp as student_bp
    app.register_blueprint(student_bp)
    
    from app.course import bp as course_bp
    app.register_blueprint(course_bp)
    
    # Register meeting blueprint
    from app.meeting import bp as meeting_bp
    app.register_blueprint(meeting_bp)
    
    # Register demo blueprint
    from app.demo import bp as demo_bp
    app.register_blueprint(demo_bp)
    
    # Register API blueprints
    from app.api.tutor import tutor_api
    app.register_blueprint(tutor_api)
    
    from app.api.course import course_api
    app.register_blueprint(course_api)
    
    from app.api.meeting import meeting_api
    app.register_blueprint(meeting_api)
    
    # Register API payment blueprint
    from app.api.payment import payment_api
    app.register_blueprint(payment_api)
    
    # Register search API blueprint
    from app.api.search import search_bp
    app.register_blueprint(search_bp)
    
    # Register AI API blueprint
    from app.api.ai import ai_bp
    app.register_blueprint(ai_bp)
    
    # Register video classroom API blueprint
    from app.api.video_classroom import video_classroom_bp
    app.register_blueprint(video_classroom_bp)
    
    # Register messaging API blueprint
    from app.api.messaging import messaging_bp
    app.register_blueprint(messaging_bp)
    
    # Register payment blueprint
    from app.payment import bp as payment_bp
    app.register_blueprint(payment_bp)
    
    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500
    
    return app
