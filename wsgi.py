#!/usr/bin/env python3
"""
WSGI Entry Point for Complete ERP System
For Digital Ocean App Platform deployment
"""

import os
from app import app, db

# Set production environment if not specified
os.environ.setdefault('FLASK_ENV', 'production')

# Create database tables and initialize if needed
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")
        
        # Initialize database with Company and Admin user if needed
        from init_db import init_database
        company, admin_user = init_database()
        
        if company and admin_user:
            print(f"Initialized with company: {company.name}")
            print(f"Admin user: {admin_user.username}")
        
    except Exception as e:
        print(f"Database initialization warning: {str(e)}")
        # Continue anyway - the app might still work

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

