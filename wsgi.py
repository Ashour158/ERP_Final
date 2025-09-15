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
        
        # Initialize database with Company and Admin user if available
        try:
            from init_db import init_database
            company, admin_user = init_database()
            if company:
                print(f"Initialized with company: {getattr(company, 'name', 'N/A')}")
            if admin_user:
                print(f"Admin user: {getattr(admin_user, 'username', 'N/A')}")
        except Exception as init_err:
            print(f"Database initialization warning: {str(init_err)}")
        
    except Exception as e:
        print(f"Database initialization warning: {str(e)}")
        # Continue anyway - the app might still work

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

