"""Integration tests for MongoDB authentication plugin."""

import os
import pytest

# Skip all tests if MongoDB is not available
pytestmark = pytest.mark.skipif(
    os.environ.get("MONGODB_TEST_URL") is None,
    reason="MongoDB not available for testing",
)


class TestMongoDBAuthPlugin:
    """Tests for MongoDB authentication plugin."""

    @pytest.fixture
    def mongodb_config(self):
        """Get MongoDB configuration from environment."""
        return {
            "connection_string": os.environ.get(
                "MONGODB_TEST_URL", "mongodb://test:testpassword@localhost:27017/"
            ),
            "database": "openmark_test",
            "users_collection": "test_users",
            "token_expiry_hours": 24,
        }

    @pytest.fixture
    def plugin(self, mongodb_config):
        """Create MongoDB auth plugin instance."""
        from app.plugins.auth.mongodb_auth import MongoDBAuthPlugin

        plugin = MongoDBAuthPlugin(mongodb_config)

        # Setup: Create test users
        import hashlib

        plugin.collection.delete_many({})  # Clean collection
        plugin.collection.insert_many(
            [
                {
                    "username": "testadmin",
                    "password_hash": hashlib.sha256("adminpass".encode()).hexdigest(),
                    "role": "admin",
                    "email": "admin@test.local",
                },
                {
                    "username": "testuser",
                    "password_hash": hashlib.sha256("userpass".encode()).hexdigest(),
                    "role": "user",
                    "email": "user@test.local",
                },
            ]
        )

        yield plugin

        # Cleanup
        plugin.collection.delete_many({})

    @pytest.mark.integration
    @pytest.mark.docker
    def test_authenticate_valid(self, plugin):
        """Test authentication with valid credentials."""
        result = plugin.authenticate("testadmin", "adminpass")

        assert result is not None
        assert "token" in result
        assert "expires_at" in result

    @pytest.mark.integration
    @pytest.mark.docker
    def test_authenticate_invalid(self, plugin):
        """Test authentication with invalid credentials."""
        result = plugin.authenticate("testadmin", "wrongpass")
        assert result is None

    @pytest.mark.integration
    @pytest.mark.docker
    def test_validate_token(self, plugin):
        """Test token validation."""
        auth_result = plugin.authenticate("testadmin", "adminpass")
        user = plugin.validate_token(auth_result["token"])

        assert user is not None
        assert user["username"] == "testadmin"
        assert user["role"] == "admin"

    @pytest.mark.integration
    @pytest.mark.docker
    def test_invalidate_token(self, plugin):
        """Test token invalidation."""
        auth_result = plugin.authenticate("testuser", "userpass")
        token = auth_result["token"]

        assert plugin.validate_token(token) is not None
        assert plugin.invalidate_token(token) is True
        assert plugin.validate_token(token) is None
