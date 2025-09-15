#!/usr/bin/env python3
"""
Storage Backend System for ERP File Management
Pluggable storage backends supporting local filesystem and DigitalOcean Spaces
"""

import os
import uuid
from abc import ABC, abstractmethod
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    def save_file(self, file_stream, key):
        """Save file stream to storage backend
        
        Args:
            file_stream: File-like object to save
            key: Unique storage key/path for the file
            
        Returns:
            str: Final storage key/path where file was saved
        """
        pass
    
    @abstractmethod
    def url_for_key(self, key):
        """Get public URL for stored file
        
        Args:
            key: Storage key/path for the file
            
        Returns:
            str: Public URL to access the file
        """
        pass
    
    @abstractmethod
    def delete_file(self, key):
        """Delete file from storage
        
        Args:
            key: Storage key/path for the file
            
        Returns:
            bool: True if deleted successfully
        """
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend"""
    
    def __init__(self, base_path="uploads", base_url="http://localhost:5000/uploads"):
        """Initialize local storage backend
        
        Args:
            base_path: Local directory to store files
            base_url: Base URL to serve files from
        """
        self.base_path = os.path.abspath(base_path)
        self.base_url = base_url.rstrip('/')
        
        # Ensure upload directory exists
        os.makedirs(self.base_path, exist_ok=True)
        logger.info(f"LocalStorageBackend initialized: {self.base_path}")
    
    def save_file(self, file_stream, key):
        """Save file to local filesystem"""
        try:
            # Ensure subdirectories exist
            file_path = os.path.join(self.base_path, key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save file
            with open(file_path, 'wb') as f:
                chunk_size = 8192
                while True:
                    chunk = file_stream.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
            
            logger.info(f"File saved to local storage: {file_path}")
            return key
            
        except Exception as e:
            logger.error(f"Failed to save file to local storage: {str(e)}")
            raise
    
    def url_for_key(self, key):
        """Get URL for locally stored file"""
        return f"{self.base_url}/{key}"
    
    def delete_file(self, key):
        """Delete file from local filesystem"""
        try:
            file_path = os.path.join(self.base_path, key)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted from local storage: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file from local storage: {str(e)}")
            return False


class SpacesStorageBackend(StorageBackend):
    """DigitalOcean Spaces storage backend"""
    
    def __init__(self, endpoint_url, region, access_key, secret_key, bucket_name):
        """Initialize Spaces storage backend
        
        Args:
            endpoint_url: Spaces endpoint URL (e.g., https://nyc3.digitaloceanspaces.com)
            region: Spaces region (e.g., nyc3)
            access_key: Spaces access key
            secret_key: Spaces secret key
            bucket_name: Spaces bucket/space name
        """
        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            raise ImportError("boto3 is required for Spaces backend. Install with: pip install boto3")
        
        self.endpoint_url = endpoint_url
        self.region = region
        self.bucket_name = bucket_name
        
        # Initialize S3-compatible client for Spaces
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4')
        )
        
        logger.info(f"SpacesStorageBackend initialized: {bucket_name} @ {endpoint_url}")
    
    def save_file(self, file_stream, key):
        """Save file to DigitalOcean Spaces"""
        try:
            self.client.upload_fileobj(
                file_stream,
                self.bucket_name,
                key,
                ExtraArgs={'ACL': 'public-read'}  # Make file publicly accessible
            )
            
            logger.info(f"File saved to Spaces: {self.bucket_name}/{key}")
            return key
            
        except Exception as e:
            logger.error(f"Failed to save file to Spaces: {str(e)}")
            raise
    
    def url_for_key(self, key):
        """Get URL for Spaces stored file"""
        # Construct public URL for Spaces
        parsed_endpoint = urlparse(self.endpoint_url)
        hostname = parsed_endpoint.hostname
        
        # DigitalOcean Spaces URL format
        return f"https://{self.bucket_name}.{hostname}/{key}"
    
    def delete_file(self, key):
        """Delete file from DigitalOcean Spaces"""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"File deleted from Spaces: {self.bucket_name}/{key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from Spaces: {str(e)}")
            return False


def generate_safe_key(filename, path_prefix=""):
    """Generate a safe storage key for uploaded files
    
    Args:
        filename: Original filename
        path_prefix: Optional subdirectory prefix
        
    Returns:
        str: Safe storage key
    """
    # Extract file extension
    name, ext = os.path.splitext(filename)
    
    # Generate unique identifier
    unique_id = str(uuid.uuid4())
    
    # Create safe filename
    safe_filename = f"{unique_id}{ext.lower()}"
    
    # Combine with path prefix
    if path_prefix:
        # Sanitize path prefix
        safe_prefix = path_prefix.strip('/')
        safe_prefix = ''.join(c for c in safe_prefix if c.isalnum() or c in '-_/')
        return f"{safe_prefix}/{safe_filename}"
    
    return safe_filename


def create_storage_backend():
    """Factory function to create appropriate storage backend based on configuration
    
    Returns:
        StorageBackend: Configured storage backend instance
    """
    # Check for Spaces configuration
    spaces_endpoint = os.environ.get('SPACES_ENDPOINT_URL')
    spaces_region = os.environ.get('SPACES_REGION')
    spaces_access_key = os.environ.get('SPACES_ACCESS_KEY')
    spaces_secret_key = os.environ.get('SPACES_SECRET_KEY')
    spaces_bucket = os.environ.get('SPACES_BUCKET_NAME')
    
    if all([spaces_endpoint, spaces_region, spaces_access_key, spaces_secret_key, spaces_bucket]):
        try:
            logger.info("Creating Spaces storage backend")
            return SpacesStorageBackend(
                endpoint_url=spaces_endpoint,
                region=spaces_region,
                access_key=spaces_access_key,
                secret_key=spaces_secret_key,
                bucket_name=spaces_bucket
            )
        except Exception as e:
            logger.warning(f"Failed to create Spaces backend, falling back to local: {str(e)}")
    
    # Fall back to local storage
    upload_folder = os.environ.get('UPLOAD_FOLDER', 'uploads')
    base_url = os.environ.get('UPLOAD_BASE_URL', 'http://localhost:5000/uploads')
    
    logger.info("Creating local storage backend")
    return LocalStorageBackend(base_path=upload_folder, base_url=base_url)