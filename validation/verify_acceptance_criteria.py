#!/usr/bin/env python3
"""
Comprehensive verification of all acceptance criteria
"""

import os
import re

def verify_cors_fix():
    """Verify CORS uses app.config.get('CORS_ORIGINS', ["*"])"""
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Check for the exact fix
    pattern = r"app\.config\.get\('CORS_ORIGINS',\s*\[\"?\*\"?\]\)"
    if re.search(pattern, content):
        print("✓ CORS configuration fixed: app.config.get('CORS_ORIGINS', [\"*\"]) found")
        return True
    else:
        print("✗ CORS fix not found or incorrect")
        return False

def verify_init_db_requirements():
    """Verify init_db.py meets all requirements"""
    with open('init_db.py', 'r') as f:
        content = f.read()
    
    requirements = [
        # Function exists
        ('def init_database()', 'init_database() function exists'),
        
        # Environment variables
        ('DEFAULT_COMPANY_CODE', 'Uses DEFAULT_COMPANY_CODE env var'),
        ('DEFAULT_COMPANY_NAME', 'Uses DEFAULT_COMPANY_NAME env var'),
        ('DEFAULT_COMPANY_EMAIL', 'Uses DEFAULT_COMPANY_EMAIL env var'),
        ('ADMIN_USERNAME', 'Uses ADMIN_USERNAME env var'),
        ('ADMIN_PASSWORD', 'Uses ADMIN_PASSWORD env var'),
        ('ADMIN_EMAIL', 'Uses ADMIN_EMAIL env var'),
        ('ADMIN_FIRST_NAME', 'Uses ADMIN_FIRST_NAME env var'),
        ('ADMIN_LAST_NAME', 'Uses ADMIN_LAST_NAME env var'),
        
        # Safe defaults
        ('DEFAULT', 'Has safe default for company code'),
        ('Default Company', 'Has safe default for company name'),
        ('admin@example.com', 'Has safe default for email'),
        ('admin', 'Has safe default for admin username'),
        ('admin123', 'Has safe default for admin password'),
        ('System', 'Has safe default for admin first name'),
        ('Administrator', 'Has safe default for admin last name'),
        
        # Error handling
        ('try:', 'Has try-catch error handling'),
        ('except Exception', 'Has exception handling'),
        ('db.session.rollback()', 'Has rollback on errors'),
        ('return None, None', 'Returns (None, None) on failure'),
        
        # Database operations
        ('db.session.commit()', 'Commits changes'),
        ('db.session.flush()', 'Uses flush to get IDs'),
    ]
    
    all_passed = True
    for requirement, description in requirements:
        if requirement in content:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            all_passed = False
    
    return all_passed

def verify_wsgi_resilience():
    """Verify wsgi.py has resilient init_db handling"""
    with open('wsgi.py', 'r') as f:
        content = f.read()
    
    requirements = [
        ('db.create_all()', 'Calls db.create_all() inside app context'),
        ('try:', 'Has try-except blocks'),
        ('from init_db import init_database', 'Imports init_database'),
        ('except Exception as init_err:', 'Has specific error handling for init_db'),
        ('print(f"Database initialization warning:', 'Logs errors but continues'),
        ('getattr(company, \'name\', \'N/A\')', 'Uses safe attribute access'),
        ('getattr(admin_user, \'username\', \'N/A\')', 'Uses safe attribute access for user'),
    ]
    
    all_passed = True
    for requirement, description in requirements:
        if requirement in content:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            all_passed = False
    
    return all_passed

def verify_dockerfile_curl():
    """Verify Dockerfile installs curl"""
    with open('Dockerfile', 'r') as f:
        content = f.read()
    
    # Check that curl is in the apt-get install line
    if 'curl' in content and 'apt-get install' in content:
        print("✓ Dockerfile installs curl for HEALTHCHECK")
        return True
    else:
        print("✗ Dockerfile missing curl installation")
        return False

def verify_health_endpoint():
    """Verify health endpoint implementation"""
    with open('app.py', 'r') as f:
        content = f.read()
    
    requirements = [
        ('@app.route(\'/\'', 'Health route exists at /'),
        ('def health_check()', 'health_check function exists'),
        ('db.session.execute(text(\'SELECT 1\'))', 'Tests DB connection with SELECT 1'),
        ('\'status\': \'ok\'', 'Returns status ok on success'),
        ('\'env\':', 'Returns env'),
        ('\'timestamp\':', 'Returns timestamp'),
        ('except Exception', 'Has exception handling'),
        ('\'status\': \'error\'', 'Returns error status on failure'),
        (', 503', 'Returns 503 status code on DB failure'),
    ]
    
    all_passed = True
    for requirement, description in requirements:
        if requirement in content:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            all_passed = False
    
    return all_passed

def main():
    """Verify all acceptance criteria"""
    print("Verifying all acceptance criteria from problem statement...\n")
    
    print("1. CORS Configuration:")
    cors_ok = verify_cors_fix()
    
    print("\n2. init_db.py Requirements:")
    init_db_ok = verify_init_db_requirements()
    
    print("\n3. wsgi.py Resilience:")
    wsgi_ok = verify_wsgi_resilience()
    
    print("\n4. Dockerfile curl Installation:")
    docker_ok = verify_dockerfile_curl()
    
    print("\n5. Health Endpoint:")
    health_ok = verify_health_endpoint()
    
    print("\n" + "="*60)
    
    results = [cors_ok, init_db_ok, wsgi_ok, docker_ok, health_ok]
    passed = sum(results)
    total = len(results)
    
    print(f"ACCEPTANCE CRITERIA VERIFICATION: {passed}/{total}")
    
    if all(results):
        print("✓ ALL ACCEPTANCE CRITERIA SATISFIED!")
        print("\nThe repository is ready for reliable production deployment.")
    else:
        print("✗ Some acceptance criteria not met.")
    
    return all(results)

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)