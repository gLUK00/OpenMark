"""Plugin system for OpenMark."""

from app.plugins.manager import PluginManager
from app.plugins.base import AuthenticationPlugin, PDFSourcePlugin, AnnotationsPlugin

__all__ = ['PluginManager', 'AuthenticationPlugin', 'PDFSourcePlugin', 'AnnotationsPlugin']
