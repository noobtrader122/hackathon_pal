"""
------------------------------------------------------------------------------------
 Author : Rayyan Mirza
---------------------------------------------------------------------------------
"""

"""
Application configuration settings for SQL Hackathon Platform
"""

import os
from datetime import timedelta
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).parent.parent

class Config:
    """Base configuration class with common settings"""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Application settings
    APP_NAME = 'SQL Hackathon Platform'
    VERSION = '1.0.0'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    
    # JSON response settings
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Challenge-specific settings
    MAX_QUERY_RESULTS = 1000  # Maximum rows per query
    DEFAULT_CHALLENGE_TIME_LIMIT = 300  # 5 minutes in seconds
    MAX_EXECUTION_TIME = 30  # Maximum SQL execution time in seconds
    
    # Leaderboard settings
    LEADERBOARD_UPDATE_INTERVAL = 30  # seconds
    MAX_LEADERBOARD_ENTRIES = 100
    
    # Defog SQL-Eval settings
    ENABLE_SQL_EVAL = True
    SQL_EVAL_TIMEOUT = 10  # seconds
    
    # Email settings (for participant notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'logs' / 'app.log'
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration"""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.LOG_FILE.parent, exist_ok=True)

class DevelopmentConfig(Config):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f'sqlite:///{BASE_DIR}/data/hackathon_dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  # Log SQL queries in development
    
    # Challenge data source
    CHALLENGES_DATA_SOURCE = os.environ.get('CHALLENGES_DATA_SOURCE') or 'database'  # 'database' or 'json'
    CHALLENGES_JSON_FILE = BASE_DIR / 'data' / 'challenges_dev.json'
    
    # Development-specific settings
    DEFAULT_CHALLENGE_TIME_LIMIT = 600  # 10 minutes for development
    MAX_EXECUTION_TIME = 60  # More time for debugging
    
    # Disable CSRF for development ease
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR}/data/hackathon.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Challenge data source
    CHALLENGES_DATA_SOURCE = os.environ.get('CHALLENGES_DATA_SOURCE', 'database')
    CHALLENGES_JSON_FILE = BASE_DIR / 'data' / 'challenges.json'
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Production-specific settings
    MAX_QUERY_RESULTS = 500  # Stricter limit in production
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Set up file logging
        file_handler = RotatingFileHandler(
            Config.LOG_FILE, maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('SQL Hackathon Platform startup')

class TestingConfig(Config):
    """Testing environment configuration"""
    
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Challenge data source
    CHALLENGES_DATA_SOURCE = 'json'
    CHALLENGES_JSON_FILE = BASE_DIR / 'tests' / 'test_challenges.json'
    
    # Testing-specific settings
    WTF_CSRF_ENABLED = False
    MAX_EXECUTION_TIME = 5  # Quick tests
    LEADERBOARD_UPDATE_INTERVAL = 1  # Fast updates for testing
    
    # Disable mail sending in tests
    MAIL_SUPPRESS_SEND = True

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class by name"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, DevelopmentConfig)
