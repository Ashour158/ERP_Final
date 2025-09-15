#!/usr/bin/env python3
"""
Simple test to validate the changes made for production deployment readiness
"""

import os
import sys
from unittest.mock import patch, MagicMock

def test_cors_fix():
    """Test that CORS uses app.config.get instead of getattr"""
    # Read app.py and check for the fix
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Check that we're using app.config.get instead of getattr
    if 'app.config.get(\'CORS_ORIGINS\', ["*"])' in content:
        print("✓ CORS fix applied correctly")
        return True
    else:
        print("✗ CORS fix not found")
        return False

def test_init_db_env_vars():
    """Test that init_db.py uses environment variables"""
    with open('init_db.py', 'r') as f:
        content = f.read()
    
    # Check for environment variable usage
    required_env_vars = [
        'DEFAULT_COMPANY_CODE',
        'DEFAULT_COMPANY_NAME', 
        'DEFAULT_COMPANY_EMAIL',
        'ADMIN_USERNAME',
        'ADMIN_PASSWORD',
        'ADMIN_EMAIL',
        'ADMIN_FIRST_NAME',
        'ADMIN_LAST_NAME'
    ]
    
    all_found = True
    for env_var in required_env_vars:
        if f'os.getenv("{env_var}"' in content:
            print(f"✓ Found environment variable: {env_var}")
        else:
            print(f"✗ Missing environment variable: {env_var}")
            all_found = False
    
    return all_found

def test_wsgi_resilience():
    """Test that wsgi.py has proper error handling"""
    with open('wsgi.py', 'r') as f:
        content = f.read()
    
    # Check for nested try-except blocks
    if 'try:' in content and 'from init_db import init_database' in content and 'except Exception as init_err:' in content:
        print("✓ WSGI has proper error handling for init_db")
        return True
    else:
        print("✗ WSGI error handling not found")
        return False

def test_dockerfile_curl():
    """Test that Dockerfile includes curl"""
    with open('Dockerfile', 'r') as f:
        content = f.read()
    
    if 'curl' in content:
        print("✓ Dockerfile includes curl")
        return True
    else:
        print("✗ Dockerfile missing curl")
        return False

def test_health_endpoint():
    """Test that health endpoint exists and handles DB failures"""
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Check for health endpoint with proper error handling
    health_check = '@app.route(\'/\', methods=[\'GET\'])' in content
    error_handling = 'return jsonify({' in content and '503' in content
    
    if health_check and error_handling:
        print("✓ Health endpoint exists with proper error handling")
        return True
    else:
        print("✗ Health endpoint or error handling missing")
        return False

def main():
    """Run all tests"""
    print("Testing production deployment readiness changes...\n")
    
    tests = [
        test_cors_fix,
        test_init_db_env_vars,
        test_wsgi_resilience,
        test_dockerfile_curl,
        test_health_endpoint
    ]
    
    results = []
    for test in tests:
        print(f"\nRunning {test.__name__}:")
        results.append(test())
    
    print(f"\n{'='*50}")
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("✓ All production readiness changes validated successfully!")
        return True
    else:
        print("✗ Some tests failed. Please review the changes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)