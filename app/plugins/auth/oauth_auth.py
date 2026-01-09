"""OAuth 2.0 authentication plugin with JWT tokens."""

import secrets
import requests
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

from app.plugins.base import AuthenticationPlugin
from app.jwt_handler import get_jwt_handler


class OAuthAuthPlugin(AuthenticationPlugin):
    """Authentication plugin using OAuth 2.0 providers with JWT tokens.
    
    Supports Google, GitHub, Microsoft, and custom OAuth providers.
    Uses stateless JWT tokens for session management after OAuth authentication.
    """
    
    # Pre-configured OAuth providers
    PROVIDERS = {
        'google': {
            'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'userinfo_url': 'https://www.googleapis.com/oauth2/v3/userinfo',
            'scope': 'openid email profile',
            'username_field': 'email'
        },
        'github': {
            'authorize_url': 'https://github.com/login/oauth/authorize',
            'token_url': 'https://github.com/login/oauth/access_token',
            'userinfo_url': 'https://api.github.com/user',
            'scope': 'user:email',
            'username_field': 'login'
        },
        'microsoft': {
            'authorize_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
            'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
            'userinfo_url': 'https://graph.microsoft.com/v1.0/me',
            'scope': 'openid email profile',
            'username_field': 'userPrincipalName'
        }
    }
    
    def __init__(self, config: dict):
        """Initialize the OAuth authentication plugin.
        
        Args:
            config: Plugin configuration with:
                - provider: OAuth provider name ('google', 'github', 'microsoft', 'custom')
                - client_id: OAuth client ID
                - client_secret: OAuth client secret
                - redirect_uri: Callback URL after OAuth authorization
                - token_expiry_hours: Token validity duration (default: 24)
                - default_role: Default role for authenticated users (default: 'user')
                
                For custom provider:
                - authorize_url: Authorization endpoint URL
                - token_url: Token endpoint URL
                - userinfo_url: User info endpoint URL
                - scope: OAuth scopes (space-separated)
                - username_field: Field name for username in userinfo response
        """
        super().__init__(config)
        
        self.provider = config.get('provider', 'google')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.redirect_uri = config.get('redirect_uri')
        self.token_expiry_hours = config.get('token_expiry_hours', 24)
        self.default_role = config.get('default_role', 'user')
        
        # Get provider configuration
        if self.provider in self.PROVIDERS:
            provider_config = self.PROVIDERS[self.provider]
            self.authorize_url = config.get('authorize_url', provider_config['authorize_url'])
            self.token_url = config.get('token_url', provider_config['token_url'])
            self.userinfo_url = config.get('userinfo_url', provider_config['userinfo_url'])
            self.scope = config.get('scope', provider_config['scope'])
            self.username_field = config.get('username_field', provider_config['username_field'])
        else:
            # Custom provider
            self.authorize_url = config.get('authorize_url')
            self.token_url = config.get('token_url')
            self.userinfo_url = config.get('userinfo_url')
            self.scope = config.get('scope', 'openid email profile')
            self.username_field = config.get('username_field', 'email')
        
        # Active tokens storage (in production, use Redis or database)
        self._active_tokens = {}
        # OAuth state storage for CSRF protection
        self._oauth_states = {}
    
    def get_authorization_url(self, state: Optional[str] = None) -> dict:
        """Generate OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Dict with 'url' and 'state' keys
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Store state for validation
        self._oauth_states[state] = {
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=10)
        }
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'response_type': 'code',
            'state': state
        }
        
        # Add provider-specific parameters
        if self.provider == 'google':
            params['access_type'] = 'offline'
            params['prompt'] = 'select_account'
        
        url = f"{self.authorize_url}?{urlencode(params)}"
        
        return {
            'url': url,
            'state': state
        }
    
    def exchange_code(self, code: str, state: str) -> Optional[dict]:
        """Exchange authorization code for tokens.
        
        Args:
            code: Authorization code from OAuth provider
            state: State parameter for CSRF validation
            
        Returns:
            Dict with 'token', 'expires_at', 'username' if successful, None otherwise
        """
        # Validate state
        state_data = self._oauth_states.get(state)
        if not state_data:
            return None
        
        if datetime.utcnow() > state_data['expires_at']:
            del self._oauth_states[state]
            return None
        
        # Clean up used state
        del self._oauth_states[state]
        
        try:
            # Exchange code for access token
            token_response = requests.post(
                self.token_url,
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code,
                    'redirect_uri': self.redirect_uri,
                    'grant_type': 'authorization_code'
                },
                headers={
                    'Accept': 'application/json'
                },
                timeout=30
            )
            
            if token_response.status_code != 200:
                return None
            
            token_data = token_response.json()
            oauth_access_token = token_data.get('access_token')
            
            if not oauth_access_token:
                return None
            
            # Get user info
            userinfo_response = requests.get(
                self.userinfo_url,
                headers={
                    'Authorization': f'Bearer {oauth_access_token}',
                    'Accept': 'application/json'
                },
                timeout=30
            )
            
            if userinfo_response.status_code != 200:
                return None
            
            userinfo = userinfo_response.json()
            username = userinfo.get(self.username_field)
            
            if not username:
                # Try common fallback fields
                username = userinfo.get('email') or userinfo.get('login') or userinfo.get('sub')
            
            if not username:
                return None
            
            # Generate JWT token using the global JWT handler
            jwt_handler = get_jwt_handler()
            if not jwt_handler:
                raise RuntimeError("JWT handler not initialized")
            
            result = jwt_handler.generate_auth_token(
                username=username,
                role=self.default_role,
                expires_in_hours=self.token_expiry_hours,
                extra_claims={
                    'oauth_provider': self.provider
                }
            )
            
            result['username'] = username
            return result
            
        except requests.RequestException:
            return None
    
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user (OAuth flow - returns authorization URL).
        
        For OAuth, the 'password' parameter is ignored. Instead, this method
        returns information needed to initiate the OAuth flow.
        
        If username is 'oauth_callback' and password contains 'code:state',
        it will attempt to exchange the authorization code.
        
        Args:
            username: Use 'oauth_callback' for code exchange, or any value for auth URL
            password: For callback: 'code:state', otherwise ignored
            
        Returns:
            Dict with 'auth_url' and 'state' for initiating OAuth,
            or Dict with 'token' and 'expires_at' for code exchange
        """
        # Check if this is a callback with authorization code
        if username == 'oauth_callback' and ':' in password:
            parts = password.split(':', 1)
            if len(parts) == 2:
                code, state = parts
                return self.exchange_code(code, state)
        
        # Return authorization URL for OAuth flow
        auth_data = self.get_authorization_url()
        return {
            'requires_oauth': True,
            'auth_url': auth_data['url'],
            'state': auth_data['state'],
            'provider': self.provider
        }
    
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
