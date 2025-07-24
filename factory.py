"""
SQL Hackathon Platform - Main Application Package
"""

import os
from flask import Flask , render_template
from models.sqlalchemy_models import db
from flask_migrate import Migrate

# --- Auto-load env vars before config, for Flask and tools ---
try:
    from dotenv import load_dotenv
    dotenv_path = None
    if os.path.exists(os.path.join(os.path.dirname(__file__), '.env')):
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    elif os.path.exists(os.path.join(os.path.dirname(__file__), '.development.env')):
        dotenv_path = os.path.join(os.path.dirname(__file__), '.development.env')
    if dotenv_path:
        load_dotenv(dotenv_path)
        print(f"[INFO] Loaded environment from: {dotenv_path}")
except ImportError:
    pass  # python-dotenv not installed, ignore

# Initialize extensions
migrate = Migrate()

def create_app(config_name=None):
    """Application factory function"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)

    # Load configuration object
    from config import get_config 
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    print(f'config_class: {config_class.SQLALCHEMY_DATABASE_URI}')
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    config_class.init_app(app)

    # Register blueprints
    from routes import challenge_bp, submission_bp, leaderboard_bp, admin_bp, admin_hackathon_bp
    
    
    app.register_blueprint(challenge_bp, url_prefix='/challenges')
    app.register_blueprint(submission_bp, url_prefix='/submit')
    app.register_blueprint(leaderboard_bp, url_prefix='/leaderboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(admin_hackathon_bp, url_prefix='/admin/hackathon')

    # Register main routes
    @app.route('/')
    def index():
        return render_template('index.html')


    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'version': app.config['VERSION']}

    # Create database tables (for early dev/testing)
    with app.app_context():
        db.create_all()
    return app

__version__ = '1.0.0'
__all__ = ['create_app', 'db', 'migrate']
