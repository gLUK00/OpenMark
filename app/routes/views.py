"""View routes for OpenMark."""

import os
from datetime import datetime

from flask import Blueprint, request, render_template, redirect, url_for, current_app, send_file, abort

from app.routes.api import temp_documents, require_auth, record_document_view

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def index():
    """Render the login page."""
    return render_template('login.html')


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
    """Render the PDF viewer page."""
    temp_doc_id = request.args.get('tempDocumentId')
    token = request.args.get('token')
    
    if not temp_doc_id or not token:
        return render_template('error.html', 
                               error='Missing tempDocumentId or token'), 400
    
    # Validate token
    plugin_manager = current_app.config['PLUGIN_MANAGER']
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
    config = current_app.config['CONFIG']
    customization = config.customization
    
    return render_template('viewer.html',
                           temp_doc_id=temp_doc_id,
                           document_id=doc_info['document_id'],
                           token=token,
                           customization=customization)


@views_bp.route('/pdf/<temp_doc_id>')
def serve_pdf(temp_doc_id):
    """Serve a cached PDF file."""
    token = request.args.get('token')
    
    if not token:
        abort(401)
    
    # Validate token
    plugin_manager = current_app.config['PLUGIN_MANAGER']
    user = plugin_manager.auth_plugin.validate_token(token)
    
    if not user:
        abort(401)
    
    # Check if temp document exists
    if temp_doc_id not in temp_documents:
        abort(404)
    
    doc_info = temp_documents[temp_doc_id]
    
    # Check if user matches
    if doc_info['user'] != user['username']:
        abort(403)
    
    # Serve the cached PDF
    config = current_app.config['CONFIG']
    cache_dir = config.cache.get('directory', './cache')
    cache_path = os.path.join(cache_dir, f"{temp_doc_id}.pdf")
    
    if not os.path.exists(cache_path):
        abort(404)
    
    return send_file(cache_path, mimetype='application/pdf')
