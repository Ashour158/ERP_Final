#!/usr/bin/env python3
"""
Database initialization script for ERP System
Creates initial Company and Admin user with proper environment variable support
"""

import os
from typing import Tuple, Optional

from werkzeug.security import generate_password_hash


def init_database() -> Tuple[Optional[object], Optional[object]]:
    """Initialize a default company and admin user if they do not exist.
    Returns (company, admin_user). On failure, returns (None, None) and does not crash startup.
    """
    try:
        # Import inside function to avoid circular imports and handle missing dependencies
        from app import db, Company, User
        
        # Company settings from environment
        company_code = os.getenv("DEFAULT_COMPANY_CODE", "DEFAULT")
        company_name = os.getenv("DEFAULT_COMPANY_NAME", "Default Company")
        company_email = os.getenv("DEFAULT_COMPANY_EMAIL", "admin@example.com")

        # Check if company already exists
        company = Company.query.filter_by(code=company_code).first()
        if not company:
            company = Company(
                name=company_name,
                code=company_code,
                email=company_email,
                is_active=True,
            )
            db.session.add(company)
            db.session.flush()  # get company.id

        # Admin user settings from environment
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        admin_email = os.getenv("ADMIN_EMAIL", company_email)
        admin_first_name = os.getenv("ADMIN_FIRST_NAME", "System")
        admin_last_name = os.getenv("ADMIN_LAST_NAME", "Administrator")

        # Check if admin user already exists
        admin_user = User.query.filter_by(username=admin_username).first()
        if not admin_user:
            admin_user = User(
                company_id=company.id,
                username=admin_username,
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                first_name=admin_first_name,
                last_name=admin_last_name,
                role='admin',
                is_active=True
            )
            db.session.add(admin_user)

        db.session.commit()
        return company, admin_user

    except Exception as e:
        print(f"init_db initialization warning: {str(e)}")
        # Rollback on any error
        try:
            if 'db' in locals():
                db.session.rollback()
        except:
            pass
        return None, None


if __name__ == "__main__":
    # Allow running this script directly for manual database initialization
    from app import app
    with app.app_context():
        company, admin_user = init_database()
        if company and admin_user:
            print(f"Successfully initialized database with company: {company.name}")
            print(f"Admin user created: {admin_user.username}")
        else:
            print("Database initialization failed or was not needed")