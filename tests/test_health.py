"""
Test health endpoint functionality
"""
import json
import pytest


def test_health_endpoint_success(client):
    """Test that health endpoint returns 200 when database is accessible."""
    response = client.get('/')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['status'] == 'ok'
    assert 'timestamp' in data
    assert 'env' in data
    assert data['database'] == 'connected'


def test_health_endpoint_content_type(client):
    """Test that health endpoint returns JSON content type."""
    response = client.get('/')
    
    assert response.content_type == 'application/json'


def test_health_endpoint_includes_environment(client):
    """Test that health endpoint includes environment information."""
    response = client.get('/')
    data = json.loads(response.data)
    
    # Should include environment info (development in test)
    assert 'env' in data
    assert isinstance(data['env'], str)


def test_health_endpoint_includes_timestamp(client):
    """Test that health endpoint includes a timestamp."""
    response = client.get('/')
    data = json.loads(response.data)
    
    assert 'timestamp' in data
    assert isinstance(data['timestamp'], str)
    # Basic ISO format check
    assert 'T' in data['timestamp']


class TestHealthEndpointIntegration:
    """Integration tests for health endpoint."""
    
    def test_health_endpoint_availability(self, client):
        """Smoke test - ensure health endpoint is accessible."""
        response = client.get('/')
        assert response.status_code in [200, 503]  # Allow both success and service unavailable
    
    def test_health_endpoint_json_structure(self, client):
        """Test that health endpoint returns valid JSON structure."""
        response = client.get('/')
        
        try:
            data = json.loads(response.data)
            # Required fields should be present
            required_fields = ['status', 'timestamp', 'env']
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
        except json.JSONDecodeError:
            pytest.fail("Health endpoint did not return valid JSON")