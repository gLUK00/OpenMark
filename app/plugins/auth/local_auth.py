"""Local file-based authentication plugin."""

import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from app.plugins.base import AuthenticationPlugin


class LocalAuthPlugin(AuthenticationPlugin):
    """Authentication plugin using local JSON file for user storage."""
    
    def __init__(self, config: dict):
        """Initialize the local authentication plugin.
        
        Args:
            config: Plugin configuration with 'users_file' and 'token_expiry_hours'
        """
        super().__init__(config)
        self.users_file = config.get('users_file', './data/users.json')
        self.token_expiry_hours = config.get('token_expiry_hours', 24)
        self._users = self._load_users()
        self._active_tokens = {}
    
    def _load_users(self) -> dict:
        """Load users from JSON file.
        
        Returns:
            Dictionary of users
        """
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {u['username']: u for u in data.get('users', [])}
            except (json.JSONDecodeError, IOError):
                pass
        
        # Create default users file if it doesn't exist
        self._create_default_users_file()
        return self._load_users() if os.path.exists(self.users_file) else {}
    
    def _create_default_users_file(self):
        """Create a default users file with an admin user."""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        
        default_users = {
            "users": [
                {
                    "username": "admin",
                    "password_hash": self._hash_password("admin123"),
                    "role": "admin"
                },
                {
                    "username": "user",
                    "password_hash": self._hash_password("user123"),
                    "role": "user"
                }
            ]
        }
        
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(default_users, f, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_token(self) -> str:
        """Generate a secure random token.
        
        Returns:
            Random token string
        """
        return secrets.token_urlsafe(32)
    
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            Dict with 'token' and 'expires_at' if successful, None otherwise
        """
        user = self._users.get(username)
        
        if not user:
            return None
        
        password_hash = self._hash_password(password)
        
        if user['password_hash'] != password_hash:
            return None
        
        # Generate token
        token = self._generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
        
        # Store token
        self._active_tokens[token] = {
            'username': username,
            'role': user.get('role', 'user'),
            'expires_at': expires_at
        }
        
        return {
            'token': token,
            'expires_at': expires_at.isoformat() + 'Z'
        }
    
    def validate_token(self, token: str) -> Optional[dict]:
        """Validate an authentication token.
        
        Args:
            token: The authentication token
            
        Returns:
            User dict if valid, None otherwise
        """
        token_data = self._active_tokens.get(token)
        
        if not token_data:
            return None
        
        # Check expiration
        if datetime.utcnow() > token_data['expires_at']:
            del self._active_tokens[token]
            return None
        
        return {
            'username': token_data['username'],
            'role': token_data['role']
        }
    
    def invalidate_token(self, token: str) -> bool:
        """Invalidate an authentication token.
        
        Args:
            token: The authentication token
            
        Returns:
            True if successful, False otherwise
        """
        if token in self._active_tokens:
            del self._active_tokens[token]
            return True
        return False
