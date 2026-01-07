"""OpenMark Flask Application Factory."""

from flask import Flask
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

from app.config import Config
from app.plugins import PluginManager
from app.jwt_handler import init_jwt_handler

# Swagger UI configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'


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
    
    # Initialize JWT handler for Document Access Tokens
    jwt_handler = init_jwt_handler(app.config['SECRET_KEY'])
    app.config['JWT_HANDLER'] = jwt_handler
    
    # Initialize CORS with full cross-domain support
    # Allow all origins for API and viewer routes
    cors_config = config.server.get('cors', {})
    allowed_origins = cors_config.get('allowed_origins', '*')
    
    CORS(app, 
         origins=allowed_origins,
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         supports_credentials=True,
         expose_headers=['Content-Type', 'Content-Length'])
    
    # Initialize plugin manager
    plugin_manager = PluginManager(config)
    app.config['PLUGIN_MANAGER'] = plugin_manager
    
    # Register Swagger UI blueprint
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "OpenMark API Documentation",
            'docExpansion': 'list',
            'defaultModelsExpandDepth': 2,
            'defaultModelExpandDepth': 2,
            'tryItOutEnabled': True
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    # Register blueprints
    from app.routes import api_bp, views_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp)
    
    # Initialize cache cleaner (only in non-reloader process)
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        from app.cache_cleaner import init_cache_cleaner
        init_cache_cleaner(app)
    
    return app
