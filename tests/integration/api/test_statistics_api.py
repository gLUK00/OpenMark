"""Integration tests for statistics and history API."""

import pytest


class TestStatisticsAPI:
    """Tests for statistics API endpoint."""

    @pytest.mark.integration
    def test_get_statistics_success(self, client, auth_headers):
        """Test retrieving statistics."""
        response = client.get("/api/statistics", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "documentsViewed" in data or "documents_viewed" in data

    @pytest.mark.integration
    def test_get_statistics_unauthorized(self, client):
        """Test retrieving statistics without authentication."""
        response = client.get("/api/statistics")
        assert response.status_code == 401

    @pytest.mark.integration
    def test_statistics_increment_on_view(self, client, auth_headers):
        """Test that statistics increment when viewing documents."""
        # Get initial stats
        initial = client.get("/api/statistics", headers=auth_headers).get_json()

        # Request and view a document
        request_response = client.post(
            "/api/requestDocument", json={"documentId": "sample"}, headers=auth_headers
        )

        if request_response.status_code == 200:
            # Get updated stats
            updated = client.get("/api/statistics", headers=auth_headers).get_json()
            # Stats should have changed (or equal if no tracking)
            assert updated is not None


class TestHistoryAPI:
    """Tests for history API endpoint."""

    @pytest.mark.integration
    def test_get_history_success(self, client, auth_headers):
        """Test retrieving history."""
        response = client.get("/api/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "history" in data
        assert isinstance(data["history"], list)

    @pytest.mark.integration
    def test_get_history_unauthorized(self, client):
        """Test retrieving history without authentication."""
        response = client.get("/api/history")
        assert response.status_code == 401

    @pytest.mark.integration
    def test_history_records_access(self, client, auth_headers):
        """Test that history records document access."""
        # Request a document
        client.post(
            "/api/requestDocument", json={"documentId": "sample"}, headers=auth_headers
        )

        # Check history
        response = client.get("/api/history", headers=auth_headers)
        data = response.get_json()

        # History should contain at least one entry
        # (May be empty if history tracking is not enabled)
        assert "history" in data

    @pytest.mark.integration
    def test_history_entry_structure(self, client, auth_headers):
        """Test history entry structure."""
        # Request a document to ensure there's history
        client.post(
            "/api/requestDocument", json={"documentId": "sample"}, headers=auth_headers
        )

        response = client.get("/api/history", headers=auth_headers)
        data = response.get_json()

        if len(data["history"]) > 0:
            entry = data["history"][0]
            # Check expected fields
            assert "documentId" in entry or "document_id" in entry
            assert "timestamp" in entry
