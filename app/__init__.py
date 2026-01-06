"""OpenMark Flask Application Factory."""

from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.plugins import PluginManager


def create_app(config_path: str = 'config.json') -> Flask:
    """Create and configure the Flask application.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Load configuration
    config = Config(config_path)
    app.config['SECRET_KEY'] = config.server.get('secret_key', 'dev-secret-key')
    app.config['CONFIG'] = config
    
    # Initialize CORS
    CORS(app)
    
    # Initialize plugin manager
    plugin_manager = PluginManager(config)
    app.config['PLUGIN_MANAGER'] = plugin_manager
    
    # Register blueprints
    from app.routes import api_bp, views_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp)
    
    return app
