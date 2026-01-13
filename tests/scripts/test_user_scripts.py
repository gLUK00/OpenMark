"""Tests for user management scripts."""

import pytest
import subprocess
import sys
import json
from pathlib import Path


class TestUserScripts:
    """Tests for user management CLI scripts."""

    @pytest.fixture
    def test_config_file(self, temp_dir, test_users_file):
        """Create a test configuration file for scripts."""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8080, "secret_key": "test-secret"},
            "plugins": {
                "authentication": {
                    "type": "local",
                    "config": {"users_file": test_users_file, "token_expiry_hours": 24},
                },
                "pdf_source": {"type": "local", "config": {"base_path": "./pdfs"}},
                "annotations": {
                    "type": "local",
                    "config": {"storage_file": str(temp_dir / "annotations.json")},
                },
            },
        }

        config_file = temp_dir / "config.json"
        config_file.write_text(json.dumps(config_data, indent=2))
        return str(config_file)

    @pytest.mark.unit
    def test_user_list_script(self, test_config_file, project_root):
        """Test user list script."""
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "user_list.py"),
                "-c",
                test_config_file,
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert result.returncode == 0
        # Should list at least admin and testuser
        assert "admin" in result.stdout or "testuser" in result.stdout

    @pytest.mark.unit
    def test_user_list_json_format(self, test_config_file, project_root):
        """Test user list script with JSON output."""
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "user_list.py"),
                "-c",
                test_config_file,
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert result.returncode == 0
        # Should be valid JSON
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    @pytest.mark.unit
    def test_user_create_script(self, test_config_file, project_root):
        """Test user creation script."""
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "user_create.py"),
                "-c",
                test_config_file,
                "-u",
                "newuser",
                "-p",
                "newpassword123",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert result.returncode == 0
        assert (
            "créé" in result.stdout.lower()
            or "created" in result.stdout.lower()
            or "✅" in result.stdout
        )

    @pytest.mark.unit
    def test_user_create_duplicate(self, test_config_file, project_root):
        """Test creating duplicate user fails."""
        # First creation
        subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "user_create.py"),
                "-c",
                test_config_file,
                "-u",
                "dupuser",
                "-p",
                "password123",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        # Second creation should fail
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "user_create.py"),
                "-c",
                test_config_file,
                "-u",
                "dupuser",
                "-p",
                "password123",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert (
            result.returncode != 0
            or "existe" in result.stdout.lower()
            or "exists" in result.stdout.lower()
        )

    @pytest.mark.unit
    def test_user_modify_password(self, test_config_file, project_root):
        """Test modifying user password."""
        # Create user first
        subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "user_create.py"),
                "-c",
                test_config_file,
                "-u",
                "moduser",
                "-p",
                "oldpassword",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        # Modify password
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "user_modify.py"),
                "-c",
                test_config_file,
                "-u",
                "moduser",
                "-p",
                "newpassword",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert result.returncode == 0

    @pytest.mark.unit
    def test_user_delete_script(self, test_config_file, project_root):
        """Test user deletion script."""
        # Create user first
        subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "user_create.py"),
                "-c",
                test_config_file,
                "-u",
                "deluser",
                "-p",
                "password",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        # Delete user
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "user_delete.py"),
                "-c",
                test_config_file,
                "-u",
                "deluser",
                "--force",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert result.returncode == 0

    @pytest.mark.unit
    def test_user_delete_nonexistent(self, test_config_file, project_root):
        """Test deleting non-existent user."""
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "user_delete.py"),
                "-c",
                test_config_file,
                "-u",
                "nonexistent",
                "--force",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        assert (
            result.returncode != 0
            or "not found" in result.stdout.lower()
            or "introuvable" in result.stdout.lower()
        )
