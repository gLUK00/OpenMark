"""Unit tests for JWT handler."""

import pytest
import time
from datetime import datetime, timedelta

from app.jwt_handler import JWTHandler, init_jwt_handler, get_jwt_handler


class TestJWTHandler:
    """Tests for JWT handler functionality."""

    @pytest.fixture
    def jwt_handler(self):
        """Create a JWT handler instance."""
        return JWTHandler("test-secret-key")

    @pytest.mark.unit
    def test_generate_auth_token(self, jwt_handler):
        """Test creating an authentication token."""
        result = jwt_handler.generate_auth_token(username="testuser", role="user")

        assert result is not None
        assert "token" in result
        assert "expires_at" in result
        assert isinstance(result["token"], str)
        assert len(result["token"]) > 0

    @pytest.mark.unit
    def test_validate_auth_token(self, jwt_handler):
        """Test validating an authentication token."""
        result = jwt_handler.generate_auth_token(username="testuser", role="admin")
        token = result["token"]

        validated = jwt_handler.validate_auth_token(token)

        assert validated is not None
        assert validated["username"] == "testuser"
        assert validated["role"] == "admin"

    @pytest.mark.unit
    def test_generate_document_token(self, jwt_handler):
        """Test creating a document access token."""
        token = jwt_handler.generate_document_token(
            temp_document_id="temp_abc123", document_id="doc123", username="testuser"
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.unit
    def test_validate_document_token(self, jwt_handler):
        """Test validating a document access token."""
        token = jwt_handler.generate_document_token(
            temp_document_id="temp_abc123", document_id="doc123", username="testuser"
        )

        result = jwt_handler.validate_document_token(token)

        assert result is not None
        assert result["username"] == "testuser"
        assert result["document_id"] == "doc123"
        assert result["temp_document_id"] == "temp_abc123"

    @pytest.mark.unit
    def test_validate_invalid_token(self, jwt_handler):
        """Test validating an invalid token."""
        result = jwt_handler.validate_document_token("invalid-token")
        assert result is None

    @pytest.mark.unit
    def test_validate_expired_token(self, jwt_handler):
        """Test validating an expired token."""
        # Create token with very short expiry (1 second)
        token = jwt_handler.generate_document_token(
            temp_document_id="temp_abc123",
            document_id="doc123",
            username="testuser",
            expires_in_seconds=1,
        )

        # Wait for token to expire
        time.sleep(2)

        result = jwt_handler.validate_document_token(token)
        assert result is None

    @pytest.mark.unit
    def test_token_contains_view_options(self, jwt_handler):
        """Test that token contains view options."""
        token = jwt_handler.generate_document_token(
            temp_document_id="temp_abc123",
            document_id="doc123",
            username="testuser",
            hide_annotations=True,
            hide_annotations_tools=True,
            hide_logo=True,
        )

        result = jwt_handler.validate_document_token(token)

        assert result is not None
        assert result.get("hide_annotations") is True
        assert result.get("hide_annotations_tools") is True
        assert result.get("hide_logo") is True

    @pytest.mark.unit
    def test_init_jwt_handler(self):
        """Test initializing JWT handler singleton."""
        handler = init_jwt_handler("another-secret")
        assert handler is not None

        # Should return same instance
        handler2 = get_jwt_handler()
        assert handler2 is handler

    @pytest.mark.unit
    def test_different_secrets_produce_different_tokens(self):
        """Test that different secrets produce different tokens."""
        handler1 = JWTHandler("secret1")
        handler2 = JWTHandler("secret2")

        token1 = handler1.generate_document_token(
            temp_document_id="temp1", document_id="doc1", username="user1"
        )
        token2 = handler2.generate_document_token(
            temp_document_id="temp1", document_id="doc1", username="user1"
        )

        assert token1 != token2

    @pytest.mark.unit
    def test_token_validation_with_wrong_secret(self):
        """Test that token cannot be validated with wrong secret."""
        handler1 = JWTHandler("secret1")
        handler2 = JWTHandler("secret2")

        token = handler1.generate_document_token(
            temp_document_id="temp1", document_id="doc1", username="user1"
        )

        # Should fail validation with different secret
        result = handler2.validate_document_token(token)
        assert result is None

    @pytest.mark.unit
    def test_revoke_token(self, jwt_handler):
        """Test token revocation (logout)."""
        result = jwt_handler.generate_auth_token(username="testuser")
        token = result["token"]

        # Token should be valid before revocation
        assert jwt_handler.validate_auth_token(token) is not None

        # Revoke the token
        jwt_handler.revoke_token(token)

        # Token should be invalid after revocation
        assert jwt_handler.validate_auth_token(token) is None

    @pytest.mark.unit
    def test_is_token_revoked(self, jwt_handler):
        """Test checking if token is revoked."""
        result = jwt_handler.generate_auth_token(username="testuser")
        token = result["token"]

        assert jwt_handler.is_token_revoked(token) is False

        jwt_handler.revoke_token(token)

        assert jwt_handler.is_token_revoked(token) is True

    @pytest.mark.unit
    def test_auth_token_with_extra_claims(self, jwt_handler):
        """Test authentication token with extra claims."""
        result = jwt_handler.generate_auth_token(
            username="testuser",
            role="admin",
            extra_claims={"department": "IT", "level": 5},
        )

        assert result is not None
        assert "token" in result
