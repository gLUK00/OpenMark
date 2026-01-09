"""Plugin manager for OpenMark with automatic plugin discovery."""

from typing import Optional

from app.config import Config
from app.plugins.base import AuthenticationPlugin, PDFSourcePlugin, AnnotationsPlugin
from app.plugins.discovery import get_registry, PluginRegistry


class PluginManager:
    """Manages plugin loading and access with automatic discovery."""
    
    def __init__(self, config: Config):
        """Initialize the plugin manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._auth_plugin: Optional[AuthenticationPlugin] = None
        self._pdf_plugin: Optional[PDFSourcePlugin] = None
        self._annotations_plugin: Optional[AnnotationsPlugin] = None
        
        # Get the plugin registry (triggers discovery if not already done)
        self._registry: PluginRegistry = get_registry()
        
        self._load_plugins()
    
    def _load_plugins(self):
        """Load all configured plugins using the registry."""
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
        """Load an authentication plugin from the registry.
        
        Args:
            plugin_type: Type of plugin to load
            config: Plugin configuration
            
        Returns:
            Loaded authentication plugin
            
        Raises:
            ValueError: If plugin type is not found
        """
        plugin_class = self._registry.get_auth_plugin(plugin_type)
        
        if plugin_class is None:
            available = ', '.join(self._registry.auth_plugins.keys())
            raise ValueError(
                f"Unknown authentication plugin type: '{plugin_type}'. "
                f"Available plugins: {available}"
            )
        
        return plugin_class(config)
    
    def _load_pdf_plugin(self, plugin_type: str, config: dict) -> PDFSourcePlugin:
        """Load a PDF source plugin from the registry.
        
        Args:
            plugin_type: Type of plugin to load
            config: Plugin configuration
            
        Returns:
            Loaded PDF source plugin
            
        Raises:
            ValueError: If plugin type is not found
        """
        plugin_class = self._registry.get_pdf_plugin(plugin_type)
        
        if plugin_class is None:
            available = ', '.join(self._registry.pdf_plugins.keys())
            raise ValueError(
                f"Unknown PDF source plugin type: '{plugin_type}'. "
                f"Available plugins: {available}"
            )
        
        return plugin_class(config)
    
    def _load_annotations_plugin(self, plugin_type: str, config: dict) -> AnnotationsPlugin:
        """Load an annotations plugin from the registry.
        
        Args:
            plugin_type: Type of plugin to load
            config: Plugin configuration
            
        Returns:
            Loaded annotations plugin
            
        Raises:
            ValueError: If plugin type is not found
        """
        plugin_class = self._registry.get_annotations_plugin(plugin_type)
        
        if plugin_class is None:
            available = ', '.join(self._registry.annotations_plugins.keys())
            raise ValueError(
                f"Unknown annotations plugin type: '{plugin_type}'. "
                f"Available plugins: {available}"
            )
        
        return plugin_class(config)
    
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
    
    @property
    def registry(self) -> PluginRegistry:
        """Get the plugin registry."""
        return self._registry
    
    def list_available_plugins(self) -> dict:
        """List all available plugins.
        
        Returns:
            Dict with plugin categories and their available types
        """
        return self._registry.list_plugins()
