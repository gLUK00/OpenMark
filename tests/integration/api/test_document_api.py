"""Integration tests for document API."""

import pytest


class TestDocumentAPI:
    """Tests for document-related API endpoints."""

    @pytest.mark.integration
    def test_request_document_success(self, client, auth_headers):
        """Test successful document request."""
        response = client.post(
            "/api/requestDocument", json={"documentId": "sample"}, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "tempDocumentId" in data

    @pytest.mark.integration
    def test_request_document_not_found(self, client, auth_headers):
        """Test requesting a non-existent document."""
        response = client.post(
            "/api/requestDocument",
            json={"documentId": "nonexistent"},
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.integration
    def test_request_document_missing_id(self, client, auth_headers):
        """Test document request with missing document ID."""
        response = client.post("/api/requestDocument", json={}, headers=auth_headers)

        assert response.status_code == 400

    @pytest.mark.integration
    def test_request_document_unauthorized(self, client):
        """Test document request without authentication."""
        response = client.post("/api/requestDocument", json={"documentId": "sample"})

        assert response.status_code == 401

    @pytest.mark.integration
    def test_quick_view_success(self, client):
        """Test quickView API success."""
        response = client.post(
            "/api/quickView",
            json={
                "username": "admin",
                "password": "adminpassword",
                "documentId": "sample",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "viewUrl" in data
        assert "dat" in data

    @pytest.mark.integration
    def test_quick_view_invalid_credentials(self, client):
        """Test quickView with invalid credentials."""
        response = client.post(
            "/api/quickView",
            json={
                "username": "admin",
                "password": "wrongpassword",
                "documentId": "sample",
            },
        )

        assert response.status_code == 401

    @pytest.mark.integration
    def test_quick_view_document_not_found(self, client):
        """Test quickView with non-existent document."""
        response = client.post(
            "/api/quickView",
            json={
                "username": "admin",
                "password": "adminpassword",
                "documentId": "nonexistent",
            },
        )

        assert response.status_code == 404

    @pytest.mark.integration
    def test_quick_view_missing_document_id(self, client):
        """Test quickView without document ID."""
        response = client.post(
            "/api/quickView", json={"username": "admin", "password": "adminpassword"}
        )

        assert response.status_code == 400

    @pytest.mark.integration
    def test_quick_view_with_options(self, client):
        """Test quickView with display options."""
        response = client.post(
            "/api/quickView",
            json={
                "username": "admin",
                "password": "adminpassword",
                "documentId": "sample",
                "hideAnnotationsTools": True,
                "hideAnnotations": True,
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "viewUrl" in data
        # URL should contain the options
        assert "hideAnnotationsTools" in data["viewUrl"] or data.get(
            "hideAnnotationsTools"
        )

    @pytest.mark.integration
    def test_view_document_success(self, client, auth_headers):
        """Test viewing a document."""
        # First request the document
        request_response = client.post(
            "/api/requestDocument", json={"documentId": "sample"}, headers=auth_headers
        )
        temp_doc_id = request_response.get_json()["tempDocumentId"]

        # Then view it
        token = auth_headers["Authorization"].split(" ")[1]
        response = client.get(
            f"/api/viewDocument?tempDocumentId={temp_doc_id}&token={token}"
        )

        assert response.status_code == 200

    @pytest.mark.integration
    def test_view_document_invalid_temp_id(self, client, auth_headers):
        """Test viewing with invalid temp document ID."""
        token = auth_headers["Authorization"].split(" ")[1]
        response = client.get(f"/api/viewDocument?tempDocumentId=invalid&token={token}")

        assert response.status_code == 404

    @pytest.mark.integration
    def test_download_status_pending(self, client, auth_headers):
        """Test download status for pending document."""
        # Request document
        request_response = client.post(
            "/api/requestDocument", json={"documentId": "sample"}, headers=auth_headers
        )
        temp_doc_id = request_response.get_json()["tempDocumentId"]

        # Check status
        response = client.get(
            f"/api/downloadStatus?tempDocumentId={temp_doc_id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data
