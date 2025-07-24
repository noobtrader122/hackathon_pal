"""
---------------------------------------------------------------------------------
 Author : Rayyan Mirza
---------------------------------------------------------------------------------
"""
# app.py - Main entry point
from factory import create_app
import os

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

# Create application
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(
        host=os.environ.get('FLASK_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=app.config['DEBUG']
    )
