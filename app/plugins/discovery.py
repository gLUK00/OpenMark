"""Plugin discovery system for OpenMark.

This module provides automatic plugin discovery by scanning plugin directories
for classes that inherit from the base plugin classes. This allows users to
add custom plugins by simply placing Python files in the appropriate directories.
"""

import importlib
import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar

from app.plugins.base import AuthenticationPlugin, PDFSourcePlugin, AnnotationsPlugin


T = TypeVar('T')

# Plugin type mapping
PLUGIN_CATEGORIES = {
    'auth': AuthenticationPlugin,
    'pdf_source': PDFSourcePlugin,
    'annotations': AnnotationsPlugin
}

# Default plugin directories (relative to app/plugins/)
DEFAULT_PLUGIN_DIRS = {
    'auth': 'auth',
    'pdf_source': 'pdf_source',
    'annotations': 'annotations'
}

# Custom plugins directory (can be mounted via Docker volume)
CUSTOM_PLUGINS_DIR = os.environ.get('OPENMARK_CUSTOM_PLUGINS_DIR', './custom_plugins')


class PluginRegistry:
    """Registry for discovered plugins."""
    
    _instance: Optional['PluginRegistry'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not PluginRegistry._initialized:
            self._auth_plugins: Dict[str, Type[AuthenticationPlugin]] = {}
            self._pdf_plugins: Dict[str, Type[PDFSourcePlugin]] = {}
            self._annotations_plugins: Dict[str, Type[AnnotationsPlugin]] = {}
            PluginRegistry._initialized = True
    
    @property
    def auth_plugins(self) -> Dict[str, Type[AuthenticationPlugin]]:
        return self._auth_plugins
    
    @property
    def pdf_plugins(self) -> Dict[str, Type[PDFSourcePlugin]]:
        return self._pdf_plugins
    
    @property
    def annotations_plugins(self) -> Dict[str, Type[AnnotationsPlugin]]:
        return self._annotations_plugins
    
    def register_auth_plugin(self, name: str, plugin_class: Type[AuthenticationPlugin]):
        """Register an authentication plugin."""
        self._auth_plugins[name] = plugin_class
        print(f"  ✓ Registered auth plugin: {name}")
    
    def register_pdf_plugin(self, name: str, plugin_class: Type[PDFSourcePlugin]):
        """Register a PDF source plugin."""
        self._pdf_plugins[name] = plugin_class
        print(f"  ✓ Registered pdf_source plugin: {name}")
    
    def register_annotations_plugin(self, name: str, plugin_class: Type[AnnotationsPlugin]):
        """Register an annotations plugin."""
        self._annotations_plugins[name] = plugin_class
        print(f"  ✓ Registered annotations plugin: {name}")
    
    def get_auth_plugin(self, name: str) -> Optional[Type[AuthenticationPlugin]]:
        """Get an authentication plugin class by name."""
        return self._auth_plugins.get(name)
    
    def get_pdf_plugin(self, name: str) -> Optional[Type[PDFSourcePlugin]]:
        """Get a PDF source plugin class by name."""
        return self._pdf_plugins.get(name)
    
    def get_annotations_plugin(self, name: str) -> Optional[Type[AnnotationsPlugin]]:
        """Get an annotations plugin class by name."""
        return self._annotations_plugins.get(name)
    
    def list_plugins(self) -> dict:
        """List all registered plugins."""
        return {
            'auth': list(self._auth_plugins.keys()),
            'pdf_source': list(self._pdf_plugins.keys()),
            'annotations': list(self._annotations_plugins.keys())
        }


def get_plugin_name_from_class(cls: type) -> str:
    """Extract plugin name from class name.
    
    Converts class names like 'LocalAuthPlugin' to 'local',
    'MongoDBAnnotationsPlugin' to 'mongodb', etc.
    
    Args:
        cls: The plugin class
        
    Returns:
        Plugin name in lowercase
    """
    name = cls.__name__
    
    # Remove common suffixes
    suffixes = ['AuthPlugin', 'SourcePlugin', 'AnnotationsPlugin', 'Plugin']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    
    # Convert CamelCase to lowercase with underscores, then remove underscores
    # e.g., 'LocalAuth' -> 'local', 'MongoDB' -> 'mongodb', 'PostgreSQL' -> 'postgresql'
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            # Don't add underscore if previous char is also uppercase (acronyms)
            if not name[i-1].isupper():
                result.append('_')
        result.append(char.lower())
    
    # Clean up the name
    clean_name = ''.join(result).replace('_', '')
    
    # Handle special cases
    special_mappings = {
        'httpsource': 'http',
        's3source': 's3',
        'localauth': 'local',
        'localannotations': 'local',
        'mongodbannotations': 'mongodb',
        'mongodbauth': 'mongodb',
        'postgresqlannotations': 'postgresql',
        'postgresqlauth': 'postgresql',
        'oauthauth': 'oauth',
        'samlauth': 'saml'
    }
    
    return special_mappings.get(clean_name, clean_name)


def discover_plugins_in_module(module, base_class: Type[T], registry: PluginRegistry, category: str):
    """Discover and register plugins in a module.
    
    Args:
        module: The Python module to scan
        base_class: The base class to look for (AuthenticationPlugin, etc.)
        registry: The plugin registry
        category: Plugin category ('auth', 'pdf_source', 'annotations')
    """
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Check if it's a subclass of the base class (but not the base class itself)
        if issubclass(obj, base_class) and obj is not base_class:
            # Skip abstract classes
            if inspect.isabstract(obj):
                continue
            
            plugin_name = get_plugin_name_from_class(obj)
            
            # Register based on category
            if category == 'auth':
                registry.register_auth_plugin(plugin_name, obj)
            elif category == 'pdf_source':
                registry.register_pdf_plugin(plugin_name, obj)
            elif category == 'annotations':
                registry.register_annotations_plugin(plugin_name, obj)


def load_module_from_file(file_path: Path, module_name: str):
    """Load a Python module from a file path.
    
    Args:
        file_path: Path to the Python file
        module_name: Name to give the module
        
    Returns:
        The loaded module, or None if loading failed
    """
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"  ⚠ Error loading module {file_path}: {e}")
        return None


def discover_plugins_in_directory(directory: Path, base_class: Type[T], 
                                   registry: PluginRegistry, category: str,
                                   module_prefix: str = ""):
    """Discover plugins in a directory.
    
    Args:
        directory: Directory to scan
        base_class: Base plugin class
        registry: Plugin registry
        category: Plugin category
        module_prefix: Prefix for module names
    """
    if not directory.exists():
        return
    
    for file_path in directory.glob("*.py"):
        # Skip __init__.py and test files
        if file_path.name.startswith('__') or file_path.name.startswith('test_'):
            continue
        
        module_name = f"{module_prefix}.{file_path.stem}" if module_prefix else file_path.stem
        
        try:
            # Try to import as a package module first
            if module_prefix:
                try:
                    module = importlib.import_module(module_name)
                except ImportError:
                    module = load_module_from_file(file_path, module_name)
            else:
                module = load_module_from_file(file_path, module_name)
            
            if module:
                discover_plugins_in_module(module, base_class, registry, category)
        except Exception as e:
            print(f"  ⚠ Error processing {file_path}: {e}")


def discover_all_plugins() -> PluginRegistry:
    """Discover all plugins from default and custom directories.
    
    Returns:
        PluginRegistry with all discovered plugins
    """
    registry = PluginRegistry()
    
    # Get the plugins directory
    plugins_dir = Path(__file__).parent
    
    print("🔍 Discovering plugins...")
    
    # Discover built-in plugins
    for category, subdir in DEFAULT_PLUGIN_DIRS.items():
        base_class = PLUGIN_CATEGORIES[category]
        plugin_dir = plugins_dir / subdir
        module_prefix = f"app.plugins.{subdir}"
        
        print(f"  Scanning {category} plugins in {plugin_dir}...")
        discover_plugins_in_directory(plugin_dir, base_class, registry, category, module_prefix)
    
    # Discover custom plugins
    custom_dir = Path(CUSTOM_PLUGINS_DIR)
    if custom_dir.exists():
        print(f"  Scanning custom plugins in {custom_dir}...")
        
        # Add custom plugins directory to path
        if str(custom_dir.absolute()) not in sys.path:
            sys.path.insert(0, str(custom_dir.absolute()))
        
        for category, base_class in PLUGIN_CATEGORIES.items():
            category_dir = custom_dir / category
            if category_dir.exists():
                print(f"    Custom {category} plugins...")
                discover_plugins_in_directory(category_dir, base_class, registry, category)
    
    print(f"✅ Plugin discovery complete. Found: {registry.list_plugins()}")
    return registry


# Global registry instance
_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """Get or create the global plugin registry.
    
    Returns:
        The global PluginRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = discover_all_plugins()
    return _registry


def reload_plugins():
    """Force reload of all plugins.
    
    Useful for development or after adding new plugins.
    """
    global _registry
    PluginRegistry._initialized = False
    PluginRegistry._instance = None
    _registry = None
    return get_registry()
