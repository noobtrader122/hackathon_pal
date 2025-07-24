"""
---------------------------------------------------------------------------------
 Author : Rayyan Mirza
---------------------------------------------------------------------------------
"""
# app.py - Main entry point
from . import create_app
import os

# Create application
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(
        host=os.environ.get('FLASK_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=app.config['DEBUG']
    )
