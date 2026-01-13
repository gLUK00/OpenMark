"""Integration tests for annotations API."""

import pytest


class TestAnnotationsAPI:
    """Tests for annotations API endpoints."""

    @pytest.mark.integration
    def test_save_annotations_success(self, client, auth_headers, sample_annotations):
        """Test saving annotations."""
        response = client.post(
            "/api/saveAnnotations",
            json={"documentId": "sample", "annotations": sample_annotations},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    @pytest.mark.integration
    def test_save_annotations_unauthorized(self, client, sample_annotations):
        """Test saving annotations without authentication."""
        response = client.post(
            "/api/saveAnnotations",
            json={"documentId": "sample", "annotations": sample_annotations},
        )

        assert response.status_code == 401

    @pytest.mark.integration
    def test_save_annotations_missing_document_id(
        self, client, auth_headers, sample_annotations
    ):
        """Test saving annotations without document ID."""
        response = client.post(
            "/api/saveAnnotations",
            json={"annotations": sample_annotations},
            headers=auth_headers,
        )

        assert response.status_code == 400

    @pytest.mark.integration
    def test_save_annotations_missing_annotations(self, client, auth_headers):
        """Test saving annotations without annotations data."""
        response = client.post(
            "/api/saveAnnotations", json={"documentId": "sample"}, headers=auth_headers
        )

        assert response.status_code == 400

    @pytest.mark.integration
    def test_get_annotations_success(self, client, auth_headers, sample_annotations):
        """Test retrieving annotations."""
        # First save some annotations
        client.post(
            "/api/saveAnnotations",
            json={"documentId": "sample", "annotations": sample_annotations},
            headers=auth_headers,
        )

        # Then retrieve them
        response = client.get(
            "/api/getAnnotations?documentId=sample", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "notes" in data
        assert "highlights" in data

    @pytest.mark.integration
    def test_get_annotations_empty(self, client, auth_headers):
        """Test retrieving annotations for document with none."""
        response = client.get(
            "/api/getAnnotations?documentId=newdoc", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["notes"] == []
        assert data["highlights"] == []

    @pytest.mark.integration
    def test_get_annotations_unauthorized(self, client):
        """Test retrieving annotations without authentication."""
        response = client.get("/api/getAnnotations?documentId=sample")
        assert response.status_code == 401

    @pytest.mark.integration
    def test_get_annotations_missing_document_id(self, client, auth_headers):
        """Test retrieving annotations without document ID."""
        response = client.get("/api/getAnnotations", headers=auth_headers)

        assert response.status_code == 400

    @pytest.mark.integration
    def test_annotations_isolation_between_users(self, client, sample_annotations):
        """Test that annotations are isolated between users."""
        # Save annotations as testuser
        auth1 = client.post(
            "/api/authenticate",
            json={"username": "testuser", "password": "testpassword"},
        ).get_json()
        headers1 = {"Authorization": f'Bearer {auth1["token"]}'}

        client.post(
            "/api/saveAnnotations",
            json={"documentId": "sample", "annotations": sample_annotations},
            headers=headers1,
        )

        # Get annotations as admin
        auth2 = client.post(
            "/api/authenticate", json={"username": "admin", "password": "adminpassword"}
        ).get_json()
        headers2 = {"Authorization": f'Bearer {auth2["token"]}'}

        response = client.get("/api/getAnnotations?documentId=sample", headers=headers2)

        data = response.get_json()
        # Admin should not see testuser's annotations
        assert len(data["notes"]) == 0

    @pytest.mark.integration
    def test_save_empty_annotations(self, client, auth_headers):
        """Test saving empty annotations (clearing)."""
        response = client.post(
            "/api/saveAnnotations",
            json={
                "documentId": "sample",
                "annotations": {"notes": [], "highlights": []},
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

    @pytest.mark.integration
    def test_annotations_note_structure(self, client, auth_headers):
        """Test that note structure is preserved."""
        note = {
            "id": "test-note",
            "page": 1,
            "x": 100,
            "y": 200,
            "width": 150,
            "height": 100,
            "content": "Test content",
            "color": "#ff0000",
        }

        client.post(
            "/api/saveAnnotations",
            json={
                "documentId": "sample",
                "annotations": {"notes": [note], "highlights": []},
            },
            headers=auth_headers,
        )

        response = client.get(
            "/api/getAnnotations?documentId=sample", headers=auth_headers
        )

        saved_note = response.get_json()["notes"][0]
        assert saved_note["page"] == note["page"]
        assert saved_note["x"] == note["x"]
        assert saved_note["content"] == note["content"]

    @pytest.mark.integration
    def test_annotations_highlight_structure(self, client, auth_headers):
        """Test that highlight structure is preserved."""
        highlight = {
            "id": "test-hl",
            "page": 1,
            "rects": [
                {"x": 10, "y": 20, "width": 100, "height": 15},
                {"x": 10, "y": 40, "width": 80, "height": 15},
            ],
            "color": "#00ff00",
        }

        client.post(
            "/api/saveAnnotations",
            json={
                "documentId": "sample",
                "annotations": {"notes": [], "highlights": [highlight]},
            },
            headers=auth_headers,
        )

        response = client.get(
            "/api/getAnnotations?documentId=sample", headers=auth_headers
        )

        saved_hl = response.get_json()["highlights"][0]
        assert len(saved_hl["rects"]) == 2
        assert saved_hl["color"] == highlight["color"]
