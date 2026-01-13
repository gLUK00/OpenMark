"""Integration tests for PostgreSQL annotations plugin."""

import os
import pytest

# Skip all tests if PostgreSQL is not available
pytestmark = pytest.mark.skipif(
    os.environ.get("POSTGRES_TEST_URL") is None,
    reason="PostgreSQL not available for testing",
)


class TestPostgreSQLAnnotationsPlugin:
    """Tests for PostgreSQL annotations plugin."""

    @pytest.fixture
    def postgres_config(self):
        """Get PostgreSQL configuration from environment."""
        return {
            "host": "localhost",
            "port": 5432,
            "database": "openmark_test",
            "user": "test",
            "password": "testpassword",
            "table_name": "test_annotations",
        }

    @pytest.fixture
    def plugin(self, postgres_config):
        """Create PostgreSQL annotations plugin instance."""
        from app.plugins.annotations.postgresql_annotations import (
            PostgreSQLAnnotationsPlugin,
        )

        plugin = PostgreSQLAnnotationsPlugin(postgres_config)

        # Cleanup before tests
        cursor = plugin.connection.cursor()
        cursor.execute(f"DELETE FROM {postgres_config['table_name']}")
        plugin.connection.commit()
        cursor.close()

        yield plugin

        # Cleanup after tests
        cursor = plugin.connection.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {postgres_config['table_name']}")
        plugin.connection.commit()
        cursor.close()

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

    @pytest.mark.integration
    @pytest.mark.docker
    def test_get_annotations_empty(self, plugin):
        """Test retrieving annotations for non-existent document."""
        result = plugin.get_annotations("nonexistent", "nodoc")

        assert result["notes"] == []
        assert result["highlights"] == []

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
