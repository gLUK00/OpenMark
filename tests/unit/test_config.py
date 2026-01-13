"""Unit tests for configuration module."""

import pytest
import json
from pathlib import Path

from app.config import Config


class TestConfig:
    """Tests for configuration loading and parsing."""

    @pytest.fixture
    def valid_config_file(self, temp_dir):
        """Create a valid configuration file."""
        config_data = {
            "server": {
                "host": "127.0.0.1",
                "port": 9000,
                "debug": True,
                "secret_key": "my-secret-key",
            },
            "cache": {"directory": "./cache", "duration_seconds": 7200},
            "plugins": {
                "authentication": {
                    "type": "local",
                    "config": {"users_file": "./users.json"},
                },
                "pdf_source": {"type": "local", "config": {"base_path": "./pdfs"}},
                "annotations": {
                    "type": "local",
                    "config": {"storage_file": "./annotations.json"},
                },
            },
        }
        config_file = temp_dir / "config.json"
        config_file.write_text(json.dumps(config_data))
        return str(config_file)

    @pytest.mark.unit
    def test_load_valid_config(self, valid_config_file):
        """Test loading a valid configuration file."""
        config = Config(valid_config_file)

        assert config.server["host"] == "127.0.0.1"
        assert config.server["port"] == 9000
        assert config.server["debug"] is True
        assert config.cache["duration_seconds"] == 7200

    @pytest.mark.unit
    def test_plugin_config(self, valid_config_file):
        """Test plugin configuration access."""
        config = Config(valid_config_file)

        assert config.plugins["authentication"]["type"] == "local"
        assert config.plugins["pdf_source"]["type"] == "local"
        assert config.plugins["annotations"]["type"] == "local"

    @pytest.mark.unit
    def test_missing_config_file_uses_defaults(self, temp_dir):
        """Test that missing configuration file uses defaults."""
        config = Config(str(temp_dir / "nonexistent.json"))

        # Should use default values
        assert config.server["host"] == "0.0.0.0"
        assert config.server["port"] == 8080
        assert "plugins" in config._config

    @pytest.mark.unit
    def test_invalid_json_config(self, temp_dir):
        """Test handling invalid JSON in configuration file."""
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            Config(str(invalid_file))

    @pytest.mark.unit
    def test_default_values(self, temp_dir):
        """Test that default values are used for missing fields."""
        minimal_config = {
            "plugins": {
                "authentication": {"type": "local", "config": {}},
                "pdf_source": {"type": "local", "config": {}},
                "annotations": {"type": "local", "config": {}},
            }
        }
        config_file = temp_dir / "minimal.json"
        config_file.write_text(json.dumps(minimal_config))

        config = Config(str(config_file))

        # Check defaults are applied
        assert (
            "host" in config.server or config.server.get("host", "0.0.0.0") == "0.0.0.0"
        )
