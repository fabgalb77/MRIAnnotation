import os
from flask import Flask, session
from app.config import Config
from datetime import datetime

def create_app(config_class=Config):
    """Application factory pattern for Flask app"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    
    # Try to load the instance config if it exists
    try:
        app.config.from_pyfile('config.py')
    except FileNotFoundError:
        pass
    
    # Ensure the secret key is set
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
        
    # Ensure session is permanent for persistence
    @app.before_request
    def make_session_permanent():
        session.permanent = True
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Register template filters
    from app.utils.template_filters import format_date
    app.jinja_env.filters['format_date'] = format_date
    
    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.now
        }
    
    return app
