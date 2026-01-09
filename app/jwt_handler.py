"""JWT Handler for Authentication and Document Access Tokens.

This module provides functionality to generate and validate JWT tokens for:
1. Authentication Tokens (AT): Used for API authentication after login
2. Document Access Tokens (DAT): Used for secure document access

All tokens are JWT-based, providing:
- Self-contained: No need for server-side token storage
- Stateless: Enables horizontal scaling without session synchronization
- Secure: Cryptographically signed with server secret
- Configurable expiration: Different validity for auth and document access
- Revocation support: Via token blacklist for logout
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Set


class JWTHandler:
    """Handler for JWT-based Authentication and Document Access Tokens."""
    
    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        """Initialize the JWT handler.
        
        Args:
            secret_key: The secret key used for signing tokens
            algorithm: The JWT algorithm to use (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        # Blacklist for revoked tokens (for logout functionality)
        self._revoked_tokens: Set[str] = set()
    
    def generate_auth_token(
        self,
        username: str,
        role: str = 'user',
        expires_in_hours: int = 24,
        extra_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a JWT Authentication Token (AT).
        
        Args:
            username: The authenticated username
            role: User role (default: 'user')
            expires_in_hours: Token validity duration in hours (default: 24)
            extra_claims: Additional claims to include in the token
            
        Returns:
            Dict with 'token' and 'expires_at' keys
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=expires_in_hours)
        
        payload = {
            # Standard JWT claims
            'iat': now,  # Issued at
            'exp': expires_at,  # Expiration
            'nbf': now,  # Not valid before
            
            # User claims
            'sub': username,  # Subject (user)
            'role': role,  # User role
            
            # Token type identifier
            'type': 'at'  # Authentication Token
        }
        
        # Add extra claims if provided
        if extra_claims:
            payload.update(extra_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return {
            'token': token,
            'expires_at': expires_at.isoformat() + 'Z'
        }
    
    def validate_auth_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a JWT Authentication Token (AT).
        
        Args:
            token: The JWT token to validate
            
        Returns:
            Dict with user info if valid, None otherwise
        """
        # Check if token is revoked
        if token in self._revoked_tokens:
            return None
        
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verify it's an Authentication Token
            if payload.get('type') != 'at':
                return None
            
            return {
                'username': payload.get('sub'),
                'role': payload.get('role', 'user'),
                'expires_at': datetime.utcfromtimestamp(payload.get('exp')),
                'issued_at': datetime.utcfromtimestamp(payload.get('iat'))
            }
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token (for logout).
        
        Note: In production, use Redis or database for distributed revocation.
        
        Args:
            token: The JWT token to revoke
            
        Returns:
            True if successful
        """
        self._revoked_tokens.add(token)
        return True
    
    def is_token_revoked(self, token: str) -> bool:
        """Check if a token has been revoked.
        
        Args:
            token: The JWT token to check
            
        Returns:
            True if revoked, False otherwise
        """
        return token in self._revoked_tokens
    
    def cleanup_revoked_tokens(self):
        """Remove expired tokens from the revocation list.
        
        Call this periodically to prevent memory growth.
        """
        valid_revoked = set()
        for token in self._revoked_tokens:
            expiry = self.get_token_expiry(token)
            if expiry and expiry > datetime.utcnow():
                valid_revoked.add(token)
        self._revoked_tokens = valid_revoked
    
    def generate_document_token(
        self,
        temp_document_id: str,
        document_id: str,
        username: str,
        expires_in_seconds: int = 7200,
        hide_annotations_tools: bool = False,
        hide_annotations: bool = False,
        hide_logo: bool = False
    ) -> str:
        """Generate a Document Access Token (DAT).
        
        The DAT contains all information needed to access a specific document
        without requiring additional authentication token validation.
        
        Args:
            temp_document_id: The temporary document ID (cache reference)
            document_id: The original document ID
            username: The authenticated username
            expires_in_seconds: Token validity duration (default: 2 hours)
            hide_annotations_tools: Whether to hide annotation tools
            hide_annotations: Whether to hide existing annotations
            hide_logo: Whether to hide the logo
            
        Returns:
            Encoded JWT token string
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=expires_in_seconds)
        
        payload = {
            # Standard JWT claims
            'iat': now,  # Issued at
            'exp': expires_at,  # Expiration
            'nbf': now,  # Not valid before
            
            # Document access claims
            'sub': username,  # Subject (user)
            'tid': temp_document_id,  # Temp document ID
            'did': document_id,  # Document ID
            
            # View options
            'hat': hide_annotations_tools,  # Hide annotation tools
            'ha': hide_annotations,  # Hide annotations
            'hl': hide_logo,  # Hide logo
            
            # Token type identifier
            'type': 'dat'  # Document Access Token
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_document_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a Document Access Token (DAT).
        
        Args:
            token: The JWT token to validate
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verify it's a Document Access Token
            if payload.get('type') != 'dat':
                return None
            
            # Return structured data
            return {
                'temp_document_id': payload.get('tid'),
                'document_id': payload.get('did'),
                'username': payload.get('sub'),
                'expires_at': datetime.utcfromtimestamp(payload.get('exp')),
                'issued_at': datetime.utcfromtimestamp(payload.get('iat')),
                'hide_annotations_tools': payload.get('hat', False),
                'hide_annotations': payload.get('ha', False),
                'hide_logo': payload.get('hl', False)
            }
            
        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.InvalidTokenError:
            # Token is invalid
            return None
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """Get the expiration time of a token without full validation.
        
        Args:
            token: The JWT token
            
        Returns:
            Expiration datetime if token is decodable, None otherwise
        """
        try:
            # Decode without verification to get expiry
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            exp = payload.get('exp')
            if exp:
                return datetime.utcfromtimestamp(exp)
            return None
        except Exception:
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """Check if a token is expired.
        
        Args:
            token: The JWT token
            
        Returns:
            True if expired, False if still valid
        """
        expiry = self.get_token_expiry(token)
        if expiry is None:
            return True
        return datetime.utcnow() > expiry


# Singleton instance (initialized in app factory)
_jwt_handler: Optional[JWTHandler] = None


def init_jwt_handler(secret_key: str) -> JWTHandler:
    """Initialize the global JWT handler.
    
    Args:
        secret_key: The secret key for signing tokens
        
    Returns:
        The initialized JWTHandler instance
    """
    global _jwt_handler
    _jwt_handler = JWTHandler(secret_key)
    return _jwt_handler


def get_jwt_handler() -> Optional[JWTHandler]:
    """Get the global JWT handler instance.
    
    Returns:
        The JWTHandler instance or None if not initialized
    """
    return _jwt_handler
