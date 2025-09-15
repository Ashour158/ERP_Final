#!/usr/bin/env python3
"""
Test script for security improvements and storage backend
"""

import os
import sys
import tempfile
from io import StringIO


def test_database_uri_masking():
    """Test database URI masking functionality"""
    print("Testing database URI masking...")
    
    # Capture stdout to test the masked output
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    try:
        # Import app which should trigger the masking
        import app
        
        # Restore stdout and get the captured output
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        # Check that the output contains masked URI, not the real one
        if "Database URI:" in output:
            # Find the database URI line
            for line in output.split('\n'):
                if line.strip().startswith("Database URI:"):
                    print(f"✓ Found masked URI line: {line.strip()}")
                    # Should not contain actual database credentials
                    if "***" in line and ("sqlite://" in line or "postgresql://" in line):
                        print("✓ Database URI properly masked")
                        return True
                    else:
                        print(f"✗ URI not properly masked: {line}")
                        return False
        
        print("✗ Database URI line not found in output")
        return False
        
    except Exception as e:
        sys.stdout = old_stdout
        print(f"✗ Error testing URI masking: {e}")
        return False


def test_production_validation():
    """Test production environment validation"""
    print("\nTesting production validation...")
    
    # Test with invalid URL
    os.environ['FLASK_ENV'] = 'production'
    os.environ['DATABASE_URL'] = 'invalid-url'
    
    try:
        # This should exit with code 1
        import subprocess
        result = subprocess.run([
            sys.executable, '-c', 
            'import sys; sys.path.insert(0, "."); from app import app'
        ], capture_output=True, text=True, cwd='/home/runner/work/ERP_Final/ERP_Final')
        
        if result.returncode == 1 and "FATAL ERROR" in result.stdout:
            print("✓ Production validation correctly rejects invalid DATABASE_URL")
        else:
            print(f"✗ Production validation failed. Return code: {result.returncode}")
            print(f"Stdout: {result.stdout}")
            print(f"Stderr: {result.stderr}")
            return False
        
    except Exception as e:
        print(f"✗ Error testing production validation: {e}")
        return False
    finally:
        # Reset environment
        os.environ.pop('FLASK_ENV', None)
        os.environ.pop('DATABASE_URL', None)
    
    return True


def test_storage_backend():
    """Test storage backend functionality"""
    print("\nTesting storage backend...")
    
    try:
        from storage import get_storage_backend, create_storage_backend
        
        # Test local backend creation
        local_backend = create_storage_backend('local')
        if local_backend.uploads_folder == 'uploads':
            print("✓ Local storage backend created successfully")
        else:
            print("✗ Local storage backend configuration incorrect")
            return False
        
        # Test factory function
        auto_backend = get_storage_backend()
        if type(auto_backend).__name__ == 'LocalStorageBackend':
            print("✓ Storage backend factory works correctly")
        else:
            print("✗ Storage backend factory failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing storage backend: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("Security and Storage Backend Tests")
    print("=" * 40)
    
    os.chdir('/home/runner/work/ERP_Final/ERP_Final')
    
    tests = [
        test_database_uri_masking,
        test_production_validation,
        test_storage_backend
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Security improvements working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())