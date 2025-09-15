"""
Storage Backend Module
Provides pluggable storage backends for file uploads and document management.
"""

import os
from abc import ABC, abstractmethod
from urllib.parse import urljoin
from werkzeug.utils import secure_filename


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    def save_file(self, file, filename=None, folder=None):
        """
        Save a file and return the path and URL
        
        Args:
            file: File object to save
            filename: Optional custom filename 
            folder: Optional subfolder within storage
            
        Returns:
            tuple: (relative_path, public_url)
        """
        pass
    
    @abstractmethod
    def delete_file(self, path):
        """Delete a file by path"""
        pass
    
    @abstractmethod
    def get_url(self, path):
        """Get public URL for a file path"""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend"""
    
    def __init__(self, uploads_folder='uploads', base_url='/uploads/'):
        """
        Initialize local storage backend
        
        Args:
            uploads_folder: Base folder for file uploads
            base_url: Base URL path for serving files
        """
        self.uploads_folder = uploads_folder
        self.base_url = base_url.rstrip('/') + '/'
        
        # Ensure uploads folder exists
        os.makedirs(self.uploads_folder, exist_ok=True)
    
    def save_file(self, file, filename=None, folder=None):
        """
        Save file to local filesystem
        
        Args:
            file: File object with save() method
            filename: Optional custom filename (will use file.filename if not provided)
            folder: Optional subfolder within uploads_folder
            
        Returns:
            tuple: (relative_path, public_url)
        """
        # Use provided filename or fall back to original filename
        if filename is None:
            filename = getattr(file, 'filename', 'upload')
        
        # Secure the filename
        filename = secure_filename(filename)
        if not filename:
            filename = 'upload'
        
        # Create subfolder if specified
        save_folder = self.uploads_folder
        if folder:
            folder = secure_filename(folder)
            save_folder = os.path.join(self.uploads_folder, folder)
            os.makedirs(save_folder, exist_ok=True)
        
        # Create full file path
        file_path = os.path.join(save_folder, filename)
        
        # Handle filename conflicts by appending numbers
        base_name, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(file_path):
            new_filename = f"{base_name}_{counter}{ext}"
            file_path = os.path.join(save_folder, new_filename)
            filename = new_filename
            counter += 1
        
        # Save the file
        file.save(file_path)
        
        # Create relative path for storage reference
        relative_path = os.path.relpath(file_path, self.uploads_folder)
        
        # Create public URL
        public_url = urljoin(self.base_url, relative_path.replace(os.sep, '/'))
        
        return relative_path, public_url
    
    def delete_file(self, path):
        """Delete file from local filesystem"""
        full_path = os.path.join(self.uploads_folder, path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    
    def get_url(self, path):
        """Get public URL for a file path"""
        return urljoin(self.base_url, path.replace(os.sep, '/'))


class DigitalOceanSpacesBackend(StorageBackend):
    """DigitalOcean Spaces (S3-compatible) storage backend"""
    
    def __init__(self, access_key=None, secret_key=None, bucket=None, region='nyc3', endpoint_url=None):
        """
        Initialize DigitalOcean Spaces backend
        
        Args:
            access_key: Spaces access key
            secret_key: Spaces secret key  
            bucket: Spaces bucket name
            region: Spaces region
            endpoint_url: Custom endpoint URL (auto-generated if not provided)
        """
        self.access_key = access_key or os.environ.get('DO_SPACES_KEY')
        self.secret_key = secret_key or os.environ.get('DO_SPACES_SECRET')
        self.bucket = bucket or os.environ.get('DO_SPACES_BUCKET')
        self.region = region or os.environ.get('DO_SPACES_REGION', 'nyc3')
        
        if endpoint_url:
            self.endpoint_url = endpoint_url
        else:
            self.endpoint_url = f"https://{self.region}.digitaloceanspaces.com"
        
        self.base_url = f"https://{self.bucket}.{self.region}.digitaloceanspaces.com/"
        
        # Initialize boto3 client if credentials are available
        self.client = None
        if self.access_key and self.secret_key and self.bucket:
            try:
                import boto3
                self.client = boto3.client(
                    's3',
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
            except ImportError:
                raise ImportError("boto3 is required for DigitalOcean Spaces backend. Install with: pip install boto3")
    
    def save_file(self, file, filename=None, folder=None):
        """
        Save file to DigitalOcean Spaces
        
        Args:
            file: File object to upload
            filename: Optional custom filename
            folder: Optional folder prefix
            
        Returns:
            tuple: (object_key, public_url)
        """
        if not self.client:
            raise RuntimeError("DigitalOcean Spaces client not configured. Check credentials.")
        
        # Use provided filename or fall back to original filename
        if filename is None:
            filename = getattr(file, 'filename', 'upload')
        
        # Secure the filename
        filename = secure_filename(filename)
        if not filename:
            filename = 'upload'
        
        # Create object key with optional folder prefix
        object_key = filename
        if folder:
            folder = secure_filename(folder)
            object_key = f"{folder}/{filename}"
        
        # Upload to Spaces
        self.client.upload_fileobj(
            file,
            self.bucket,
            object_key,
            ExtraArgs={'ACL': 'public-read'}
        )
        
        # Create public URL
        public_url = urljoin(self.base_url, object_key)
        
        return object_key, public_url
    
    def delete_file(self, path):
        """Delete file from DigitalOcean Spaces"""
        if not self.client:
            return False
        
        try:
            self.client.delete_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False
    
    def get_url(self, path):
        """Get public URL for a file path"""
        return urljoin(self.base_url, path)


def create_storage_backend(backend_type=None):
    """
    Factory function to create storage backend
    
    Args:
        backend_type: Type of backend ('local' or 'spaces'). Auto-detected if None.
        
    Returns:
        StorageBackend: Configured storage backend instance
    """
    # Auto-detect backend type if not specified
    if backend_type is None:
        # Use Spaces if DO credentials are available
        if (os.environ.get('DO_SPACES_KEY') and 
            os.environ.get('DO_SPACES_SECRET') and 
            os.environ.get('DO_SPACES_BUCKET')):
            backend_type = 'spaces'
        else:
            backend_type = 'local'
    
    if backend_type == 'local':
        uploads_folder = os.environ.get('UPLOAD_FOLDER', 'uploads')
        return LocalStorageBackend(uploads_folder=uploads_folder)
    
    elif backend_type == 'spaces':
        return DigitalOceanSpacesBackend()
    
    else:
        raise ValueError(f"Unknown storage backend type: {backend_type}")


# Global storage backend instance (initialized on first use)
_storage_backend = None

def get_storage_backend():
    """Get the configured storage backend instance"""
    global _storage_backend
    if _storage_backend is None:
        _storage_backend = create_storage_backend()
    return _storage_backend