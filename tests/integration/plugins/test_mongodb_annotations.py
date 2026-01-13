"""Integration tests for MongoDB annotations plugin."""

import os
import pytest

# Skip all tests if MongoDB is not available
pytestmark = pytest.mark.skipif(
    os.environ.get("MONGODB_TEST_URL") is None,
    reason="MongoDB not available for testing",
)


class TestMongoDBAnnotationsPlugin:
    """Tests for MongoDB annotations plugin."""

    @pytest.fixture
    def mongodb_config(self):
        """Get MongoDB configuration from environment."""
        return {
            "connection_string": os.environ.get(
                "MONGODB_TEST_URL", "mongodb://test:testpassword@localhost:27017/"
            ),
            "database": "openmark_test",
            "collection": "test_annotations",
        }

    @pytest.fixture
    def plugin(self, mongodb_config):
        """Create MongoDB annotations plugin instance."""
        from app.plugins.annotations.mongodb_annotations import MongoDBAnnotationsPlugin

        plugin = MongoDBAnnotationsPlugin(mongodb_config)

        # Cleanup before tests
        plugin.collection.delete_many({})

        yield plugin

        # Cleanup after tests
        plugin.collection.delete_many({})

    @pytest.fixture
    def sample_annotations(self):
        """Sample annotations data."""
        return {
            "notes": [
                {
                    "id": "note-1",
                    "page": 1,
                    "x": 100,
                    "y": 200,
                    "content": "Test note",
                    "color": "#ffff00",
                }
            ],
            "highlights": [
                {
                    "id": "hl-1",
                    "page": 1,
                    "rects": [{"x": 50, "y": 100, "width": 200, "height": 20}],
                    "color": "#00ff00",
                }
            ],
        }

    @pytest.mark.integration
    @pytest.mark.docker
    def test_save_annotations(self, plugin, sample_annotations):
        """Test saving annotations."""
        result = plugin.save_annotations("user1", "doc1", sample_annotations)
        assert result is True

    @pytest.mark.integration
    @pytest.mark.docker
    def test_get_annotations(self, plugin, sample_annotations):
        """Test retrieving annotations."""
        plugin.save_annotations("user1", "doc1", sample_annotations)

        result = plugin.get_annotations("user1", "doc1")

        assert len(result["notes"]) == 1
        assert len(result["highlights"]) == 1
        assert result["notes"][0]["content"] == "Test note"

    @pytest.mark.integration
    @pytest.mark.docker
    def test_get_annotations_empty(self, plugin):
        """Test retrieving annotations for non-existent document."""
        result = plugin.get_annotations("nonexistent", "nodoc")

        assert result["notes"] == []
        assert result["highlights"] == []

    @pytest.mark.integration
    @pytest.mark.docker
    def test_update_annotations(self, plugin, sample_annotations):
        """Test updating annotations."""
        plugin.save_annotations("user1", "doc1", sample_annotations)

        # Update
        updated = {
            "notes": [
                {
                    "id": "note-1",
                    "page": 1,
                    "x": 150,
                    "y": 250,
                    "content": "Updated",
                    "color": "#ff0000",
                },
                {
                    "id": "note-2",
                    "page": 2,
                    "x": 50,
                    "y": 100,
                    "content": "New note",
                    "color": "#0000ff",
                },
            ],
            "highlights": [],
        }
        plugin.save_annotations("user1", "doc1", updated)

        result = plugin.get_annotations("user1", "doc1")
        assert len(result["notes"]) == 2
        assert result["notes"][0]["content"] == "Updated"

    @pytest.mark.integration
    @pytest.mark.docker
    def test_user_isolation(self, plugin, sample_annotations):
        """Test that annotations are isolated between users."""
        plugin.save_annotations("user1", "doc1", sample_annotations)
        plugin.save_annotations("user2", "doc1", {"notes": [], "highlights": []})

        result1 = plugin.get_annotations("user1", "doc1")
        result2 = plugin.get_annotations("user2", "doc1")

        assert len(result1["notes"]) == 1
        assert len(result2["notes"]) == 0
