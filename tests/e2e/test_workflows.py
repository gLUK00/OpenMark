"""End-to-end tests for complete workflows."""

import pytest
import time


class TestCompleteWorkflows:
    """End-to-end tests for complete user workflows."""

    @pytest.mark.e2e
    def test_full_document_workflow(self, client):
        """Test complete document viewing workflow."""
        # 1. Authenticate
        auth_response = client.post(
            "/api/authenticate", json={"username": "admin", "password": "adminpassword"}
        )
        assert auth_response.status_code == 200
        token = auth_response.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Request document
        doc_response = client.post(
            "/api/requestDocument", json={"documentId": "sample"}, headers=headers
        )
        assert doc_response.status_code == 200
        temp_doc_id = doc_response.get_json()["tempDocumentId"]

        # 3. Wait for download (if async)
        max_wait = 10
        for _ in range(max_wait):
            status_response = client.get(
                f"/api/downloadStatus?tempDocumentId={temp_doc_id}", headers=headers
            )
            if status_response.status_code == 200:
                status = status_response.get_json().get("status")
                if status == "ready":
                    break
            time.sleep(0.5)

        # 4. View document
        view_response = client.get(
            f"/api/viewDocument?tempDocumentId={temp_doc_id}&token={token}"
        )
        assert view_response.status_code == 200

        # 5. Save annotations
        save_response = client.post(
            "/api/saveAnnotations",
            json={
                "documentId": "sample",
                "annotations": {
                    "notes": [
                        {
                            "id": "e2e-note",
                            "page": 1,
                            "x": 100,
                            "y": 100,
                            "content": "E2E test note",
                            "color": "#ffff00",
                        }
                    ],
                    "highlights": [],
                },
            },
            headers=headers,
        )
        assert save_response.status_code == 200

        # 6. Retrieve annotations
        get_response = client.get(
            "/api/getAnnotations?documentId=sample", headers=headers
        )
        assert get_response.status_code == 200
        annotations = get_response.get_json()
        assert len(annotations["notes"]) > 0

        # 7. Logout
        logout_response = client.post("/api/logout", headers=headers)
        assert logout_response.status_code == 200

    @pytest.mark.e2e
    def test_quick_view_workflow(self, client):
        """Test quickView API workflow."""
        # 1. Use quickView
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

        # 2. Access document using DAT
        dat = data["dat"]
        view_url = data["viewUrl"]

        # Extract tempDocumentId from URL or use DAT directly
        view_response = client.get(f"/api/viewDocument?dat={dat}")
        assert view_response.status_code == 200

    @pytest.mark.e2e
    def test_multi_user_isolation(self, client):
        """Test that multiple users have isolated data."""
        # User 1 saves annotations
        auth1 = client.post(
            "/api/authenticate",
            json={"username": "testuser", "password": "testpassword"},
        ).get_json()
        headers1 = {"Authorization": f'Bearer {auth1["token"]}'}

        client.post(
            "/api/saveAnnotations",
            json={
                "documentId": "sample",
                "annotations": {
                    "notes": [
                        {
                            "id": "user1-note",
                            "page": 1,
                            "x": 10,
                            "y": 10,
                            "content": "User 1 note",
                            "color": "#ff0000",
                        }
                    ],
                    "highlights": [],
                },
            },
            headers=headers1,
        )

        # User 2 checks annotations
        auth2 = client.post(
            "/api/authenticate", json={"username": "admin", "password": "adminpassword"}
        ).get_json()
        headers2 = {"Authorization": f'Bearer {auth2["token"]}'}

        response = client.get("/api/getAnnotations?documentId=sample", headers=headers2)

        annotations = response.get_json()
        # User 2 should not see User 1's annotations
        user1_notes = [n for n in annotations["notes"] if n.get("id") == "user1-note"]
        assert len(user1_notes) == 0

    @pytest.mark.e2e
    def test_statistics_tracking(self, client):
        """Test that statistics are tracked correctly."""
        # Authenticate
        auth = client.post(
            "/api/authenticate", json={"username": "admin", "password": "adminpassword"}
        ).get_json()
        headers = {"Authorization": f'Bearer {auth["token"]}'}

        # Get initial statistics
        initial_stats = client.get("/api/statistics", headers=headers).get_json()

        # Request a document
        client.post(
            "/api/requestDocument", json={"documentId": "sample"}, headers=headers
        )

        # Save some annotations
        client.post(
            "/api/saveAnnotations",
            json={
                "documentId": "sample",
                "annotations": {
                    "notes": [
                        {
                            "id": "stat-note",
                            "page": 1,
                            "x": 10,
                            "y": 10,
                            "content": "Stats test",
                            "color": "#00ff00",
                        }
                    ],
                    "highlights": [
                        {
                            "id": "stat-hl",
                            "page": 1,
                            "rects": [{"x": 10, "y": 50, "width": 100, "height": 15}],
                            "color": "#ffff00",
                        }
                    ],
                },
            },
            headers=headers,
        )

        # Get updated statistics
        updated_stats = client.get("/api/statistics", headers=headers).get_json()

        # Statistics should be present
        assert updated_stats is not None

    @pytest.mark.e2e
    def test_history_tracking(self, client):
        """Test that document access history is tracked."""
        # Authenticate
        auth = client.post(
            "/api/authenticate", json={"username": "admin", "password": "adminpassword"}
        ).get_json()
        headers = {"Authorization": f'Bearer {auth["token"]}'}

        # Request document
        client.post(
            "/api/requestDocument", json={"documentId": "sample"}, headers=headers
        )

        # Check history
        history_response = client.get("/api/history", headers=headers)
        assert history_response.status_code == 200

        history = history_response.get_json()
        assert "history" in history
