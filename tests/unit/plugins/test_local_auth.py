"""Unit tests for local authentication plugin."""

import pytest
import json
import hashlib
from pathlib import Path

from app.plugins.auth.local_auth import LocalAuthPlugin
from app.jwt_handler import init_jwt_handler


class TestLocalAuthPlugin:
    """Tests for local authentication plugin."""

    @pytest.fixture(autouse=True)
    def setup_jwt_handler(self):
        """Initialize JWT handler before each test."""
        init_jwt_handler("test-secret-key-for-auth-tests")

    @pytest.fixture
    def users_file(self, temp_dir):
        """Create a temporary users file."""
        users_data = {
            "users": [
                {
                    "username": "admin",
                    "password_hash": hashlib.sha256("adminpass".encode()).hexdigest(),
                    "role": "admin",
                    "email": "admin@test.local",
                },
                {
                    "username": "user1",
                    "password_hash": hashlib.sha256("userpass".encode()).hexdigest(),
                    "role": "user",
                    "email": "user1@test.local",
                },
            ]
        }
        users_file = temp_dir / "users.json"
        users_file.write_text(json.dumps(users_data, indent=2))
        return str(users_file)

    @pytest.fixture
    def plugin(self, users_file):
        """Create plugin instance."""
        config = {"users_file": users_file, "token_expiry_hours": 24}
        return LocalAuthPlugin(config)

    @pytest.mark.unit
    def test_authenticate_valid_admin(self, plugin):
        """Test authentication with valid admin credentials."""
        result = plugin.authenticate("admin", "adminpass")

        assert result is not None
        assert "token" in result
        assert "expires_at" in result

    @pytest.mark.unit
    def test_authenticate_valid_user(self, plugin):
        """Test authentication with valid user credentials."""
        result = plugin.authenticate("user1", "userpass")

        assert result is not None
        assert "token" in result

    @pytest.mark.unit
    def test_authenticate_invalid_password(self, plugin):
        """Test authentication with invalid password."""
        result = plugin.authenticate("admin", "wrongpassword")
        assert result is None

    @pytest.mark.unit
    def test_authenticate_invalid_username(self, plugin):
        """Test authentication with invalid username."""
        result = plugin.authenticate("nonexistent", "password")
        assert result is None

    @pytest.mark.unit
    def test_authenticate_empty_credentials(self, plugin):
        """Test authentication with empty credentials."""
        result = plugin.authenticate("", "")
        assert result is None

    @pytest.mark.unit
    def test_validate_token_valid(self, plugin):
        """Test token validation with valid token."""
        auth_result = plugin.authenticate("admin", "adminpass")
        token = auth_result["token"]

        user = plugin.validate_token(token)

        assert user is not None
        assert user["username"] == "admin"
        assert user["role"] == "admin"

    @pytest.mark.unit
    def test_validate_token_invalid(self, plugin):
        """Test token validation with invalid token."""
        user = plugin.validate_token("invalid-token-12345")
        assert user is None

    @pytest.mark.unit
    def test_invalidate_token(self, plugin):
        """Test token invalidation."""
        auth_result = plugin.authenticate("admin", "adminpass")
        token = auth_result["token"]

        # Token should be valid
        assert plugin.validate_token(token) is not None

        # Invalidate token
        result = plugin.invalidate_token(token)
        assert result is True

        # Token should be invalid now
        assert plugin.validate_token(token) is None

    @pytest.mark.unit
    def test_multiple_tokens_same_user(self, plugin):
        """Test that a user can have multiple valid tokens."""
        import time

        result1 = plugin.authenticate("admin", "adminpass")
        time.sleep(0.01)  # Small delay to ensure different iat
        result2 = plugin.authenticate("admin", "adminpass")

        # Both tokens should be valid
        assert plugin.validate_token(result1["token"]) is not None
        assert plugin.validate_token(result2["token"]) is not None

    @pytest.mark.unit
    def test_missing_users_file_creates_default(self, temp_dir):
        """Test that missing users file creates default users."""
        config = {
            "users_file": str(temp_dir / "new_users.json"),
            "token_expiry_hours": 24,
        }

        # Plugin should create default users file
        plugin = LocalAuthPlugin(config)

        # Default admin user should exist with password "admin123"
        result = plugin.authenticate("admin", "admin123")
        assert result is not None
