#!/usr/bin/env python3
"""
WSGI Entry Point for Complete ERP System
For Digital Ocean App Platform deployment
"""

import os
from app import app, db

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

