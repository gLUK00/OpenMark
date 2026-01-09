"""Local file-based authentication plugin with JWT tokens."""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from app.plugins.base import AuthenticationPlugin
from app.jwt_handler import get_jwt_handler


class LocalAuthPlugin(AuthenticationPlugin):
    """Authentication plugin using local JSON file for user storage with JWT tokens.
    
    This plugin uses stateless JWT tokens for authentication, eliminating
    the need for server-side token storage. The user database is still
    stored in a local JSON file.
    """
    
    def __init__(self, config: dict):
        """Initialize the local authentication plugin.
        
        Args:
            config: Plugin configuration with 'users_file' and 'token_expiry_hours'
        """
        super().__init__(config)
        self.users_file = config.get('users_file', './data/users.json')
        self.token_expiry_hours = config.get('token_expiry_hours', 24)
        self._users = self._load_users()
    
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
    
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user and return a JWT token.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            Dict with 'token' (JWT) and 'expires_at' if successful, None otherwise
        """
        user = self._users.get(username)
        
        if not user:
            return None
        
        password_hash = self._hash_password(password)
        
        if user['password_hash'] != password_hash:
            return None
        
        # Generate JWT token using the global JWT handler
        jwt_handler = get_jwt_handler()
        if not jwt_handler:
            raise RuntimeError("JWT handler not initialized")
        
        return jwt_handler.generate_auth_token(
            username=username,
            role=user.get('role', 'user'),
            expires_in_hours=self.token_expiry_hours
        )
    
    def validate_token(self, token: str) -> Optional[dict]:
        """Validate a JWT authentication token.
        
        Args:
            token: The JWT authentication token
            
        Returns:
            User dict with 'username' and 'role' if valid, None otherwise
        """
        jwt_handler = get_jwt_handler()
        if not jwt_handler:
            return None
        
        token_data = jwt_handler.validate_auth_token(token)
        
        if not token_data:
            return None
        
        return {
            'username': token_data['username'],
            'role': token_data['role']
        }
    
    def invalidate_token(self, token: str) -> bool:
        """Invalidate a JWT authentication token (revoke it).
        
        Args:
            token: The JWT authentication token
            
        Returns:
            True if successful, False otherwise
        """
        jwt_handler = get_jwt_handler()
        if not jwt_handler:
            return False
        
        return jwt_handler.revoke_token(token)
