#!/usr/bin/env python3
"""
Deployment readiness check for ERP System
Validates environment variables and configuration
"""

import os
import sys

def check_required_env_vars():
    """Check if required environment variables are set"""
    print("Checking environment variables...")
    
    # Core variables
    required_vars = [
        'FLASK_ENV',
        'SECRET_KEY', 
        'JWT_SECRET_KEY'
    ]
    
    # Environment-specific variables
    flask_env = os.environ.get('FLASK_ENV', 'development')
    
    if flask_env == 'production':
        required_vars.append('DATABASE_URL')
    elif flask_env == 'development':
        # DEV_DATABASE_URL is optional (falls back to SQLite)
        pass
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if not value or value.startswith('your-') or value.startswith('dev-'):
            missing_vars.append(var)
        else:
            print(f"✓ {var} is set")
    
    if missing_vars:
        print(f"⚠️  Missing or default values for: {', '.join(missing_vars)}")
        return False
    
    return True

def check_optional_env_vars():
    """Check optional environment variables"""
    print("\nChecking optional environment variables...")
    
    optional_vars = [
        'CORS_ORIGINS',
        'REDIS_URL',
        'MAIL_SERVER',
        'DEFAULT_COMPANY_NAME',
        'ADMIN_USERNAME'
    ]
    
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            print(f"✓ {var} is set")
        else:
            print(f"- {var} not set (using defaults)")

def check_file_structure():
    """Check if required files exist"""
    print("\nChecking file structure...")
    
    required_files = [
        'app.py',
        'config.py',
        'wsgi.py', 
        'init_db.py',
        'requirements.txt',
        'Dockerfile',
        '.env.example'
    ]
    
    missing_files = []
    for filename in required_files:
        if os.path.exists(filename):
            print(f"✓ {filename} exists")
        else:
            missing_files.append(filename)
            print(f"✗ {filename} missing")
    
    return len(missing_files) == 0

def check_docker_setup():
    """Check Docker-related files"""
    print("\nChecking Docker setup...")
    
    if os.path.exists('Dockerfile'):
        print("✓ Dockerfile exists")
        
        # Check if Dockerfile has health check
        with open('Dockerfile', 'r') as f:
            content = f.read()
            if 'HEALTHCHECK' in content:
                print("✓ Dockerfile has health check")
            else:
                print("- Dockerfile missing health check")
        
        return True
    else:
        print("✗ Dockerfile missing")
        return False

def check_security_settings():
    """Check security-related settings"""
    print("\nChecking security settings...")
    
    flask_env = os.environ.get('FLASK_ENV', 'development')
    
    if flask_env == 'production':
        # Check if using default/weak secrets
        secret_key = os.environ.get('SECRET_KEY', '')
        jwt_secret = os.environ.get('JWT_SECRET_KEY', '')
        
        if 'your-' in secret_key or 'dev-' in secret_key or len(secret_key) < 32:
            print("⚠️  SECRET_KEY appears to be default or weak")
            return False
        else:
            print("✓ SECRET_KEY appears secure")
        
        if 'your-' in jwt_secret or 'dev-' in jwt_secret or len(jwt_secret) < 32:
            print("⚠️  JWT_SECRET_KEY appears to be default or weak")
            return False
        else:
            print("✓ JWT_SECRET_KEY appears secure")
    else:
        print("- Security check skipped (not production)")
    
    return True

def main():
    """Run all deployment checks"""
    print("ERP System Deployment Readiness Check")
    print("=" * 40)
    
    checks = [
        check_file_structure,
        check_required_env_vars,
        check_optional_env_vars,
        check_docker_setup,
        check_security_settings
    ]
    
    all_passed = True
    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"✗ Check {check.__name__} failed: {e}")
            all_passed = False
        print()  # Add spacing between checks
    
    if all_passed:
        print("🚀 System is ready for deployment!")
        return 0
    else:
        print("⚠️  Some deployment checks failed. Review configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())