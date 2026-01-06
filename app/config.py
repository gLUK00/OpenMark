"""Configuration management for OpenMark."""

import json
import os
from typing import Any


class Config:
    """Application configuration manager."""
    
    def __init__(self, config_path: str = 'config.json'):
        """Initialize configuration from JSON file.
        
        Args:
            config_path: Path to the configuration file
        """
        self._config = self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._default_config()
    
    def _default_config(self) -> dict:
        """Return default configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": True,
                "secret_key": "dev-secret-key-change-in-production"
            },
            "cache": {
                "directory": "./cache",
                "duration_seconds": 3600
            },
            "plugins": {
                "authentication": {
                    "type": "local",
                    "config": {
                        "users_file": "./data/users.json",
                        "token_expiry_hours": 24
                    }
                },
                "pdf_source": {
                    "type": "http",
                    "config": {
                        "base_url": "",
                        "timeout": 30
                    }
                },
                "annotations": {
                    "type": "local",
                    "config": {
                        "storage_path": "./data/annotations.json"
                    }
                }
            },
            "customization": {
                "script_file": None,
                "logo_url": None,
                "primary_color": "#007bff"
            }
        }
    
    @property
    def server(self) -> dict:
        """Get server configuration."""
        return self._config.get('server', {})
    
    @property
    def cache(self) -> dict:
        """Get cache configuration."""
        return self._config.get('cache', {})
    
    @property
    def plugins(self) -> dict:
        """Get plugins configuration."""
        return self._config.get('plugins', {})
    
    @property
    def customization(self) -> dict:
        """Get customization configuration."""
        return self._config.get('customization', {})
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
