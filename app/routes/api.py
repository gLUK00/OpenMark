"""API routes for OpenMark."""

import os
import uuid
import hashlib
import threading
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, current_app, g

from app.jwt_handler import get_jwt_handler

api_bp = Blueprint('api', __name__)

# In-memory storage for temporary documents and sessions
temp_documents = {}
download_status = {}  # Track download status: 'pending', 'downloading', 'ready', 'error'
active_tokens = {}
user_statistics = {}
user_history = {}


def format_duration(seconds):
    """Format duration in seconds to human-readable string."""
    hours = seconds // 3600
    if hours >= 1:
        return f"{hours} hour{'s' if hours > 1 else ''}"
    minutes = seconds // 60
    return f"{minutes} minute{'s' if minutes > 1 else ''}"


def require_auth(f):
    """Decorator to require authentication for API endpoints.
    
    Supports multiple authentication methods:
    1. Bearer token in Authorization header
    2. token query parameter
    3. DAT (Document Access Token) query parameter
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        jwt_handler = get_jwt_handler()
        plugin_manager = current_app.config['PLUGIN_MANAGER']
        
        # Try DAT (Document Access Token) first
        dat = request.args.get('dat')
        if dat and jwt_handler:
            dat_info = jwt_handler.validate_document_token(dat)
            if dat_info:
                g.user = {'username': dat_info['username'], 'role': 'user'}
                g.token = None
                g.dat = dat
                g.dat_info = dat_info
                return f(*args, **kwargs)
        
        # Try Bearer token
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Check query parameter as fallback
        if not token:
            token = request.args.get('token')
        
        if not token:
            return jsonify({'success': False, 'error': 'Missing authentication token'}), 401
        
        # Validate token
        user = plugin_manager.auth_plugin.validate_token(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        g.user = user
        g.token = token
        g.dat = None
        g.dat_info = None
        return f(*args, **kwargs)
    
    return decorated_function


def get_client_ip():
    """Get the client IP address."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


@api_bp.route('/authenticate', methods=['POST'])
def authenticate():
    """Authenticate a user and return a token."""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Missing request body'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Missing username or password'}), 400
    
    plugin_manager = current_app.config['PLUGIN_MANAGER']
    result = plugin_manager.auth_plugin.authenticate(username, password)
    
    if result:
        return jsonify({
            'success': True,
            'token': result['token'],
            'expires_at': result['expires_at']
        })
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401


@api_bp.route('/quickView', methods=['POST'])
def quick_view():
    """Authenticate and request a document in one call, returning the viewer URL.
    
    This API simplifies integration by combining authentication and document
    request into a single call. It returns a ready-to-use URL with a Document
    Access Token (DAT) for embedding the PDF viewer in an iframe or opening 
    in a new tab.
    
    The DAT is a self-contained JWT that includes all necessary information
    to access the document without requiring additional authentication validation.
    This means the page can be refreshed (F5) without losing access as long as
    the DAT is still valid.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Missing request body'}), 400
    
    username = data.get('username')
    password = data.get('password')
    document_id = data.get('documentId')
    
    # Optional view parameters
    hide_annotations_tools = data.get('hideAnnotationsTools', False)
    hide_annotations = data.get('hideAnnotations', False)
    hide_logo = data.get('hideLogo', False)
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Missing username or password'}), 400
    
    if not document_id:
        return jsonify({'success': False, 'error': 'Missing documentId'}), 400
    
    plugin_manager = current_app.config['PLUGIN_MANAGER']
    config = current_app.config['CONFIG']
    jwt_handler = current_app.config['JWT_HANDLER']
    
    # Step 1: Authenticate
    auth_result = plugin_manager.auth_plugin.authenticate(username, password)
    
    if not auth_result:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    # Step 2: Check if document exists
    if not plugin_manager.pdf_plugin.document_exists(document_id):
        return jsonify({'success': False, 'error': 'Document not found'}), 404
    
    # Step 3: Generate temporary document ID and cache settings
    temp_doc_id = f"temp_{uuid.uuid4().hex}"
    cache_duration = config.cache.get('duration_seconds', 3600)
    
    # DAT (Document Access Token) validity: longer than cache to allow viewing
    # Default: 2 hours or cache duration * 4, whichever is longer
    dat_duration = max(7200, cache_duration * 4)
    dat_expires_at = datetime.utcnow() + timedelta(seconds=dat_duration)
    cache_expires_at = datetime.utcnow() + timedelta(seconds=cache_duration)
    
    # Store temporary document mapping
    temp_documents[temp_doc_id] = {
        'document_id': document_id,
        'user': username,
        'expires_at': dat_expires_at.isoformat() + 'Z',  # Use DAT expiry for cache
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    # Initialize download status
    download_status[temp_doc_id] = 'pending'
    
    # Cache the document in background thread
    cache_dir_config = config.cache.get('directory', './cache')
    app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cache_dir = os.path.join(app_root, cache_dir_config.lstrip('./'))
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{temp_doc_id}.pdf")
    
    # Start background download
    def download_pdf():
        try:
            download_status[temp_doc_id] = 'downloading'
            pdf_data = plugin_manager.pdf_plugin.get_document(document_id)
            
            if pdf_data:
                with open(cache_path, 'wb') as f:
                    f.write(pdf_data)
                download_status[temp_doc_id] = 'ready'
            else:
                download_status[temp_doc_id] = 'error'
        except Exception as e:
            print(f"Error downloading PDF {document_id}: {e}")
            download_status[temp_doc_id] = 'error'
    
    thread = threading.Thread(target=download_pdf)
    thread.daemon = True
    thread.start()
    
    # Step 4: Generate Document Access Token (DAT)
    dat = jwt_handler.generate_document_token(
        temp_document_id=temp_doc_id,
        document_id=document_id,
        username=username,
        expires_in_seconds=dat_duration,
        hide_annotations_tools=hide_annotations_tools,
        hide_annotations=hide_annotations,
        hide_logo=hide_logo
    )
    
    # Step 5: Build the viewer URL with DAT only (no separate token needed)
    view_path = f"/api/viewDocument?dat={dat}"
    
    # Calculate human-readable validity
    valid_for = format_duration(dat_duration)
    
    return jsonify({
        'success': True,
        'viewUrl': view_path,
        'dat': dat,
        'validFor': valid_for,
        'expires_at': dat_expires_at.isoformat() + 'Z'
    })


@api_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout and invalidate the current token."""
    plugin_manager = current_app.config['PLUGIN_MANAGER']
    plugin_manager.auth_plugin.invalidate_token(g.token)
    
    return jsonify({'success': True})


@api_bp.route('/requestDocument', methods=['POST'])
@require_auth
def request_document():
    """Request a PDF document for viewing.
    
    Returns a Document Access Token (DAT) that can be used to access 
    the viewer without requiring additional authentication validation.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Missing request body'}), 400
    
    document_id = data.get('documentId')
    
    # Optional view parameters
    hide_annotations_tools = data.get('hideAnnotationsTools', False)
    hide_annotations = data.get('hideAnnotations', False)
    hide_logo = data.get('hideLogo', False)
    
    if not document_id:
        return jsonify({'success': False, 'error': 'Missing documentId'}), 400
    
    plugin_manager = current_app.config['PLUGIN_MANAGER']
    config = current_app.config['CONFIG']
    jwt_handler = current_app.config['JWT_HANDLER']
    
    # Check if document exists
    if not plugin_manager.pdf_plugin.document_exists(document_id):
        return jsonify({'success': False, 'error': 'Document not found'}), 404
    
    # Generate temporary document ID
    temp_doc_id = f"temp_{uuid.uuid4().hex}"
    cache_duration = config.cache.get('duration_seconds', 3600)
    
    # DAT validity: longer than cache to allow viewing
    dat_duration = max(7200, cache_duration * 4)
    dat_expires_at = datetime.utcnow() + timedelta(seconds=dat_duration)
    
    # Store temporary document mapping
    temp_documents[temp_doc_id] = {
        'document_id': document_id,
        'user': g.user['username'],
        'expires_at': dat_expires_at.isoformat() + 'Z',
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    # Initialize download status
    download_status[temp_doc_id] = 'pending'
    
    # Cache the document in background thread
    cache_dir_config = config.cache.get('directory', './cache')
    app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cache_dir = os.path.join(app_root, cache_dir_config.lstrip('./'))
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{temp_doc_id}.pdf")
    
    # Start background download
    def download_pdf():
        try:
            download_status[temp_doc_id] = 'downloading'
            pdf_data = plugin_manager.pdf_plugin.get_document(document_id)
            
            if pdf_data:
                with open(cache_path, 'wb') as f:
                    f.write(pdf_data)
                download_status[temp_doc_id] = 'ready'
            else:
                download_status[temp_doc_id] = 'error'
        except Exception as e:
            print(f"Error downloading PDF {document_id}: {e}")
            download_status[temp_doc_id] = 'error'
    
    thread = threading.Thread(target=download_pdf)
    thread.daemon = True
    thread.start()
    
    # Generate Document Access Token (DAT)
    dat = jwt_handler.generate_document_token(
        temp_document_id=temp_doc_id,
        document_id=document_id,
        username=g.user['username'],
        expires_in_seconds=dat_duration,
        hide_annotations_tools=hide_annotations_tools,
        hide_annotations=hide_annotations,
        hide_logo=hide_logo
    )
    
    return jsonify({
        'success': True,
        'dat': dat,
        'viewUrl': f'/api/viewDocument?dat={dat}',
        'validFor': format_duration(dat_duration),
        'expires_at': dat_expires_at.isoformat() + 'Z'
    })


@api_bp.route('/documentStatus/<temp_doc_id>', methods=['GET'])
def get_document_status(temp_doc_id):
    """Get the download status of a document.
    
    Supports authentication via:
    - DAT (Document Access Token) in query parameter
    - Bearer token in Authorization header
    
    Returns status: 'pending', 'downloading', 'ready', 'error', or 'not_found'
    """
    jwt_handler = current_app.config['JWT_HANDLER']
    plugin_manager = current_app.config['PLUGIN_MANAGER']
    
    # Check for DAT first
    dat = request.args.get('dat')
    username = None
    
    if dat:
        # Validate DAT
        dat_info = jwt_handler.validate_document_token(dat)
        if dat_info and dat_info['temp_document_id'] == temp_doc_id:
            username = dat_info['username']
    
    # Fallback to Bearer token
    if not username:
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if token:
            user = plugin_manager.auth_plugin.validate_token(token)
            if user:
                username = user['username']
    
    if not username:
        return jsonify({
            'success': False,
            'status': 'unauthorized',
            'error': 'Invalid or missing authentication'
        }), 401
    
    if temp_doc_id not in temp_documents:
        return jsonify({
            'success': False,
            'status': 'not_found',
            'error': 'Document not found'
        }), 404
    
    doc_info = temp_documents[temp_doc_id]
    
    # Check if user matches
    if doc_info['user'] != username:
        return jsonify({
            'success': False,
            'status': 'forbidden',
            'error': 'Access denied'
        }), 403
    
    status = download_status.get(temp_doc_id, 'pending')
    
    return jsonify({
        'success': True,
        'status': status,
        'documentId': doc_info['document_id']
    })


@api_bp.route('/saveAnnotations', methods=['POST'])
@require_auth
def save_annotations():
    """Save annotations for a document."""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Missing request body'}), 400
    
    document_id = data.get('documentId')
    annotations = data.get('annotations')
    
    if not document_id:
        return jsonify({'success': False, 'error': 'Missing documentId'}), 400
    
    if annotations is None:
        return jsonify({'success': False, 'error': 'Missing annotations'}), 400
    
    plugin_manager = current_app.config['PLUGIN_MANAGER']
    success = plugin_manager.annotations_plugin.save_annotations(
        g.user['username'],
        document_id,
        annotations
    )
    
    if success:
        # Update statistics
        username = g.user['username']
        if username not in user_statistics:
            user_statistics[username] = {
                'documents_viewed': 0,
                'notes_created': 0,
                'highlights_created': 0
            }
        
        user_statistics[username]['notes_created'] = len(annotations.get('notes', []))
        user_statistics[username]['highlights_created'] = len(annotations.get('highlights', []))
        
        return jsonify({
            'success': True,
            'message': 'Annotations saved successfully'
        })
    
    return jsonify({'success': False, 'error': 'Failed to save annotations'}), 500


@api_bp.route('/getAnnotations', methods=['GET'])
@require_auth
def get_annotations():
    """Get annotations for a document."""
    document_id = request.args.get('documentId')
    
    if not document_id:
        return jsonify({'success': False, 'error': 'Missing documentId'}), 400
    
    plugin_manager = current_app.config['PLUGIN_MANAGER']
    annotations = plugin_manager.annotations_plugin.get_annotations(
        g.user['username'],
        document_id
    )
    
    return jsonify({
        'success': True,
        'annotations': annotations
    })


@api_bp.route('/statistics', methods=['GET'])
@require_auth
def get_statistics():
    """Get usage statistics for the current user."""
    username = g.user['username']
    
    stats = user_statistics.get(username, {
        'documents_viewed': 0,
        'notes_created': 0,
        'highlights_created': 0
    })
    
    stats['last_activity'] = datetime.utcnow().isoformat() + 'Z'
    
    return jsonify({
        'success': True,
        'statistics': stats
    })


@api_bp.route('/history', methods=['GET'])
@require_auth
def get_history():
    """Get document consultation history."""
    username = g.user['username']
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    history = user_history.get(username, [])
    total = len(history)
    
    # Apply pagination
    paginated_history = history[offset:offset + limit]
    
    return jsonify({
        'success': True,
        'history': paginated_history,
        'total': total,
        'limit': limit,
        'offset': offset
    })


def record_document_view(username: str, document_id: str, document_name: str = None):
    """Record a document view in history."""
    if username not in user_history:
        user_history[username] = []
    
    user_history[username].insert(0, {
        'document_id': document_id,
        'document_name': document_name or document_id,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'ip_address': get_client_ip(),
        'duration_seconds': 0
    })
    
    # Update statistics
    if username not in user_statistics:
        user_statistics[username] = {
            'documents_viewed': 0,
            'notes_created': 0,
            'highlights_created': 0
        }
    user_statistics[username]['documents_viewed'] += 1
    
    # Keep only last 1000 entries
    user_history[username] = user_history[username][:1000]
