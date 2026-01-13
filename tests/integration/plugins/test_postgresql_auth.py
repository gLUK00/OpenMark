"""Integration tests for PostgreSQL authentication plugin."""

import os
import pytest

# Skip all tests if PostgreSQL is not available
pytestmark = pytest.mark.skipif(
    os.environ.get("POSTGRES_TEST_URL") is None,
    reason="PostgreSQL not available for testing",
)


class TestPostgreSQLAuthPlugin:
    """Tests for PostgreSQL authentication plugin."""

    @pytest.fixture
    def postgres_config(self):
        """Get PostgreSQL configuration from environment."""
        url = os.environ.get("POSTGRES_TEST_URL", "")
        # Parse URL or use defaults
        return {
            "host": "localhost",
            "port": 5432,
            "database": "openmark_test",
            "user": "test",
            "password": "testpassword",
            "users_table": "test_users",
            "token_expiry_hours": 24,
        }

    @pytest.fixture
    def plugin(self, postgres_config):
        """Create PostgreSQL auth plugin instance."""
        from app.plugins.auth.postgresql_auth import PostgreSQLAuthPlugin

        plugin = PostgreSQLAuthPlugin(postgres_config)

        # Setup: Create table and test users
        import hashlib

        cursor = plugin.connection.cursor()

        # Create table
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {postgres_config['users_table']} (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Clear and insert test users
        cursor.execute(f"DELETE FROM {postgres_config['users_table']}")
        cursor.execute(
            f"""
            INSERT INTO {postgres_config['users_table']} (username, password_hash, role, email)
            VALUES 
                ('testadmin', %s, 'admin', 'admin@test.local'),
                ('testuser', %s, 'user', 'user@test.local')
        """,
            (
                hashlib.sha256("adminpass".encode()).hexdigest(),
                hashlib.sha256("userpass".encode()).hexdigest(),
            ),
        )
        plugin.connection.commit()

        yield plugin

        # Cleanup
        cursor.execute(f"DROP TABLE IF EXISTS {postgres_config['users_table']}")
        plugin.connection.commit()
        cursor.close()

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
