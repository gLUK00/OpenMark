"""View routes for OpenMark."""

import os
from datetime import datetime

from flask import Blueprint, request, render_template, redirect, url_for, current_app, send_file, abort, make_response

from app.routes.api import temp_documents, require_auth, record_document_view
from app.jwt_handler import get_jwt_handler

views_bp = Blueprint('views', __name__)


def add_iframe_headers(response):
    """Add headers to allow embedding in iframe from any origin."""
    # Remove X-Frame-Options to allow iframe embedding
    response.headers.pop('X-Frame-Options', None)
    
    # Set Content-Security-Policy to allow embedding from any origin
    # frame-ancestors * allows the page to be embedded in any iframe
    response.headers['Content-Security-Policy'] = "frame-ancestors *"
    
    # Allow cross-origin isolation for SharedArrayBuffer if needed
    response.headers['Cross-Origin-Embedder-Policy'] = 'credentialless'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
    
    return response


@views_bp.route('/')
def index():
    """Render the login page."""
    return render_template('login.html', debug=current_app.config.get('DEBUG', False))


@views_bp.route('/dashboard')
def dashboard():
    """Render the dashboard page."""
    return render_template('dashboard.html')


@views_bp.route('/statistics')
def statistics_page():
    """Render the statistics page."""
    return render_template('statistics.html')


@views_bp.route('/history')
def history_page():
    """Render the history page."""
    return render_template('history.html')


@views_bp.route('/api/viewDocument')
def view_document():
    """Render the PDF viewer page.
    
    Authentication via DAT (Document Access Token):
    URL: /api/viewDocument?dat=<jwt_token>
    
    The DAT is a self-contained JWT that:
    - Contains all necessary information in a single token
    - Survives page refresh (F5) without issues
    - Has longer validity (2 hours by default)
    - Doesn't require auth token validation on each request
    """
    jwt_handler = current_app.config['JWT_HANDLER']
    plugin_manager = current_app.config['PLUGIN_MANAGER']
    config = current_app.config['CONFIG']
    
    # Try DAT (Document Access Token) first - preferred method
    dat = request.args.get('dat')
    
    if dat:
        # Validate DAT
        dat_info = jwt_handler.validate_document_token(dat)
        
        if not dat_info:
            return render_template('error.html', 
                                   error='Invalid or expired document access token'), 401
        
        temp_doc_id = dat_info['temp_document_id']
        username = dat_info['username']
        document_id = dat_info['document_id']
        hide_annotations_tools = dat_info['hide_annotations_tools']
        hide_annotations = dat_info['hide_annotations']
        hide_logo = dat_info['hide_logo']
        
        # Check if temp document still exists in cache
        if temp_doc_id not in temp_documents:
            return render_template('error.html', 
                                   error='Document cache expired. Please request a new access token.'), 410
        
        # Record document view
        record_document_view(username, document_id)
        
        # Get customization settings
        customization = config.customization
        
        response = make_response(render_template('viewer.html',
                               temp_doc_id=temp_doc_id,
                               document_id=document_id,
                               dat=dat,  # Pass DAT for API calls
                               token=None,  # No separate token needed
                               customization=customization,
                               hide_annotations_tools=hide_annotations_tools,
                               hide_annotations=hide_annotations,
                               hide_logo=hide_logo))
        
        return add_iframe_headers(response)
    
    # Fallback: tempDocumentId + token authentication
    temp_doc_id = request.args.get('tempDocumentId')
    token = request.args.get('token')
    hide_annotations_tools = request.args.get('hideAnnotationsTools', 'false').lower() == 'true'
    hide_annotations = request.args.get('hideAnnotations', 'false').lower() == 'true'
    hide_logo = request.args.get('hideLogo', 'false').lower() == 'true'
    
    # If hideAnnotations is true, also hide the tools
    if hide_annotations:
        hide_annotations_tools = True
    
    if not temp_doc_id or not token:
        return render_template('error.html', 
                               error='Missing document access token (dat) parameter'), 400
    
    # Validate token
    user = plugin_manager.auth_plugin.validate_token(token)
    
    if not user:
        return render_template('error.html', 
                               error='Invalid or expired token'), 401
    
    # Check if temp document exists and is valid
    if temp_doc_id not in temp_documents:
        return render_template('error.html', 
                               error='Document not found or expired'), 404
    
    doc_info = temp_documents[temp_doc_id]
    
    # Check if document has expired
    expires_at = datetime.fromisoformat(doc_info['expires_at'].rstrip('Z'))
    if datetime.utcnow() > expires_at:
        del temp_documents[temp_doc_id]
        return render_template('error.html', 
                               error='Document has expired'), 410
    
    # Check if user matches
    if doc_info['user'] != user['username']:
        return render_template('error.html', 
                               error='Unauthorized access'), 403
    
    # Record document view
    record_document_view(user['username'], doc_info['document_id'])
    
    # Get customization settings
    customization = config.customization
    
    response = make_response(render_template('viewer.html',
                           temp_doc_id=temp_doc_id,
                           document_id=doc_info['document_id'],
                           dat=None,
                           token=token,
                           customization=customization,
                           hide_annotations_tools=hide_annotations_tools,
                           hide_annotations=hide_annotations,
                           hide_logo=hide_logo))
    
    # Add headers to allow iframe embedding from any origin
    return add_iframe_headers(response)


@views_bp.route('/pdf/<temp_doc_id>')
def serve_pdf(temp_doc_id):
    """Serve a cached PDF file.
    
    Supports authentication via:
    - DAT (dat query parameter)
    - Auth token (token query parameter)
    """
    jwt_handler = current_app.config['JWT_HANDLER']
    plugin_manager = current_app.config['PLUGIN_MANAGER']
    
    # Try DAT first
    dat = request.args.get('dat')
    username = None
    
    if dat:
        dat_info = jwt_handler.validate_document_token(dat)
        if dat_info and dat_info['temp_document_id'] == temp_doc_id:
            username = dat_info['username']
    
    # Fallback to token
    if not username:
        token = request.args.get('token')
        if token:
            user = plugin_manager.auth_plugin.validate_token(token)
            if user:
                username = user['username']
    
    if not username:
        abort(401)
    
    # Check if temp document exists
    if temp_doc_id not in temp_documents:
        abort(404)
    
    doc_info = temp_documents[temp_doc_id]
    
    # Check if user matches
    if doc_info['user'] != username:
        abort(403)
    
    # Serve the cached PDF - use absolute path from app root
    config = current_app.config['CONFIG']
    cache_dir_config = config.cache.get('directory', './cache')
    app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cache_dir = os.path.join(app_root, cache_dir_config.lstrip('./'))
    cache_path = os.path.join(cache_dir, f"{temp_doc_id}.pdf")
    
    if not os.path.exists(cache_path):
        abort(404)
    
    response = make_response(send_file(cache_path, mimetype='application/pdf'))
    
    # Add CORS headers for cross-domain PDF access
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response
