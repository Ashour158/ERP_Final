"""
Test configuration and fixtures for ERP System
"""
import os
import tempfile
import pytest
from app import app, db


@pytest.fixture
def app_instance():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


@pytest.fixture
def client(app_instance):
    """A test client for the app."""
    return app_instance.test_client()


@pytest.fixture
def runner(app_instance):
    """A test runner for the app's Click commands."""
    return app_instance.test_cli_runner()


@pytest.fixture
def auth_headers():
    """Mock authentication headers for testing protected endpoints."""
    return {
        'Authorization': 'Bearer test-token',
        'Content-Type': 'application/json'
    }