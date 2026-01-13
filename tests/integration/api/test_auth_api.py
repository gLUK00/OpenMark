"""Integration tests for authentication API."""

import pytest


class TestAuthenticationAPI:
    """Tests for authentication API endpoints."""

    @pytest.mark.integration
    def test_authenticate_success(self, client):
        """Test successful authentication."""
        response = client.post(
            "/api/authenticate", json={"username": "admin", "password": "adminpassword"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "token" in data
        assert "expires_at" in data

    @pytest.mark.integration
    def test_authenticate_invalid_credentials(self, client):
        """Test authentication with invalid credentials."""
        response = client.post(
            "/api/authenticate", json={"username": "admin", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.integration
    def test_authenticate_missing_username(self, client):
        """Test authentication with missing username."""
        response = client.post("/api/authenticate", json={"password": "password"})

        assert response.status_code == 400

    @pytest.mark.integration
    def test_authenticate_missing_password(self, client):
        """Test authentication with missing password."""
        response = client.post("/api/authenticate", json={"username": "admin"})

        assert response.status_code == 400

    @pytest.mark.integration
    def test_authenticate_missing_body(self, client):
        """Test authentication with missing request body."""
        response = client.post("/api/authenticate")
        assert response.status_code == 400

    @pytest.mark.integration
    def test_authenticate_empty_credentials(self, client):
        """Test authentication with empty credentials."""
        response = client.post(
            "/api/authenticate", json={"username": "", "password": ""}
        )

        assert response.status_code == 400

    @pytest.mark.integration
    def test_logout_success(self, client, auth_headers):
        """Test successful logout."""
        response = client.post("/api/logout", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    @pytest.mark.integration
    def test_logout_without_token(self, client):
        """Test logout without authentication."""
        response = client.post("/api/logout")
        assert response.status_code == 401

    @pytest.mark.integration
    def test_token_validation_after_logout(self, client):
        """Test that token is invalid after logout."""
        # Authenticate
        auth_response = client.post(
            "/api/authenticate",
            json={"username": "testuser", "password": "testpassword"},
        )
        token = auth_response.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Logout
        client.post("/api/logout", headers=headers)

        # Try to use token - should be invalid
        response = client.get("/api/statistics", headers=headers)
        assert response.status_code == 401

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "username,password,expected_status",
        [
            ("admin", "adminpassword", 200),
            ("testuser", "testpassword", 200),
            ("admin", "wrong", 401),
            ("nonexistent", "password", 401),
            ("", "password", 400),
            ("admin", "", 400),
        ],
    )
    def test_authenticate_various_credentials(
        self, client, username, password, expected_status
    ):
        """Test authentication with various credential combinations."""
        response = client.post(
            "/api/authenticate", json={"username": username, "password": password}
        )
        assert response.status_code == expected_status
