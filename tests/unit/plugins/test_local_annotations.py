"""Unit tests for local annotations plugin."""

import pytest
import json
from pathlib import Path

from app.plugins.annotations.local_annotations import LocalAnnotationsPlugin


class TestLocalAnnotationsPlugin:
    """Tests for local annotations plugin."""

    @pytest.fixture
    def storage_file(self, temp_dir):
        """Create a temporary storage file."""
        storage_path = temp_dir / "annotations.json"
        storage_path.write_text("{}")
        return str(storage_path)

    @pytest.fixture
    def plugin(self, storage_file):
        """Create plugin instance."""
        config = {"storage_file": storage_file}
        return LocalAnnotationsPlugin(config)

    @pytest.fixture
    def sample_notes(self):
        """Sample notes data."""
        return [
            {
                "id": "note-1",
                "page": 1,
                "x": 100,
                "y": 200,
                "width": 150,
                "height": 100,
                "content": "Test note 1",
                "color": "#ffff00",
            },
            {
                "id": "note-2",
                "page": 2,
                "x": 50,
                "y": 300,
                "width": 200,
                "height": 150,
                "content": "Test note 2",
                "color": "#ff9900",
            },
        ]

    @pytest.fixture
    def sample_highlights(self):
        """Sample highlights data."""
        return [
            {
                "id": "hl-1",
                "page": 1,
                "rects": [{"x": 50, "y": 100, "width": 300, "height": 20}],
                "color": "#00ff00",
            }
        ]

    @pytest.mark.unit
    def test_save_annotations(self, plugin, sample_notes, sample_highlights):
        """Test saving annotations."""
        annotations = {"notes": sample_notes, "highlights": sample_highlights}

        result = plugin.save_annotations("user1", "doc1", annotations)
        assert result is True

    @pytest.mark.unit
    def test_get_annotations(self, plugin, sample_notes, sample_highlights):
        """Test retrieving saved annotations."""
        annotations = {"notes": sample_notes, "highlights": sample_highlights}

        plugin.save_annotations("user1", "doc1", annotations)
        result = plugin.get_annotations("user1", "doc1")

        assert "notes" in result
        assert "highlights" in result
        assert len(result["notes"]) == 2
        assert len(result["highlights"]) == 1

    @pytest.mark.unit
    def test_get_annotations_empty(self, plugin):
        """Test retrieving annotations for non-existent user/document."""
        result = plugin.get_annotations("nonexistent", "nodoc")

        assert result["notes"] == []
        assert result["highlights"] == []

    @pytest.mark.unit
    def test_update_annotations(self, plugin, sample_notes):
        """Test updating existing annotations."""
        # Save initial annotations
        plugin.save_annotations(
            "user1", "doc1", {"notes": sample_notes[:1], "highlights": []}
        )

        # Update with new annotations
        updated = {"notes": sample_notes, "highlights": []}
        plugin.save_annotations("user1", "doc1", updated)

        result = plugin.get_annotations("user1", "doc1")
        assert len(result["notes"]) == 2

    @pytest.mark.unit
    def test_multiple_users_same_document(self, plugin, sample_notes):
        """Test that different users have separate annotations for same document."""
        plugin.save_annotations(
            "user1", "doc1", {"notes": sample_notes[:1], "highlights": []}
        )
        plugin.save_annotations(
            "user2", "doc1", {"notes": sample_notes[1:], "highlights": []}
        )

        result1 = plugin.get_annotations("user1", "doc1")
        result2 = plugin.get_annotations("user2", "doc1")

        assert len(result1["notes"]) == 1
        assert len(result2["notes"]) == 1
        assert result1["notes"][0]["id"] != result2["notes"][0]["id"]

    @pytest.mark.unit
    def test_multiple_documents_same_user(self, plugin, sample_notes):
        """Test that same user can have annotations on different documents."""
        plugin.save_annotations(
            "user1", "doc1", {"notes": sample_notes[:1], "highlights": []}
        )
        plugin.save_annotations(
            "user1", "doc2", {"notes": sample_notes[1:], "highlights": []}
        )

        result1 = plugin.get_annotations("user1", "doc1")
        result2 = plugin.get_annotations("user1", "doc2")

        assert len(result1["notes"]) == 1
        assert len(result2["notes"]) == 1

    @pytest.mark.unit
    def test_save_empty_annotations(self, plugin):
        """Test saving empty annotations."""
        result = plugin.save_annotations(
            "user1", "doc1", {"notes": [], "highlights": []}
        )
        assert result is True

        loaded = plugin.get_annotations("user1", "doc1")
        assert loaded["notes"] == []
        assert loaded["highlights"] == []

    @pytest.mark.unit
    def test_persistence(self, storage_file, sample_notes):
        """Test that annotations persist across plugin instances."""
        plugin1 = LocalAnnotationsPlugin({"storage_file": storage_file})
        plugin1.save_annotations(
            "user1", "doc1", {"notes": sample_notes, "highlights": []}
        )

        # Create new plugin instance
        plugin2 = LocalAnnotationsPlugin({"storage_file": storage_file})
        result = plugin2.get_annotations("user1", "doc1")

        assert len(result["notes"]) == 2
