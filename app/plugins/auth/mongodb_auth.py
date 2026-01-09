"""MongoDB authentication plugin with JWT tokens."""

import hashlib
from datetime import datetime, timedelta
from typing import Optional

from app.plugins.base import AuthenticationPlugin
from app.jwt_handler import get_jwt_handler

# Try to import pymongo
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, OperationFailure
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False


class MongoDBAuthPlugin(AuthenticationPlugin):
    """Authentication plugin using MongoDB for user storage with JWT tokens.
    
    Requires: pip install pymongo
    
    This plugin stores users in MongoDB and uses stateless JWT tokens
    for authentication. Token revocation is tracked in MongoDB for
    logout functionality across distributed instances.
    """
    
    def __init__(self, config: dict):
        """Initialize the MongoDB authentication plugin.
        
        Args:
            config: Plugin configuration with:
                - connection_string: MongoDB connection URI (default: mongodb://localhost:27017)
                - database: Database name (default: openmark)
                - users_collection: Users collection name (default: users)
                - revoked_tokens_collection: Revoked tokens collection (default: revoked_tokens)
                - token_expiry_hours: Token validity duration (default: 24)
                - create_indexes: Auto-create indexes on startup (default: True)
                
        User document schema:
            {
                "username": "string",
                "password_hash": "sha256 hash",
                "role": "user|admin",
                "email": "string (optional)",
                "created_at": "datetime",
                "updated_at": "datetime",
                "active": true|false
            }
        """
        super().__init__(config)
        
        if not PYMONGO_AVAILABLE:
            raise ImportError(
                "MongoDB authentication plugin requires pymongo. "
                "Install it with: pip install pymongo"
            )
        
        self.connection_string = config.get('connection_string', 'mongodb://localhost:27017')
        self.database_name = config.get('database', 'openmark')
        self.users_collection_name = config.get('users_collection', 'users')
        self.revoked_tokens_collection_name = config.get('revoked_tokens_collection', 'revoked_tokens')
        self.token_expiry_hours = config.get('token_expiry_hours', 24)
        self.create_indexes = config.get('create_indexes', True)
        
        # Initialize MongoDB connection
        self._client = None
        self._db = None
        self._users = None
        self._revoked_tokens = None
        
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB."""
        try:
            self._client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000
            )
            # Verify connection
            self._client.admin.command('ping')
            
            self._db = self._client[self.database_name]
            self._users = self._db[self.users_collection_name]
            self._revoked_tokens = self._db[self.revoked_tokens_collection_name]
            
            if self.create_indexes:
                self._setup_indexes()
            
            # Create default admin user if no users exist
            if self._users.count_documents({}) == 0:
                self._create_default_users()
                
        except ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    
    def _setup_indexes(self):
        """Create necessary indexes for performance."""
        # Users indexes
        self._users.create_index('username', unique=True)
        self._users.create_index('email', sparse=True)
        
        # Revoked tokens indexes (for JWT blacklist)
        self._revoked_tokens.create_index('token_hash', unique=True)
        self._revoked_tokens.create_index('expires_at', expireAfterSeconds=0)  # TTL index
    
    def _create_default_users(self):
        """Create default admin and user accounts."""
        default_users = [
            {
                'username': 'admin',
                'password_hash': self._hash_password('admin123'),
                'role': 'admin',
                'email': 'admin@example.com',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'active': True
            },
            {
                'username': 'user',
                'password_hash': self._hash_password('user123'),
                'role': 'user',
                'email': 'user@example.com',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'active': True
            }
        ]
        
        try:
            self._users.insert_many(default_users)
        except OperationFailure:
            pass  # Users might already exist
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _hash_token(self, token: str) -> str:
        """Hash a token for storage in revocation list.
        
        Args:
            token: JWT token to hash
            
        Returns:
            Hashed token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _is_token_revoked(self, token: str) -> bool:
        """Check if a token has been revoked.
        
        Args:
            token: JWT token to check
            
        Returns:
            True if revoked, False otherwise
        """
        try:
            token_hash = self._hash_token(token)
            return self._revoked_tokens.find_one({'token_hash': token_hash}) is not None
        except OperationFailure:
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user and return a JWT token.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            Dict with 'token' (JWT) and 'expires_at' if successful, None otherwise
        """
        try:
            user = self._users.find_one({
                'username': username,
                'active': True
            })
            
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
            
        except OperationFailure:
            return None
    
    def validate_token(self, token: str) -> Optional[dict]:
        """Validate a JWT authentication token.
        
        Args:
            token: The JWT authentication token
            
        Returns:
            User dict with 'username' and 'role' if valid, None otherwise
        """
        # Check if token is revoked in MongoDB
        if self._is_token_revoked(token):
            return None
        
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
        
        Stores the token hash in MongoDB for distributed revocation.
        
        Args:
            token: The JWT authentication token
            
        Returns:
            True if successful, False otherwise
        """
        try:
            jwt_handler = get_jwt_handler()
            if not jwt_handler:
                return False
            
            # Get token expiry for TTL
            expiry = jwt_handler.get_token_expiry(token)
            if not expiry:
                return False
            
            # Store token hash in revocation list
            token_hash = self._hash_token(token)
            self._revoked_tokens.insert_one({
                'token_hash': token_hash,
                'expires_at': expiry,  # TTL will auto-delete after expiry
                'revoked_at': datetime.utcnow()
            })
            
            return True
        except OperationFailure:
            return False
    
    # Additional utility methods
    
    def create_user(self, username: str, password: str, role: str = 'user', 
                    email: Optional[str] = None) -> bool:
        """Create a new user.
        
        Args:
            username: The username
            password: The password
            role: User role (default: 'user')
            email: Optional email address
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._users.insert_one({
                'username': username,
                'password_hash': self._hash_password(password),
                'role': role,
                'email': email,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'active': True
            })
            return True
        except OperationFailure:
            return False
    
    def update_password(self, username: str, new_password: str) -> bool:
        """Update a user's password.
        
        Args:
            username: The username
            new_password: The new password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._users.update_one(
                {'username': username},
                {
                    '$set': {
                        'password_hash': self._hash_password(new_password),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except OperationFailure:
            return False
    
    def deactivate_user(self, username: str) -> bool:
        """Deactivate a user account.
        
        Args:
            username: The username
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Deactivate user
            result = self._users.update_one(
                {'username': username},
                {'$set': {'active': False, 'updated_at': datetime.utcnow()}}
            )
            
            # Invalidate all tokens for this user
            self._tokens.delete_many({'username': username})
            
            return result.modified_count > 0
        except OperationFailure:
            return False
    
    def get_user(self, username: str) -> Optional[dict]:
        """Get user information.
        
        Args:
            username: The username
            
        Returns:
            User dict (without password_hash) if found, None otherwise
        """
        try:
            user = self._users.find_one(
                {'username': username},
                {'password_hash': 0}  # Exclude password hash
            )
            if user:
                user['_id'] = str(user['_id'])  # Convert ObjectId to string
            return user
        except OperationFailure:
            return None
    
    def list_users(self, skip: int = 0, limit: int = 100) -> list:
        """List all users.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of user dicts (without password_hash)
        """
        try:
            users = list(self._users.find(
                {},
                {'password_hash': 0}
            ).skip(skip).limit(limit))
            
            for user in users:
                user['_id'] = str(user['_id'])
            
            return users
        except OperationFailure:
            return []
    
    def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
