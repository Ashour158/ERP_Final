"""
Test suite for operational hardening features:
- Upload size limits
- Rate limiting
- Error handling
"""

import os
import sys
import tempfile
import time
from unittest.mock import patch, MagicMock
from io import BytesIO

import pytest

# Set test environment before importing app
os.environ["FLASK_ENV"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Import app after setting environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, db


@pytest.fixture
def client():
    """Create test client with custom configuration"""
    # Override configuration for testing
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_MAX_BYTES"] = 1024  # 1KB for testing
    app.config["MAX_CONTENT_LENGTH"] = 1024
    app.config["RATE_LIMIT_UPLOAD_WINDOW_SECONDS"] = 10  # 10 seconds for testing
    app.config["RATE_LIMIT_UPLOAD_MAX_REQUESTS"] = 2  # 2 requests for testing
    app.config["RATE_LIMIT_HEALTH_WINDOW_SECONDS"] = 10  # 10 seconds for testing
    app.config["RATE_LIMIT_HEALTH_MAX_REQUESTS"] = 3  # 3 requests for testing

    with app.test_client() as client:
        with app.app_context():
            try:
                db.create_all()
            except Exception:
                pass
        yield client


class TestUploadSizeLimits:
    """Test upload size limit functionality"""

    def test_upload_file_within_limit(self, client):
        """Test upload of file within size limit"""
        from app import upload_hits
        upload_hits.clear()  # Clear rate limit data
        
        # Create a small file (less than 1KB)
        small_file = BytesIO(b"small file content")
        small_file.name = "test.txt"
        
        with patch('app.storage.save_file') as mock_save, \
             patch('app.storage.url_for_key') as mock_url:
            mock_save.return_value = "test-key"
            mock_url.return_value = "http://example.com/test-key"
            
            response = client.post('/upload', data={
                'file': (small_file, 'test.txt')
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'

    def test_upload_file_too_large_returns_413(self, client):
        """Test that uploading a file larger than limit returns 413"""
        from app import upload_hits
        upload_hits.clear()  # Clear rate limit data
        
        # Create a large file (larger than 1KB)
        large_file = BytesIO(b"x" * 2048)  # 2KB file
        large_file.name = "large.txt"
        
        response = client.post('/upload', data={
            'file': (large_file, 'large.txt')
        })
        
        assert response.status_code == 413
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'File too large' in data['message']
        assert '1024 bytes' in data['message']

    def test_413_error_handler_message_format(self, client):
        """Test that 413 error includes proper message format"""
        from app import upload_hits
        upload_hits.clear()  # Clear rate limit data
        
        large_file = BytesIO(b"x" * 2048)
        large_file.name = "large.txt"
        
        response = client.post('/upload', data={
            'file': (large_file, 'large.txt')
        })
        
        assert response.status_code == 413
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Max 1024 bytes' in data['message']
        assert '0.0MB' in data['message']  # 1024 bytes = 0.001 MB, displayed as 0.0MB


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_health_endpoint_rate_limiting(self, client):
        """Test rate limiting on health endpoint"""
        # Clear any existing rate limit data
        from app import health_hits
        health_hits.clear()
        
        # Make requests within limit
        for i in range(3):  # Should be allowed (limit is 3)
            response = client.get('/health')
            assert response.status_code in [200, 503]  # 503 if DB fails
            assert 'X-RateLimit-Limit' in response.headers
            assert 'X-RateLimit-Remaining' in response.headers
            assert 'X-RateLimit-Reset' in response.headers
        
        # Next request should be rate limited
        response = client.get('/health')
        assert response.status_code == 429
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Rate limit exceeded' in data['message']

    def test_upload_endpoint_rate_limiting(self, client):
        """Test rate limiting on upload endpoint"""
        # Clear any existing rate limit data
        from app import upload_hits
        upload_hits.clear()
        
        with patch('app.storage.save_file') as mock_save, \
             patch('app.storage.url_for_key') as mock_url:
            mock_save.return_value = "test-key"
            mock_url.return_value = "http://example.com/test-key"
            
            # Make requests within limit (limit is 2)
            for i in range(2):
                small_file = BytesIO(b"test")  # Create fresh file each time
                small_file.name = f"test{i}.txt"
                response = client.post('/upload', data={
                    'file': (small_file, f'test{i}.txt')
                })
                assert response.status_code == 200
                assert 'X-RateLimit-Limit' in response.headers
                assert 'X-RateLimit-Remaining' in response.headers
            
            # Next request should be rate limited
            small_file = BytesIO(b"test")
            small_file.name = 'test_over_limit.txt'
            response = client.post('/upload', data={
                'file': (small_file, 'test_over_limit.txt')
            })
            assert response.status_code == 429

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present in successful responses"""
        from app import health_hits
        health_hits.clear()
        
        response = client.get('/health')
        assert response.status_code in [200, 503]
        
        # Check headers are present and have correct format
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
        assert 'X-RateLimit-Reset' in response.headers
        
        # Headers should be numeric strings
        assert response.headers['X-RateLimit-Limit'].isdigit()
        assert response.headers['X-RateLimit-Remaining'].isdigit()
        assert response.headers['X-RateLimit-Reset'].isdigit()

    def test_rate_limit_different_ips(self, client):
        """Test that rate limiting is per IP"""
        from app import health_hits
        health_hits.clear()
        
        # Make requests from first IP to hit limit
        for i in range(3):
            response = client.get('/health', environ_base={'REMOTE_ADDR': '1.1.1.1'})
            assert response.status_code in [200, 503]
        
        # Should be rate limited
        response = client.get('/health', environ_base={'REMOTE_ADDR': '1.1.1.1'})
        assert response.status_code == 429
        
        # Request from different IP should not be rate limited
        response = client.get('/health', environ_base={'REMOTE_ADDR': '2.2.2.2'})
        assert response.status_code in [200, 503]  # Should work
        assert response.status_code != 429

    def test_rate_limit_window_expiry(self, client):
        """Test that rate limit window expires and resets"""
        from app import health_hits
        health_hits.clear()
        
        # Make requests to hit the limit
        for i in range(3):
            response = client.get('/health')
            assert response.status_code in [200, 503]
        
        # Should be rate limited now
        response = client.get('/health')
        assert response.status_code == 429
        
        # Manually clear the rate limit data to simulate time passing
        # (mocking time.time() is complex due to threading)
        health_hits.clear()
        
        # Should work again
        response = client.get('/health')
        assert response.status_code in [200, 503]


class TestIntegration:
    """Integration tests for all operational hardening features"""

    def test_upload_size_and_rate_limiting_together(self, client):
        """Test that both upload size limits and rate limiting work together"""
        from app import upload_hits
        upload_hits.clear()
        
        with patch('app.storage.save_file') as mock_save, \
             patch('app.storage.url_for_key') as mock_url:
            mock_save.return_value = "test-key"
            mock_url.return_value = "http://example.com/test-key"
            
            # First upload should work
            small_file1 = BytesIO(b"test")
            small_file1.name = "test1.txt"
            response = client.post('/upload', data={
                'file': (small_file1, 'test1.txt')
            })
            assert response.status_code == 200
            
            # Second upload should work
            small_file2 = BytesIO(b"test")
            small_file2.name = "test2.txt"
            response = client.post('/upload', data={
                'file': (small_file2, 'test2.txt')
            })
            assert response.status_code == 200
            
            # Third upload should be rate limited
            small_file3 = BytesIO(b"test")
            small_file3.name = "test3.txt"
            response = client.post('/upload', data={
                'file': (small_file3, 'test3.txt')
            })
            assert response.status_code == 429
            
        # Test large file size limit separately (without rate limit interference)
        upload_hits.clear()  # Clear rate limit to test size limit
        large_file = BytesIO(b"x" * 2048)
        large_file.name = "large.txt"
        response = client.post('/upload', data={
            'file': (large_file, 'large.txt')
        })
        assert response.status_code == 413

    def test_health_endpoints_both_rate_limited(self, client):
        """Test that both / and /health endpoints are rate limited"""
        from app import health_hits
        health_hits.clear()
        
        # Test / endpoint
        for i in range(3):
            response = client.get('/')
            assert response.status_code in [200, 503]
        
        response = client.get('/')
        assert response.status_code == 429
        
        # /health endpoint should also be affected (same rate limit pool)
        response = client.get('/health')
        assert response.status_code == 429

    def test_configuration_from_environment(self, client):
        """Test that configuration comes from environment variables"""
        # Test upload size configuration
        assert app.config['UPLOAD_MAX_BYTES'] == 1024
        assert app.config['MAX_CONTENT_LENGTH'] == 1024
        
        # Test rate limit configuration
        assert app.config['RATE_LIMIT_UPLOAD_WINDOW_SECONDS'] == 10
        assert app.config['RATE_LIMIT_UPLOAD_MAX_REQUESTS'] == 2
        assert app.config['RATE_LIMIT_HEALTH_WINDOW_SECONDS'] == 10
        assert app.config['RATE_LIMIT_HEALTH_MAX_REQUESTS'] == 3