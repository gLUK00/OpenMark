"""Tests for annotations import/export scripts."""

import pytest
import subprocess
import sys
import json
from pathlib import Path


class TestAnnotationsScripts:
    """Tests for annotations import/export CLI scripts."""

    @pytest.fixture
    def test_config_file(self, temp_dir):
        """Create a test configuration file for scripts."""
        # Create annotations file
        annotations_file = temp_dir / "annotations.json"
        annotations_file.write_text("{}")

        config_data = {
            "server": {"host": "0.0.0.0", "port": 8080, "secret_key": "test-secret"},
            "plugins": {
                "authentication": {
                    "type": "local",
                    "config": {
                        "users_file": str(temp_dir / "users.json"),
                        "token_expiry_hours": 24,
                    },
                },
                "pdf_source": {"type": "local", "config": {"base_path": "./pdfs"}},
                "annotations": {
                    "type": "local",
                    "config": {"storage_file": str(annotations_file)},
                },
            },
        }

        # Create users file
        import hashlib

        users_data = {
            "users": [
                {
                    "username": "admin",
                    "password_hash": hashlib.sha256("adminpass".encode()).hexdigest(),
                    "role": "admin",
                }
            ]
        }
        (temp_dir / "users.json").write_text(json.dumps(users_data))

        config_file = temp_dir / "config.json"
        config_file.write_text(json.dumps(config_data, indent=2))
        return str(config_file), str(annotations_file)

    @pytest.fixture
    def sample_import_file(self, temp_dir):
        """Create a sample import file."""
        data = {
            "version": "1.0",
            "exported_at": "2026-01-13T10:00:00Z",
            "data": [
                {
                    "user_id": "admin",
                    "document_id": "sample",
                    "annotations": {
                        "notes": [
                            {
                                "id": "imported-note-1",
                                "page": 1,
                                "x": 100,
                                "y": 200,
                                "content": "Imported note",
                                "color": "#ffff00",
                            }
                        ],
                        "highlights": [],
                    },
                }
            ],
        }

        import_file = temp_dir / "import.json"
        import_file.write_text(json.dumps(data, indent=2))
        return str(import_file)

    @pytest.mark.unit
    def test_annotations_export_empty(self, test_config_file, temp_dir, project_root):
        """Test exporting annotations when none exist."""
        config_file, _ = test_config_file
        output_file = temp_dir / "export.json"

        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "annotations_export.py"),
                "-c",
                config_file,
                "-u",
                "admin",
                "-d",
                "sample",
                "-o",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        # Should succeed even with no annotations
        assert result.returncode == 0 or "aucune" in result.stdout.lower()

    @pytest.mark.unit
    def test_annotations_import_dry_run(
        self, test_config_file, sample_import_file, project_root
    ):
        """Test import with dry-run mode."""
        config_file, _ = test_config_file

        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "annotations_import.py"),
                "-c",
                config_file,
                "-f",
                sample_import_file,
                "--dry-run",
                "-v",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert result.returncode == 0
        assert (
            "simulé" in result.stdout.lower()
            or "dry" in result.stdout.lower()
            or "validation" in result.stdout.lower()
        )

    @pytest.mark.unit
    def test_annotations_import_actual(
        self, test_config_file, sample_import_file, project_root
    ):
        """Test actual import."""
        config_file, _ = test_config_file

        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "annotations_import.py"),
                "-c",
                config_file,
                "-f",
                sample_import_file,
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert result.returncode == 0

    @pytest.mark.unit
    def test_annotations_export_after_import(
        self, test_config_file, sample_import_file, temp_dir, project_root
    ):
        """Test export after import."""
        config_file, _ = test_config_file
        output_file = temp_dir / "export.json"

        # Import first
        subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "annotations_import.py"),
                "-c",
                config_file,
                "-f",
                sample_import_file,
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        # Then export
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "annotations_export.py"),
                "-c",
                config_file,
                "-u",
                "admin",
                "-d",
                "sample",
                "-o",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert result.returncode == 0

        # Verify exported content
        if output_file.exists():
            exported = json.loads(output_file.read_text())
            assert "data" in exported or "notes" in exported

    @pytest.mark.unit
    def test_annotations_import_invalid_file(
        self, test_config_file, temp_dir, project_root
    ):
        """Test import with invalid file."""
        config_file, _ = test_config_file
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("{ invalid json }")

        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "annotations_import.py"),
                "-c",
                config_file,
                "-f",
                str(invalid_file),
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert result.returncode != 0

    @pytest.mark.unit
    def test_annotations_import_nonexistent_file(self, test_config_file, project_root):
        """Test import with non-existent file."""
        config_file, _ = test_config_file

        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "annotations_import.py"),
                "-c",
                config_file,
                "-f",
                "/nonexistent/file.json",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert result.returncode != 0
