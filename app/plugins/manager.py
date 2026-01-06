"""Plugin manager for OpenMark."""

from typing import Optional

from app.config import Config
from app.plugins.base import AuthenticationPlugin, PDFSourcePlugin, AnnotationsPlugin


class PluginManager:
    """Manages plugin loading and access."""
    
    def __init__(self, config: Config):
        """Initialize the plugin manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._auth_plugin: Optional[AuthenticationPlugin] = None
        self._pdf_plugin: Optional[PDFSourcePlugin] = None
        self._annotations_plugin: Optional[AnnotationsPlugin] = None
        
        self._load_plugins()
    
    def _load_plugins(self):
        """Load all configured plugins."""
        plugins_config = self.config.plugins
        
        # Load authentication plugin
        auth_config = plugins_config.get('authentication', {})
        self._auth_plugin = self._load_auth_plugin(
            auth_config.get('type', 'local'),
            auth_config.get('config', {})
        )
        
        # Load PDF source plugin
        pdf_config = plugins_config.get('pdf_source', {})
        self._pdf_plugin = self._load_pdf_plugin(
            pdf_config.get('type', 'http'),
            pdf_config.get('config', {})
        )
        
        # Load annotations plugin
        ann_config = plugins_config.get('annotations', {})
        self._annotations_plugin = self._load_annotations_plugin(
            ann_config.get('type', 'local'),
            ann_config.get('config', {})
        )
    
    def _load_auth_plugin(self, plugin_type: str, config: dict) -> AuthenticationPlugin:
        """Load an authentication plugin.
        
        Args:
            plugin_type: Type of plugin to load
            config: Plugin configuration
            
        Returns:
            Loaded authentication plugin
        """
        if plugin_type == 'local':
            from app.plugins.auth.local_auth import LocalAuthPlugin
            return LocalAuthPlugin(config)
        else:
            raise ValueError(f"Unknown authentication plugin type: {plugin_type}")
    
    def _load_pdf_plugin(self, plugin_type: str, config: dict) -> PDFSourcePlugin:
        """Load a PDF source plugin.
        
        Args:
            plugin_type: Type of plugin to load
            config: Plugin configuration
            
        Returns:
            Loaded PDF source plugin
        """
        if plugin_type == 'http':
            from app.plugins.pdf_source.http_source import HTTPSourcePlugin
            return HTTPSourcePlugin(config)
        else:
            raise ValueError(f"Unknown PDF source plugin type: {plugin_type}")
    
    def _load_annotations_plugin(self, plugin_type: str, config: dict) -> AnnotationsPlugin:
        """Load an annotations plugin.
        
        Args:
            plugin_type: Type of plugin to load
            config: Plugin configuration
            
        Returns:
            Loaded annotations plugin
        """
        if plugin_type == 'local':
            from app.plugins.annotations.local_annotations import LocalAnnotationsPlugin
            return LocalAnnotationsPlugin(config)
        elif plugin_type == 'mongodb':
            from app.plugins.annotations.mongodb_annotations import MongoDBAnnotationsPlugin
            return MongoDBAnnotationsPlugin(config)
        else:
            raise ValueError(f"Unknown annotations plugin type: {plugin_type}")
    
    @property
    def auth_plugin(self) -> AuthenticationPlugin:
        """Get the authentication plugin."""
        return self._auth_plugin
    
    @property
    def pdf_plugin(self) -> PDFSourcePlugin:
        """Get the PDF source plugin."""
        return self._pdf_plugin
    
    @property
    def annotations_plugin(self) -> AnnotationsPlugin:
        """Get the annotations plugin."""
        return self._annotations_plugin
