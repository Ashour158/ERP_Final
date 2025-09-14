#!/usr/bin/env python3
"""
Basic validation script for ERP System
Tests configuration loading and basic functionality
"""

import os
import sys
import tempfile

def test_config_loading():
    """Test configuration loading"""
    print("Testing configuration loading...")
    
    try:
        from config import config
        
        # Test all config environments
        for env_name in ['development', 'production', 'testing']:
            cfg = config.get(env_name)
            if cfg:
                instance = cfg()
                print(f"✓ {env_name} config loaded successfully")
                print(f"  JWT expires: {instance.JWT_ACCESS_TOKEN_EXPIRES}")
            else:
                print(f"✗ {env_name} config failed to load")
        
        return True
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        return False

def test_helper_functions():
    """Test helper functions"""
    print("\nTesting helper functions...")
    
    try:
        # We can't test all functions without Flask context, but we can test imports
        import app
        
        # Test safe conversion functions
        assert app.safe_float("123.45") == 123.45
        assert app.safe_float("invalid") == 0.0
        assert app.safe_float(None) == 0.0
        print("✓ safe_float function works")
        
        assert app.safe_int("123") == 123
        assert app.safe_int("invalid") == 0
        assert app.safe_int(None) == 0
        print("✓ safe_int function works")
        
        return True
    except Exception as e:
        print(f"✗ Helper functions test failed: {e}")
        return False

def test_database_models():
    """Test database models can be imported"""
    print("\nTesting database models...")
    
    try:
        from app import Company, User, UserKPI, VigilanceAlert
        print("✓ Core models imported successfully")
        return True
    except Exception as e:
        print(f"✗ Database models test failed: {e}")
        return False

def test_environment_configs():
    """Test environment-specific configurations"""
    print("\nTesting environment configurations...")
    
    # Test development config
    os.environ['FLASK_ENV'] = 'development'
    try:
        from config import config
        dev_config = config['development']()
        assert 'dev_erp.db' in dev_config.SQLALCHEMY_DATABASE_URI or 'DEV_DATABASE_URL' in str(dev_config.SQLALCHEMY_DATABASE_URI)
        print("✓ Development config works")
    except Exception as e:
        print(f"✗ Development config failed: {e}")
        return False
    
    # Test production config
    os.environ['FLASK_ENV'] = 'production'
    try:
        prod_config = config['production']()
        assert 'DATABASE_URL' in str(prod_config.SQLALCHEMY_DATABASE_URI) or 'postgresql' in prod_config.SQLALCHEMY_DATABASE_URI
        print("✓ Production config works")
    except Exception as e:
        print(f"✗ Production config failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("ERP System Validation Tests")
    print("=" * 40)
    
    tests = [
        test_config_loading,
        test_helper_functions,
        test_database_models,
        test_environment_configs
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
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())