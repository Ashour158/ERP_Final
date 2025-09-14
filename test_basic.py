#!/usr/bin/env python3
"""Basic test to verify app structure works"""
import os
import sys

def test_basic_imports():
    """Test if we can import basic Flask"""
    try:
        import flask
        print("✓ Flask import successful")
        return True
    except ImportError as e:
        print("✗ Flask import failed:", e)
        return False

def test_file_structure():
    """Test if required files exist"""
    required_files = ['app.py', 'wsgi.py', 'config.py', 'requirements.txt', 
                     'Dockerfile', 'docker-compose.yml', 'index.html']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files present")
        return True

def test_app_basic_structure():
    """Test if app.py has expected content"""
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        required_patterns = ['Flask', 'app =', 'db =', '@app.route']
        missing = []
        
        for pattern in required_patterns:
            if pattern not in content:
                missing.append(pattern)
        
        if missing:
            print(f"✗ Missing patterns in app.py: {missing}")
            return False
        else:
            print("✓ app.py structure looks correct")
            return True
    except Exception as e:
        print(f"✗ Error reading app.py: {e}")
        return False

if __name__ == "__main__":
    print("Running basic validation tests...")
    
    tests = [
        test_basic_imports,
        test_file_structure,
        test_app_basic_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ Basic validation successful - repository structure is correct")
        sys.exit(0)
    else:
        print("✗ Some basic validation tests failed")
        sys.exit(1)
