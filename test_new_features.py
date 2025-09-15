#!/usr/bin/env python3
"""
Test suite for new ERP System features:
- Database URL masking and validation
- File upload endpoint
- Health endpoint
- Storage backends
"""

import os
import sys
import tempfile
import io
from unittest.mock import patch, MagicMock

import pytest

# Set test environment before importing app
os.environ["FLASK_ENV"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Import app and modules after setting environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, db
from db_utils import mask_db_uri, is_valid_prod_db_url, get_database_info
from storage import LocalStorageBackend, SpacesStorageBackend, generate_safe_key


@pytest.fixture
def client():
    """Create test client"""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    with app.test_client() as client:
        with app.app_context():
            try:
                db.create_all()
            except Exception:
                # Handle case where tables might already exist or DB is not needed
                pass
        yield client


@pytest.fixture
def temp_upload_dir():
    """Create temporary upload directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestDatabaseUtils:
    """Test database utility functions"""
    
    def test_mask_db_uri_sqlite_memory(self):
        """Test masking SQLite in-memory database URI"""
        uri = "sqlite:///:memory:"
        result = mask_db_uri(uri)
        assert result == "sqlite:///:memory:"
    
    def test_mask_db_uri_sqlite_file(self):
        """Test masking SQLite file database URI"""
        uri = "sqlite:///data/app.db"
        result = mask_db_uri(uri)
        assert result == "sqlite:///app.db"
        
        uri = "sqlite:///app.db"
        result = mask_db_uri(uri)
        assert result == "sqlite:///app.db"
    
    def test_mask_db_uri_postgresql_with_credentials(self):
        """Test masking PostgreSQL URI with credentials"""
        uri = "postgresql://user:password@localhost:5432/dbname"
        result = mask_db_uri(uri)
        expected = "postgresql://***masked***:***masked***@localhost:5432/dbname"
        assert result == expected
    
    def test_mask_db_uri_postgresql_without_credentials(self):
        """Test PostgreSQL URI without credentials"""
        uri = "postgresql://localhost:5432/dbname"
        result = mask_db_uri(uri)
        assert result == uri  # Should remain unchanged
    
    def test_mask_db_uri_none_or_empty(self):
        """Test masking None or empty URI"""
        assert mask_db_uri(None) == "Not configured"
        assert mask_db_uri("") == "Not configured"
    
    def test_mask_db_uri_invalid(self):
        """Test masking invalid URI"""
        # Test a truly invalid URI that would cause urlparse to fail
        with patch('db_utils.urlparse') as mock_urlparse:
            mock_urlparse.side_effect = Exception("Parse error")
            result = mask_db_uri("invalid-uri")
            assert result == "***invalid_or_unparseable_uri***"
    
    def test_is_valid_prod_db_url_sqlite_invalid(self):
        """Test that SQLite URIs are not valid for production"""
        assert not is_valid_prod_db_url("sqlite:///app.db")
        assert not is_valid_prod_db_url("sqlite:///:memory:")
    
    def test_is_valid_prod_db_url_localhost_invalid(self):
        """Test that localhost URIs are not valid for production"""
        uris = [
            "postgresql://user:pass@localhost:5432/db",
            "postgresql://user:pass@127.0.0.1:5432/db",
            "postgresql://user:pass@0.0.0.0:5432/db"
        ]
        for uri in uris:
            assert not is_valid_prod_db_url(uri)
    
    def test_is_valid_prod_db_url_missing_credentials(self):
        """Test that URIs without credentials are not valid for production"""
        uris = [
            "postgresql://production-host:5432/db",
            "postgresql://user@production-host:5432/db",
            "postgresql://:password@production-host:5432/db"
        ]
        for uri in uris:
            assert not is_valid_prod_db_url(uri)
    
    def test_is_valid_prod_db_url_missing_database(self):
        """Test that URIs without database name are not valid for production"""
        uris = [
            "postgresql://user:pass@production-host:5432/",
            "postgresql://user:pass@production-host:5432"
        ]
        for uri in uris:
            assert not is_valid_prod_db_url(uri)
    
    def test_is_valid_prod_db_url_valid_postgresql(self):
        """Test valid production PostgreSQL URI"""
        uri = "postgresql://user:password@production-db.example.com:5432/myapp"
        assert is_valid_prod_db_url(uri)
    
    def test_is_valid_prod_db_url_valid_mysql(self):
        """Test valid production MySQL URI"""
        uri = "mysql://user:password@db.company.com:3306/production_db"
        assert is_valid_prod_db_url(uri)
    
    def test_is_valid_prod_db_url_invalid_scheme(self):
        """Test invalid database schemes"""
        uri = "invalid://user:password@host:5432/db"
        assert not is_valid_prod_db_url(uri)
    
    def test_get_database_info_postgresql(self):
        """Test extracting PostgreSQL database info"""
        uri = "postgresql://user:password@prod-db.example.com:5432/myapp_db"
        info = get_database_info(uri)
        
        assert info['type'] == 'PostgreSQL'
        assert info['host'] == 'prod-db.example.com'
        assert info['port'] == 5432
        assert info['database'] == 'myapp_db'
        assert info['is_production_ready'] is True
    
    def test_get_database_info_sqlite(self):
        """Test extracting SQLite database info"""
        uri = "sqlite:///app.db"
        info = get_database_info(uri)
        
        assert info['type'] == 'SQLite'
        assert info['host'] == 'unknown'
        assert info['port'] is None
        assert info['database'] == 'app.db'  # Should extract filename
        assert info['is_production_ready'] is False


class TestStorageBackends:
    """Test storage backend functionality"""
    
    def test_generate_safe_key(self):
        """Test safe key generation"""
        key = generate_safe_key("test.txt")
        assert key.endswith(".txt")
        assert len(key) > 10  # Should include UUID
        
        key_with_prefix = generate_safe_key("document.pdf", "uploads/docs")
        assert key_with_prefix.startswith("uploads/docs/")
        assert key_with_prefix.endswith(".pdf")
    
    def test_local_storage_backend(self, temp_upload_dir):
        """Test local storage backend"""
        backend = LocalStorageBackend(base_path=temp_upload_dir)
        
        # Test file save
        test_content = b"Hello, World!"
        file_stream = io.BytesIO(test_content)
        key = "test/file.txt"
        
        saved_key = backend.save_file(file_stream, key)
        assert saved_key == key
        
        # Test file exists
        file_path = os.path.join(temp_upload_dir, key)
        assert os.path.exists(file_path)
        
        # Test file content
        with open(file_path, 'rb') as f:
            assert f.read() == test_content
        
        # Test URL generation
        url = backend.url_for_key(key)
        assert key in url
        
        # Test file deletion
        assert backend.delete_file(key) is True
        assert not os.path.exists(file_path)
        
        # Test deleting non-existent file
        assert backend.delete_file("nonexistent.txt") is False
    
    def test_spaces_storage_backend_init(self):
        """Test Spaces storage backend initialization"""
        with patch.dict('sys.modules', {'boto3': MagicMock()}):
            # Mock the boto3 module and client
            import sys
            mock_boto3 = sys.modules['boto3']
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            
            backend = SpacesStorageBackend(
                endpoint_url="https://nyc3.digitaloceanspaces.com",
                region="nyc3",
                access_key="test_key",
                secret_key="test_secret",
                bucket_name="test-bucket"
            )
            
            assert backend.endpoint_url == "https://nyc3.digitaloceanspaces.com"
            assert backend.bucket_name == "test-bucket"
            mock_boto3.client.assert_called_once()
    
    def test_spaces_storage_backend_save_file(self):
        """Test Spaces storage backend file save"""
        with patch.dict('sys.modules', {'boto3': MagicMock()}):
            import sys
            mock_boto3 = sys.modules['boto3']
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            
            backend = SpacesStorageBackend(
                endpoint_url="https://nyc3.digitaloceanspaces.com",
                region="nyc3",
                access_key="test_key",
                secret_key="test_secret",
                bucket_name="test-bucket"
            )
            
            # Test file save
            test_content = b"Test file content"
            file_stream = io.BytesIO(test_content)
            key = "test/file.txt"
            
            saved_key = backend.save_file(file_stream, key)
            assert saved_key == key
            
            # Verify upload_fileobj was called
            mock_client.upload_fileobj.assert_called_once()
            args, kwargs = mock_client.upload_fileobj.call_args
            assert args[1] == "test-bucket"
            assert args[2] == key
            assert kwargs['ExtraArgs']['ACL'] == 'public-read'
    
    def test_spaces_storage_backend_url_generation(self):
        """Test Spaces storage backend URL generation"""
        with patch.dict('sys.modules', {'boto3': MagicMock()}):
            import sys
            mock_boto3 = sys.modules['boto3']
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            
            backend = SpacesStorageBackend(
                endpoint_url="https://nyc3.digitaloceanspaces.com",
                region="nyc3",
                access_key="test_key",
                secret_key="test_secret",
                bucket_name="test-bucket"
            )
            
            url = backend.url_for_key("path/to/file.txt")
            expected = "https://test-bucket.nyc3.digitaloceanspaces.com/path/to/file.txt"
            assert url == expected


class TestUploadEndpoint:
    """Test file upload endpoint"""
    
    def test_upload_no_file(self, client):
        """Test upload endpoint with no file"""
        response = client.post('/upload')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'No file provided' in data['message']
    
    def test_upload_empty_filename(self, client):
        """Test upload endpoint with empty filename"""
        data = {'file': (io.BytesIO(b"test"), '')}
        response = client.post('/upload', data=data)
        assert response.status_code == 400
        
        response_data = response.get_json()
        assert response_data['status'] == 'error'
        assert 'No file selected' in response_data['message']
    
    @patch('app.storage')
    def test_upload_successful(self, mock_storage, client):
        """Test successful file upload"""
        # Mock storage backend
        mock_storage.save_file.return_value = "uploads/test-file.txt"
        mock_storage.url_for_key.return_value = "http://localhost:5000/uploads/test-file.txt"
        
        # Mock isinstance check for backend type
        with patch('app.isinstance', return_value=False):  # Local storage
            data = {
                'file': (io.BytesIO(b"test content"), 'test.txt'),
                'path': 'documents'
            }
            response = client.post('/upload', data=data)
            
            assert response.status_code == 200
            response_data = response.get_json()
            assert response_data['status'] == 'ok'
            assert 'key' in response_data
            assert 'url' in response_data
            assert response_data['backend'] == 'local'
    
    @patch('app.storage')
    def test_upload_storage_error(self, mock_storage, client):
        """Test upload endpoint with storage error"""
        mock_storage.save_file.side_effect = Exception("Storage error")
        
        data = {'file': (io.BytesIO(b"test"), 'test.txt')}
        response = client.post('/upload', data=data)
        
        assert response.status_code == 500
        response_data = response.get_json()
        assert response_data['status'] == 'error'
        assert 'Upload failed' in response_data['message']


class TestHealthEndpoint:
    """Test health endpoint"""
    
    def test_health_endpoint_success(self, client):
        """Test health endpoint with successful database connection"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['database'] == 'up'
        assert 'storage_backend' in data
        assert 'masked_database' in data
        assert 'timestamp' in data
    
    @patch('app.db.session.execute')
    def test_health_endpoint_db_failure(self, mock_execute, client):
        """Test health endpoint with database failure"""
        mock_execute.side_effect = Exception("Database error")
        
        response = client.get('/health')
        assert response.status_code == 200  # Should not return 500
        
        data = response.get_json()
        assert data['status'] == 'degraded'
        assert data['database'] == 'down'
        assert 'storage_backend' in data
        assert 'masked_database' in data
    
    @patch('app.mask_db_uri')
    @patch('app.isinstance')
    def test_health_endpoint_storage_backend_detection(self, mock_isinstance, mock_mask_db_uri, client):
        """Test health endpoint storage backend detection"""
        mock_mask_db_uri.return_value = "sqlite:///:memory:"
        
        # Test Spaces backend detection
        mock_isinstance.return_value = True  # SpacesStorageBackend
        response = client.get('/health')
        data = response.get_json()
        assert data['storage_backend'] == 'spaces'
        
        # Test Local backend detection
        mock_isinstance.return_value = False  # LocalStorageBackend
        response = client.get('/health')
        data = response.get_json()
        assert data['storage_backend'] == 'local'


class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_basic_health_endpoint_still_works(self, client):
        """Test that original health endpoint still works"""
        response = client.get('/')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'timestamp' in data
    
    @patch('app.storage')
    def test_upload_and_health_endpoints_work_together(self, mock_storage, client):
        """Test that upload and health endpoints work together"""
        # First test health
        health_response = client.get('/health')
        assert health_response.status_code == 200
        
        # Mock storage for upload test
        mock_storage.save_file.return_value = "test-file.txt"
        mock_storage.url_for_key.return_value = "http://localhost/test-file.txt"
        
        with patch('app.isinstance', return_value=False):
            # Then test upload
            upload_data = {'file': (io.BytesIO(b"test"), 'test.txt')}
            upload_response = client.post('/upload', data=upload_data)
            assert upload_response.status_code == 200
            
            upload_data = upload_response.get_json()
            assert upload_data['status'] == 'ok'