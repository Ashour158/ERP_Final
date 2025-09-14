"""
Test suite for ERP System endpoints
"""
import os
import sys
import tempfile
import pytest
from unittest.mock import patch

# Set test environment before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Import app after setting environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, db


@pytest.fixture
def client():
    """Create test client"""
    # Use in-memory SQLite for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.test_client() as client:
        with app.app_context():
            try:
                db.create_all()
            except Exception:
                # Handle case where tables might already exist or DB is not needed
                pass
        yield client


def test_health_endpoint_success(client):
    """Test health endpoint returns success"""
    response = client.get('/')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'timestamp' in data
    assert 'env' in data


def test_health_endpoint_db_failure(client):
    """Test health endpoint handles database failure gracefully"""
    with patch('app.db.session.execute') as mock_execute:
        mock_execute.side_effect = Exception("Database error")
        
        response = client.get('/')
        assert response.status_code == 503
        
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'error' in data