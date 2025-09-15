#!/usr/bin/env python3
"""
Database Utilities for ERP System
Functions for database URL masking and validation
"""

import re
from urllib.parse import urlparse, urlunparse


def mask_db_uri(database_uri):
    """Mask sensitive information in database URI for logging/display
    
    Args:
        database_uri (str): Database connection URI
        
    Returns:
        str: Masked database URI with credentials hidden
    """
    if not database_uri:
        return "Not configured"
    
    try:
        parsed = urlparse(database_uri)
        
        # For SQLite URIs, handle special cases
        if parsed.scheme == 'sqlite':
            if parsed.path == ':memory:':
                return "sqlite:///:memory:"
            else:
                # Show relative path but mask absolute paths
                path = parsed.path
                if path and path.startswith('/') and '/' in path[1:]:
                    # Extract just the filename for absolute paths with directories
                    filename = path.split('/')[-1]
                    return f"sqlite:///{filename}"
                return f"sqlite://{path}"
        
        # For other databases, mask credentials
        if parsed.username or parsed.password:
            # Replace username and password with masked values
            username = '***masked***' if parsed.username else ''
            password = '***masked***' if parsed.password else ''
            
            # Reconstruct netloc with masked credentials
            if username and password:
                netloc = f"{username}:{password}@{parsed.hostname}"
            elif username:
                netloc = f"{username}@{parsed.hostname}"
            else:
                netloc = parsed.hostname
                
            if parsed.port:
                netloc += f":{parsed.port}"
            
            # Reconstruct URL
            masked = urlunparse((
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            return masked
        else:
            # No credentials to mask
            return database_uri
            
    except Exception:
        # If parsing fails, return a generic masked version
        return "***invalid_or_unparseable_uri***"


def is_valid_prod_db_url(database_uri):
    """Validate if database URI is suitable for production use
    
    Args:
        database_uri (str): Database connection URI
        
    Returns:
        bool: True if URI is production-ready, False otherwise
    """
    if not database_uri:
        return False
    
    try:
        parsed = urlparse(database_uri)
        
        # SQLite is not suitable for production (except in-memory for testing)
        if parsed.scheme == 'sqlite':
            return False
        
        # Must be a recognized database scheme
        valid_schemes = {
            'postgresql', 'postgres', 'mysql', 'oracle', 'mssql',
            'mysql+pymysql', 'postgresql+psycopg2', 'oracle+cx_oracle'
        }
        
        if parsed.scheme not in valid_schemes:
            return False
        
        # Must have hostname (not localhost/127.0.0.1 for production)
        if not parsed.hostname:
            return False
            
        # Localhost indicators suggest non-production
        localhost_indicators = {'localhost', '127.0.0.1', '0.0.0.0', '::1'}
        if parsed.hostname.lower() in localhost_indicators:
            return False
        
        # Must have credentials for production databases
        if not parsed.username or not parsed.password:
            return False
        
        # Must have database name
        if not parsed.path or parsed.path == '/':
            return False
        
        # Additional validation for PostgreSQL (most common in production)
        if parsed.scheme in ['postgresql', 'postgres', 'postgresql+psycopg2']:
            # Should have proper port (default PostgreSQL port or custom)
            if parsed.port and parsed.port not in [5432, 5433, 5434, 5435]:
                # Allow custom ports but warn if suspicious
                if parsed.port < 1024 or parsed.port > 65535:
                    return False
        
        return True
        
    except Exception:
        return False


def get_database_info(database_uri):
    """Extract database information for health checks
    
    Args:
        database_uri (str): Database connection URI
        
    Returns:
        dict: Database information including type, host, port, database name
    """
    if not database_uri:
        return {
            'type': 'unknown',
            'host': 'unknown',
            'port': None,
            'database': 'unknown',
            'is_production_ready': False
        }
    
    try:
        parsed = urlparse(database_uri)
        
        # Determine database type
        db_type_map = {
            'sqlite': 'SQLite',
            'postgresql': 'PostgreSQL',
            'postgres': 'PostgreSQL',
            'postgresql+psycopg2': 'PostgreSQL',
            'mysql': 'MySQL',
            'mysql+pymysql': 'MySQL',
            'oracle': 'Oracle',
            'oracle+cx_oracle': 'Oracle',
            'mssql': 'SQL Server'
        }
        
        db_type = db_type_map.get(parsed.scheme, 'Unknown')
        
        # Extract database name
        database_name = 'unknown'
        if parsed.path:
            if parsed.scheme == 'sqlite':
                # For SQLite, extract filename from path
                path = parsed.path.strip('/')
                if path and path != ':memory:':
                    database_name = path.split('/')[-1] if '/' in path else path
            else:
                # For other databases, remove leading slash and get first path component
                path_parts = parsed.path.lstrip('/').split('/')
                if path_parts and path_parts[0]:
                    database_name = path_parts[0]
        
        return {
            'type': db_type,
            'host': parsed.hostname or 'unknown',
            'port': parsed.port,
            'database': database_name,
            'is_production_ready': is_valid_prod_db_url(database_uri)
        }
        
    except Exception:
        return {
            'type': 'unknown',
            'host': 'unknown',
            'port': None,
            'database': 'unknown',
            'is_production_ready': False
        }