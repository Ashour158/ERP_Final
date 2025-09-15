#!/usr/bin/env python3
"""
Test rate limiting functionality for the ERP system
"""
import pytest
import os
import sys
import time

# Set environment before importing the app
os.environ['FLASK_ENV'] = 'testing'

# Import app and modules after setting environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, rate_limit_storage


@pytest.fixture
def client():
    """Create test client with rate limiting"""
    app.config['TESTING'] = True
    app.config['UPLOAD_MAX_BYTES'] = 1024 * 1024  # 1MB for testing
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
    
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clear_rate_limit_storage():
    """Clear rate limit storage before each test"""
    rate_limit_storage.clear()
    yield
    rate_limit_storage.clear()


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_health_endpoint_rate_limiting(self, client):
        """Test rate limiting on /health endpoint"""
        # Health endpoint allows 30 requests per minute
        # Make 29 requests - should all succeed
        for i in range(29):
            response = client.get('/health')
            assert response.status_code == 200
            assert 'X-RateLimit-Limit' in response.headers
            assert 'X-RateLimit-Remaining' in response.headers
            assert 'X-RateLimit-Reset' in response.headers
            assert response.headers['X-RateLimit-Limit'] == '30'
        
        # 30th request should still succeed
        response = client.get('/health')
        assert response.status_code == 200
        assert response.headers['X-RateLimit-Remaining'] == '0'
        
        # 31st request should be rate limited
        response = client.get('/health')
        assert response.status_code == 429
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Rate limit exceeded' in data['message']
        assert response.headers['X-RateLimit-Remaining'] == '0'
    
    def test_upload_endpoint_rate_limiting(self, client):
        """Test rate limiting on /upload endpoint"""
        import io
        
        # Upload endpoint allows 10 requests per minute
        # Make 10 requests with valid files - should all succeed
        for i in range(10):
            data = {'file': (io.BytesIO(b'test content'), f'test{i}.txt')}
            response = client.post('/upload', data=data, content_type='multipart/form-data')
            assert response.status_code == 200
            assert 'X-RateLimit-Limit' in response.headers
            assert 'X-RateLimit-Remaining' in response.headers
            assert response.headers['X-RateLimit-Limit'] == '10'
        
        # 11th request should be rate limited
        data = {'file': (io.BytesIO(b'test content'), 'test11.txt')}
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 429
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Rate limit exceeded' in data['message']
        assert response.headers['X-RateLimit-Remaining'] == '0'
    
    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present in responses"""
        response = client.get('/health')
        assert response.status_code == 200
        
        # Check required rate limit headers
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
        assert 'X-RateLimit-Reset' in response.headers
        
        # Verify header values are numeric
        assert response.headers['X-RateLimit-Limit'].isdigit()
        assert response.headers['X-RateLimit-Remaining'].isdigit()
        assert response.headers['X-RateLimit-Reset'].isdigit()
    
    def test_rate_limit_different_ips(self, client):
        """Test that rate limiting works per IP address"""
        # Clear storage first
        rate_limit_storage.clear()
        
        # Make requests from default IP (test client)
        for i in range(10):
            response = client.get('/health')
            assert response.status_code == 200
        
        # Simulate request from different IP using headers
        # (Note: In real scenarios, X-Forwarded-For would be set by proxy)
        headers = {'X-Forwarded-For': '192.168.1.100'}
        response = client.get('/health', headers=headers)
        assert response.status_code == 200
        # Should have full rate limit available for new IP
        assert int(response.headers['X-RateLimit-Remaining']) == 29

    def test_upload_size_limit_configuration(self, client):
        """Test that upload size limit is configurable"""
        import io
        
        # Test with file larger than configured limit (1MB in test config)
        large_content = b'x' * (2 * 1024 * 1024)  # 2MB
        data = {'file': (io.BytesIO(large_content), 'large_test.txt')}
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        # Should be rejected due to size limit - Flask catches this and the app returns 500 
        # which becomes an error response with rate limiting headers
        assert response.status_code == 500
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Upload failed' in data['message']
        # Should still have rate limit headers
        assert 'X-RateLimit-Limit' in response.headers
    
    def test_upload_endpoint_validation(self, client):
        """Test upload endpoint validation works with rate limiting"""
        # Test missing file
        response = client.post('/upload', data={}, content_type='multipart/form-data')
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'No file provided' in data['message']
        
        # Should still have rate limit headers
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
    
    def test_health_endpoint_structure(self, client):
        """Test health endpoint returns proper structure with rate limiting"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        required_fields = ['status', 'database', 'storage_backend', 'timestamp', 'environment']
        for field in required_fields:
            assert field in data
        
        # Verify rate limit headers
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
        assert 'X-RateLimit-Reset' in response.headers


if __name__ == '__main__':
    pytest.main([__file__])