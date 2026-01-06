"""API routes for OpenMark."""

import os
import uuid
import hashlib
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, current_app, g

api_bp = Blueprint('api', __name__)

# In-memory storage for temporary documents and sessions
temp_documents = {}
active_tokens = {}
user_statistics = {}
user_history = {}


def require_auth(f):
    """Decorator to require authentication for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Check query parameter (for viewDocument)
        if not token:
            token = request.args.get('token')
        
        if not token:
            return jsonify({'success': False, 'error': 'Missing authentication token'}), 401
        
        # Validate token
        plugin_manager = current_app.config['PLUGIN_MANAGER']
        user = plugin_manager.auth_plugin.validate_token(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        g.user = user
        g.token = token
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
    """Request a PDF document for viewing."""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Missing request body'}), 400
    
    document_id = data.get('documentId')
    
    if not document_id:
        return jsonify({'success': False, 'error': 'Missing documentId'}), 400
    
    plugin_manager = current_app.config['PLUGIN_MANAGER']
    config = current_app.config['CONFIG']
    
    # Check if document exists
    if not plugin_manager.pdf_plugin.document_exists(document_id):
        return jsonify({'success': False, 'error': 'Document not found'}), 404
    
    # Generate temporary document ID
    temp_doc_id = f"temp_{uuid.uuid4().hex}"
    cache_duration = config.cache.get('duration_seconds', 3600)
    expires_at = datetime.utcnow() + timedelta(seconds=cache_duration)
    
    # Store temporary document mapping
    temp_documents[temp_doc_id] = {
        'document_id': document_id,
        'user': g.user['username'],
        'expires_at': expires_at.isoformat() + 'Z',
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    # Cache the document asynchronously (simplified: sync for now)
    cache_dir = config.cache.get('directory', './cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_path = os.path.join(cache_dir, f"{temp_doc_id}.pdf")
    pdf_data = plugin_manager.pdf_plugin.get_document(document_id)
    
    if pdf_data:
        with open(cache_path, 'wb') as f:
            f.write(pdf_data)
    
    return jsonify({
        'success': True,
        'tempDocumentId': temp_doc_id,
        'expires_at': expires_at.isoformat() + 'Z'
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
