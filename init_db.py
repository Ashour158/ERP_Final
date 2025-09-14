#!/usr/bin/env python3
"""
Database initialization script for ERP System
Creates initial Company and Admin user with proper constraints
"""

import os
import sys
from werkzeug.security import generate_password_hash
from datetime import datetime

# Add the current directory to the path so we can import our app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Initialize database with Company and Admin user"""
    try:
        from app import app, db, Company, User
        
        with app.app_context():
            print("Creating database tables...")
            db.create_all()
            
            # Check if Company already exists
            existing_company = Company.query.first()
            if existing_company:
                print(f"Company already exists: {existing_company.name}")
                return existing_company, None
            
            # Create default company
            company_name = os.environ.get('DEFAULT_COMPANY_NAME', 'Default Company')
            company_code = os.environ.get('DEFAULT_COMPANY_CODE', 'DEFAULT')
            
            company = Company(
                name=company_name,
                code=company_code,
                domain=os.environ.get('DEFAULT_COMPANY_DOMAIN'),
                email=os.environ.get('DEFAULT_COMPANY_EMAIL', 'admin@company.com'),
                phone=os.environ.get('DEFAULT_COMPANY_PHONE'),
                address=os.environ.get('DEFAULT_COMPANY_ADDRESS', 'Default Address'),
                industry=os.environ.get('DEFAULT_COMPANY_INDUSTRY', 'Technology'),
                subscription_plan='enterprise',
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.session.add(company)
            db.session.flush()  # Get company ID without committing
            
            print(f"Created company: {company.name} ({company.code})")
            
            # Check if admin user already exists
            existing_admin = User.query.filter_by(
                company_id=company.id, 
                role='admin'
            ).first()
            
            if existing_admin:
                print(f"Admin user already exists: {existing_admin.username}")
                db.session.commit()
                return company, existing_admin
            
            # Create admin user
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@company.com')
            
            admin_user = User(
                company_id=company.id,
                username=admin_username,
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                first_name=os.environ.get('ADMIN_FIRST_NAME', 'System'),
                last_name=os.environ.get('ADMIN_LAST_NAME', 'Administrator'),
                phone=os.environ.get('ADMIN_PHONE'),
                department='IT',
                position='System Administrator',
                role='admin',
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print(f"Created admin user: {admin_user.username}")
            print(f"Admin credentials: {admin_username} / {admin_password}")
            print("Database initialization completed successfully!")
            
            return company, admin_user
            
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")
        if 'db' in locals():
            db.session.rollback()
        raise e

if __name__ == "__main__":
    init_database()