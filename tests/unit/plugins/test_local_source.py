"""Unit tests for local PDF source plugin."""

import pytest
from pathlib import Path

from app.plugins.pdf_source.local_source import LocalSourcePlugin


class TestLocalSourcePlugin:
    """Tests for local PDF source plugin."""

    @pytest.fixture
    def pdfs_dir(self, temp_dir, fixtures_dir):
        """Create a directory with test PDFs."""
        pdfs_path = temp_dir / "pdfs"
        pdfs_path.mkdir()

        # Copy sample PDF if exists
        sample = fixtures_dir / "pdfs" / "sample.pdf"
        if sample.exists():
            (pdfs_path / "sample.pdf").write_bytes(sample.read_bytes())
        else:
            # Create a minimal PDF
            (pdfs_path / "sample.pdf").write_bytes(b"%PDF-1.4 minimal")

        return str(pdfs_path)

    @pytest.fixture
    def plugin(self, pdfs_dir):
        """Create plugin instance."""
        config = {"base_path": pdfs_dir}
        return LocalSourcePlugin(config)

    @pytest.mark.unit
    def test_document_exists_true(self, plugin):
        """Test checking for existing document."""
        assert plugin.document_exists("sample") is True

    @pytest.mark.unit
    def test_document_exists_false(self, plugin):
        """Test checking for non-existing document."""
        assert plugin.document_exists("nonexistent") is False

    @pytest.mark.unit
    def test_get_document_valid(self, plugin):
        """Test retrieving a valid document."""
        data = plugin.get_document("sample")

        assert data is not None
        assert isinstance(data, bytes)
        assert len(data) > 0

    @pytest.mark.unit
    def test_get_document_invalid(self, plugin):
        """Test retrieving a non-existent document."""
        data = plugin.get_document("nonexistent")
        assert data is None

    @pytest.mark.unit
    def test_document_id_with_extension(self, plugin):
        """Test that document ID works with or without .pdf extension."""
        # Should work without extension
        assert plugin.document_exists("sample") is True

        # Should also work with extension
        assert plugin.document_exists("sample.pdf") is True

    @pytest.mark.unit
    def test_path_traversal_prevention(self, plugin):
        """Test that path traversal attacks are prevented."""
        # Attempt path traversal
        assert plugin.document_exists("../../../etc/passwd") is False
        assert plugin.get_document("../../../etc/passwd") is None

    @pytest.mark.unit
    def test_empty_document_id(self, plugin):
        """Test handling of empty document ID."""
        assert plugin.document_exists("") is False
        assert plugin.get_document("") is None

    @pytest.mark.unit
    def test_special_characters_in_id(self, plugin, temp_dir):
        """Test handling of special characters in document ID."""
        pdfs_dir = Path(plugin.config["base_path"])

        # Create file with special name
        special_file = pdfs_dir / "test-doc_2026.pdf"
        special_file.write_bytes(b"%PDF-1.4 test")

        assert plugin.document_exists("test-doc_2026") is True
        data = plugin.get_document("test-doc_2026")
        assert data is not None
