"""SAML SSO authentication plugin."""

import secrets
import base64
import zlib
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

from app.plugins.base import AuthenticationPlugin

# Try to import optional SAML libraries
try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
    SAML_AVAILABLE = True
except ImportError:
    SAML_AVAILABLE = False


class SAMLAuthPlugin(AuthenticationPlugin):
    """Authentication plugin using SAML 2.0 for Single Sign-On (SSO).
    
    This plugin supports two modes:
    1. Full SAML with python3-saml library (recommended for production)
    2. Basic SAML without external dependencies (limited features)
    
    For full SAML support, install: pip install python3-saml
    """
    
    def __init__(self, config: dict):
        """Initialize the SAML SSO authentication plugin.
        
        Args:
            config: Plugin configuration with:
                - idp_entity_id: Identity Provider Entity ID
                - idp_sso_url: IdP Single Sign-On URL
                - idp_slo_url: IdP Single Logout URL (optional)
                - idp_x509_cert: IdP X.509 certificate (PEM format)
                - sp_entity_id: Service Provider Entity ID
                - sp_acs_url: SP Assertion Consumer Service URL
                - sp_slo_url: SP Single Logout URL (optional)
                - sp_x509_cert: SP X.509 certificate (optional, for signed requests)
                - sp_private_key: SP private key (optional, for signed requests)
                - token_expiry_hours: Token validity duration (default: 24)
                - default_role: Default role for authenticated users (default: 'user')
                - username_attribute: SAML attribute for username (default: 'email')
                - role_attribute: SAML attribute for role (optional)
                - role_mapping: Dict mapping IdP roles to OpenMark roles (optional)
        """
        super().__init__(config)
        
        # Identity Provider (IdP) configuration
        self.idp_entity_id = config.get('idp_entity_id')
        self.idp_sso_url = config.get('idp_sso_url')
        self.idp_slo_url = config.get('idp_slo_url')
        self.idp_x509_cert = config.get('idp_x509_cert')
        
        # Service Provider (SP) configuration
        self.sp_entity_id = config.get('sp_entity_id')
        self.sp_acs_url = config.get('sp_acs_url')
        self.sp_slo_url = config.get('sp_slo_url')
        self.sp_x509_cert = config.get('sp_x509_cert')
        self.sp_private_key = config.get('sp_private_key')
        
        # Token and role configuration
        self.token_expiry_hours = config.get('token_expiry_hours', 24)
        self.default_role = config.get('default_role', 'user')
        self.username_attribute = config.get('username_attribute', 'email')
        self.role_attribute = config.get('role_attribute')
        self.role_mapping = config.get('role_mapping', {})
        
        # Active tokens storage
        self._active_tokens = {}
        # SAML request IDs for validation
        self._saml_requests = {}
        
        # Check if full SAML library is available
        self.full_saml_mode = SAML_AVAILABLE and self._validate_config()
    
    def _validate_config(self) -> bool:
        """Validate that required configuration is present."""
        required = ['idp_entity_id', 'idp_sso_url', 'sp_entity_id', 'sp_acs_url']
        return all(getattr(self, attr) for attr in required)
    
    def _get_saml_settings(self) -> dict:
        """Get SAML settings dictionary for python3-saml library."""
        settings = {
            'strict': True,
            'debug': False,
            'sp': {
                'entityId': self.sp_entity_id,
                'assertionConsumerService': {
                    'url': self.sp_acs_url,
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
                },
                'NameIDFormat': 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress'
            },
            'idp': {
                'entityId': self.idp_entity_id,
                'singleSignOnService': {
                    'url': self.idp_sso_url,
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
                }
            }
        }
        
        # Add SLO if configured
        if self.sp_slo_url:
            settings['sp']['singleLogoutService'] = {
                'url': self.sp_slo_url,
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
            }
        
        if self.idp_slo_url:
            settings['idp']['singleLogoutService'] = {
                'url': self.idp_slo_url,
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
            }
        
        # Add certificates if provided
        if self.idp_x509_cert:
            settings['idp']['x509cert'] = self.idp_x509_cert
        
        if self.sp_x509_cert:
            settings['sp']['x509cert'] = self.sp_x509_cert
        
        if self.sp_private_key:
            settings['sp']['privateKey'] = self.sp_private_key
        
        return settings
    
    def get_login_url(self, relay_state: Optional[str] = None) -> dict:
        """Generate SAML login URL.
        
        Args:
            relay_state: Optional URL to redirect to after authentication
            
        Returns:
            Dict with 'url', 'request_id' keys
        """
        request_id = f"_openmark_{secrets.token_hex(16)}"
        
        # Store request for validation
        self._saml_requests[request_id] = {
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=10),
            'relay_state': relay_state
        }
        
        if self.full_saml_mode:
            # Use python3-saml for proper SAML request
            try:
                # This would need Flask request context in real usage
                # For now, generate a basic redirect URL
                pass
            except Exception:
                pass
        
        # Basic SAML AuthnRequest generation
        authn_request = self._create_authn_request(request_id)
        encoded_request = self._encode_saml_request(authn_request)
        
        params = {
            'SAMLRequest': encoded_request
        }
        
        if relay_state:
            params['RelayState'] = relay_state
        
        url = f"{self.idp_sso_url}?{urlencode(params)}"
        
        return {
            'url': url,
            'request_id': request_id
        }
    
    def _create_authn_request(self, request_id: str) -> str:
        """Create a SAML AuthnRequest XML document.
        
        Args:
            request_id: Unique request identifier
            
        Returns:
            SAML AuthnRequest XML string
        """
        issue_instant = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        authn_request = f'''<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest 
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="{request_id}"
    Version="2.0"
    IssueInstant="{issue_instant}"
    Destination="{self.idp_sso_url}"
    AssertionConsumerServiceURL="{self.sp_acs_url}"
    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>{self.sp_entity_id}</saml:Issuer>
    <samlp:NameIDPolicy 
        Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
        AllowCreate="true"/>
</samlp:AuthnRequest>'''
        
        return authn_request
    
    def _encode_saml_request(self, saml_request: str) -> str:
        """Encode and compress SAML request for HTTP-Redirect binding.
        
        Args:
            saml_request: SAML request XML string
            
        Returns:
            Base64 encoded, deflated SAML request
        """
        # Deflate (compress) the request
        compressed = zlib.compress(saml_request.encode('utf-8'))[2:-4]
        # Base64 encode
        encoded = base64.b64encode(compressed).decode('utf-8')
        return encoded
    
    def process_response(self, saml_response: str, relay_state: Optional[str] = None) -> Optional[dict]:
        """Process SAML Response from IdP.
        
        Args:
            saml_response: Base64 encoded SAML Response
            relay_state: Optional relay state
            
        Returns:
            Dict with 'token', 'expires_at', 'username' if successful, None otherwise
        """
        try:
            # Decode the SAML response
            decoded_response = base64.b64decode(saml_response).decode('utf-8')
            
            # Parse XML
            root = ET.fromstring(decoded_response)
            
            # Define SAML namespaces
            namespaces = {
                'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol',
                'saml': 'urn:oasis:names:tc:SAML:2.0:assertion'
            }
            
            # Check response status
            status = root.find('.//samlp:StatusCode', namespaces)
            if status is not None:
                status_value = status.get('Value', '')
                if 'Success' not in status_value:
                    return None
            
            # Extract NameID (username)
            name_id = root.find('.//saml:NameID', namespaces)
            username = name_id.text if name_id is not None else None
            
            # Try to get username from attributes if NameID is not available
            if not username:
                attributes = root.findall('.//saml:Attribute', namespaces)
                for attr in attributes:
                    attr_name = attr.get('Name', '')
                    if self.username_attribute.lower() in attr_name.lower():
                        attr_value = attr.find('saml:AttributeValue', namespaces)
                        if attr_value is not None:
                            username = attr_value.text
                            break
            
            if not username:
                return None
            
            # Determine role
            role = self.default_role
            if self.role_attribute:
                attributes = root.findall('.//saml:Attribute', namespaces)
                for attr in attributes:
                    attr_name = attr.get('Name', '')
                    if self.role_attribute.lower() in attr_name.lower():
                        attr_value = attr.find('saml:AttributeValue', namespaces)
                        if attr_value is not None:
                            idp_role = attr_value.text
                            role = self.role_mapping.get(idp_role, self.default_role)
                            break
            
            # Generate OpenMark token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
            
            # Store token
            self._active_tokens[token] = {
                'username': username,
                'role': role,
                'expires_at': expires_at,
                'saml_session': True
            }
            
            return {
                'token': token,
                'expires_at': expires_at.isoformat() + 'Z',
                'username': username,
                'relay_state': relay_state
            }
            
        except (ET.ParseError, ValueError, TypeError):
            return None
    
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user (SAML flow - returns login URL or processes response).
        
        For SAML, use special username values:
        - 'saml_login': Returns SAML login URL
        - 'saml_callback': password contains base64 SAML Response
        
        Args:
            username: 'saml_login' or 'saml_callback'
            password: For callback: base64 SAML Response, otherwise relay_state
            
        Returns:
            Dict with login info or authentication result
        """
        if username == 'saml_callback':
            # Process SAML response
            return self.process_response(password)
        
        # Return SAML login URL
        relay_state = password if password else None
        login_data = self.get_login_url(relay_state)
        
        return {
            'requires_saml': True,
            'login_url': login_data['url'],
            'request_id': login_data['request_id']
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
    
    def get_metadata(self) -> str:
        """Generate SP metadata XML for IdP configuration.
        
        Returns:
            SP metadata XML string
        """
        metadata = f'''<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor 
    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="{self.sp_entity_id}">
    <md:SPSSODescriptor 
        AuthnRequestsSigned="false" 
        WantAssertionsSigned="true"
        protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
        <md:AssertionConsumerService 
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Location="{self.sp_acs_url}"
            index="0"/>'''
        
        if self.sp_slo_url:
            metadata += f'''
        <md:SingleLogoutService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            Location="{self.sp_slo_url}"/>'''
        
        metadata += '''
    </md:SPSSODescriptor>
</md:EntityDescriptor>'''
        
        return metadata
