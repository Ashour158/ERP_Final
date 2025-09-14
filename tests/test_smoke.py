"""
Smoke tests for ERP System
Basic functionality and import tests
"""
import pytest


def test_app_imports():
    """Test that core app modules can be imported."""
    try:
        import app
        import config
        import wsgi
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import core modules: {e}")


def test_app_creation():
    """Test that Flask app can be created."""
    from app import app
    assert app is not None
    assert app.config is not None


def test_config_loading():
    """Test that configuration can be loaded."""
    from config import config
    
    # Test that config dictionary exists and has expected environments
    assert 'development' in config
    assert 'production' in config
    assert 'testing' in config
    assert 'default' in config


def test_database_models_import():
    """Test that database models can be imported without errors."""
    try:
        from app import db, Company, User
        # Basic check that models exist
        assert db is not None
        assert Company is not None
        assert User is not None
    except ImportError as e:
        pytest.fail(f"Failed to import database models: {e}")


def test_helper_functions():
    """Test that helper functions work correctly."""
    from app import safe_float, safe_int
    
    # Test safe_float
    assert safe_float("123.45") == 123.45
    assert safe_float("invalid") == 0.0
    assert safe_float(None) == 0.0
    assert safe_float("") == 0.0
    
    # Test safe_int
    assert safe_int("123") == 123
    assert safe_int("invalid") == 0
    assert safe_int(None) == 0
    assert safe_int("") == 0


def test_flask_app_configuration(app_instance):
    """Test that Flask app is properly configured."""
    assert app_instance.config['TESTING'] is True
    assert 'SECRET_KEY' in app_instance.config
    assert 'JWT_SECRET_KEY' in app_instance.config


def test_app_routes_exist():
    """Test that key routes are registered."""
    from app import app
    
    # Get all registered routes
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    
    # Check that health endpoint exists
    assert '/' in routes