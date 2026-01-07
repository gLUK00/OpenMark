/**
 * OpenMark - PDF Viewer JavaScript
 */

// PDF.js configuration
pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/lib/pdfjs/pdf.worker.min.js';

class PDFViewer {
    constructor() {
        this.pdfDoc = null;
        this.currentPage = 1;
        this.totalPages = 0;
        this.scale = 1.0;
        this.currentTool = 'select';
        this.currentColor = '#ffff00';
        this.annotations = { notes: [], highlights: [] };
        this.isDrawing = false;
        this.selectionStart = null;
        this.hasUnsavedChanges = false;
        
        // View options
        this.hideAnnotationsTools = window.OPENMARK.hideAnnotationsTools || false;
        this.hideAnnotations = window.OPENMARK.hideAnnotations || false;
        this.hideLogo = window.OPENMARK.hideLogo || false;
        
        // If hideAnnotations is true, also hide the tools
        if (this.hideAnnotations) {
            this.hideAnnotationsTools = true;
        }
        
        this.canvas = document.getElementById('pdfCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.annotationsLayer = document.getElementById('annotationsLayer');
        this.pdfContainer = document.getElementById('pdfContainer');
        
        this.init();
    }
    
    async init() {
        this.applyViewOptions();
        await this.loadPDF();
        this.bindEvents();
        if (!this.hideAnnotations) {
            await this.loadAnnotations();
        }
    }
    
    applyViewOptions() {
        // Hide annotation tools if requested
        if (this.hideAnnotationsTools) {
            // Hide tool buttons (note, highlight, colors, save)
            const noteTool = document.getElementById('noteTool');
            const highlightTool = document.getElementById('highlightTool');
            const colorPicker = document.getElementById('colorPicker');
            const saveBtn = document.getElementById('saveBtn');
            
            if (noteTool) noteTool.style.display = 'none';
            if (highlightTool) highlightTool.style.display = 'none';
            if (colorPicker) colorPicker.style.display = 'none';
            if (saveBtn) saveBtn.style.display = 'none';
            
            // Hide separator before save button
            const separators = document.querySelectorAll('.toolbar-right .toolbar-separator');
            separators.forEach(sep => sep.style.display = 'none');
            
            // Add class to body for CSS targeting
            document.body.classList.add('hide-annotations-tools');
        }
        
        // Hide annotations and sidebar if requested
        if (this.hideAnnotations) {
            const sidebar = document.getElementById('sidebar');
            const showSidebarBtn = document.getElementById('showSidebar');
            
            if (sidebar) sidebar.style.display = 'none';
            if (showSidebarBtn) showSidebarBtn.style.display = 'none';
            
            // Add class to body for CSS targeting
            document.body.classList.add('hide-annotations');
        }
        
        // Hide logo if requested
        if (this.hideLogo) {
            const toolbarBrand = document.querySelector('.toolbar-brand');
            if (toolbarBrand) toolbarBrand.style.display = 'none';
            
            // Add class to body for CSS targeting
            document.body.classList.add('hide-logo');
        }
    }
    
    /**
     * Get authorization headers for API requests.
     * Supports both DAT (preferred) and legacy token.
     */
    getAuthHeaders() {
        if (window.OPENMARK.dat) {
            // DAT doesn't need Authorization header, it's passed as query param
            return {};
        }
        return {
            'Authorization': `Bearer ${window.OPENMARK.token}`
        };
    }
    
    /**
     * Get auth query parameter for API requests.
     */
    getAuthQueryParam() {
        if (window.OPENMARK.dat) {
            return `dat=${window.OPENMARK.dat}`;
        }
        return `token=${window.OPENMARK.token}`;
    }
    
    async waitForDocument() {
        const loadingText = document.querySelector('.loading-text');
        const loadingProgress = document.getElementById('loadingProgress');
        const maxRetries = 60; // 60 retries * 1 second = 60 seconds max wait
        let retries = 0;
        
        while (retries < maxRetries) {
            try {
                // Build URL with appropriate auth (DAT or token)
                const authParam = this.getAuthQueryParam();
                const response = await fetch(
                    `/api/documentStatus/${window.OPENMARK.tempDocumentId}?${authParam}`,
                    {
                        headers: this.getAuthHeaders()
                    }
                );
                
                const data = await response.json();
                
                if (data.status === 'ready') {
                    return true;
                } else if (data.status === 'error') {
                    throw new Error('Failed to download the document from source.');
                } else if (data.status === 'not_found') {
                    throw new Error('Document not found or expired.');
                } else if (data.status === 'forbidden') {
                    throw new Error('Access denied.');
                }
                
                // Update loading text based on status
                if (loadingText) {
                    if (data.status === 'downloading') {
                        loadingText.textContent = 'Downloading PDF from source...';
                    } else if (data.status === 'pending') {
                        loadingText.textContent = 'Preparing document...';
                    }
                }
                if (loadingProgress) {
                    loadingProgress.textContent = '';
                }
                
                // Wait 1 second before checking again
                await new Promise(resolve => setTimeout(resolve, 1000));
                retries++;
                
            } catch (error) {
                if (error.message.includes('Failed to download') || 
                    error.message.includes('not found') ||
                    error.message.includes('Access denied')) {
                    throw error;
                }
                // Network error, retry
                await new Promise(resolve => setTimeout(resolve, 1000));
                retries++;
            }
        }
        
        throw new Error('Document download timed out. Please try again.');
    }
    
    async loadPDF() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        const errorOverlay = document.getElementById('errorOverlay');
        const loadingProgress = document.getElementById('loadingProgress');
        const loadingText = document.querySelector('.loading-text');
        const pageWrapper = document.getElementById('pageWrapper');
        
        // Show loading overlay, hide error and content
        if (loadingOverlay) loadingOverlay.style.display = 'flex';
        if (errorOverlay) errorOverlay.style.display = 'none';
        if (pageWrapper) pageWrapper.style.opacity = '0';
        if (loadingText) loadingText.textContent = 'Preparing document...';
        if (loadingProgress) loadingProgress.textContent = '';
        
        try {
            // First wait for document to be ready
            await this.waitForDocument();
            
            // Update loading text
            if (loadingText) loadingText.textContent = 'Loading PDF...';
            
            const loadingTask = pdfjsLib.getDocument(window.OPENMARK.pdfUrl);
            
            // Track loading progress
            loadingTask.onProgress = (progress) => {
                if (progress.total > 0 && loadingProgress) {
                    const percent = Math.round((progress.loaded / progress.total) * 100);
                    loadingProgress.textContent = `${percent}%`;
                } else if (loadingProgress) {
                    // If total is unknown, show bytes loaded
                    const kb = Math.round(progress.loaded / 1024);
                    loadingProgress.textContent = `${kb} KB loaded`;
                }
            };
            
            this.pdfDoc = await loadingTask.promise;
            this.totalPages = this.pdfDoc.numPages;
            
            document.getElementById('totalPages').textContent = this.totalPages;
            
            // Hide loading overlay, show content
            if (loadingOverlay) loadingOverlay.style.display = 'none';
            if (pageWrapper) pageWrapper.style.opacity = '1';
            
            await this.renderPage(1);
        } catch (error) {
            console.error('Error loading PDF:', error);
            
            // Hide loading overlay, show error
            if (loadingOverlay) loadingOverlay.style.display = 'none';
            
            // Show error overlay with appropriate message
            this.showLoadError(error);
        }
    }
    
    showLoadError(error) {
        const errorOverlay = document.getElementById('errorOverlay');
        const errorMessage = document.getElementById('errorMessage');
        const retryBtn = document.getElementById('retryLoadBtn');
        
        if (!errorOverlay || !errorMessage) {
            this.showToast('Failed to load PDF: ' + error.message, 'error');
            return;
        }
        
        // Determine error message based on error type
        let message = 'An error occurred while loading the document.';
        
        if (error.name === 'MissingPDFException' || error.message.includes('Missing PDF')) {
            message = 'The PDF document was not found. It may have expired or been removed.';
        } else if (error.name === 'InvalidPDFException') {
            message = 'The file is not a valid PDF document.';
        } else if (error.name === 'UnexpectedResponseException') {
            message = 'Server returned an unexpected response. The document may not be ready yet.';
        } else if (error.message.includes('fetch') || error.message.includes('network')) {
            message = 'Network error. Please check your connection and try again.';
        } else if (error.message.includes('401') || error.message.includes('Unauthorized')) {
            message = 'Authentication error. Your session may have expired.';
        } else if (error.message.includes('403') || error.message.includes('Forbidden')) {
            message = 'Access denied. You do not have permission to view this document.';
        } else if (error.message.includes('404')) {
            message = 'Document not found. It may have expired from the cache.';
        } else if (error.message.includes('500') || error.message.includes('502') || error.message.includes('503')) {
            message = 'Server error. Please try again later.';
        } else if (error.message.includes('timeout') || error.message.includes('Timeout')) {
            message = 'The request timed out. The document may be too large or the server is slow.';
        } else if (error.message) {
            message = error.message;
        }
        
        errorMessage.textContent = message;
        errorOverlay.style.display = 'flex';
        
        // Setup retry button
        if (retryBtn) {
            retryBtn.onclick = () => {
                this.loadPDF();
            };
        }
    }
    
    async renderPage(pageNum) {
        if (!this.pdfDoc) return;
        
        const page = await this.pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale: this.scale });
        
        this.canvas.width = viewport.width;
        this.canvas.height = viewport.height;
        
        const renderContext = {
            canvasContext: this.ctx,
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        
        this.currentPage = pageNum;
        document.getElementById('pageInput').value = pageNum;
        
        // Re-render annotations for this page
        this.renderAnnotations();
        
        // Update button states
        document.getElementById('prevPage').disabled = pageNum <= 1;
        document.getElementById('nextPage').disabled = pageNum >= this.totalPages;
    }
    
    bindEvents() {
        // Navigation
        document.getElementById('prevPage').addEventListener('click', () => this.goToPage(this.currentPage - 1));
        document.getElementById('nextPage').addEventListener('click', () => this.goToPage(this.currentPage + 1));
        document.getElementById('pageInput').addEventListener('change', (e) => this.goToPage(parseInt(e.target.value)));
        
        // Zoom
        document.getElementById('zoomIn').addEventListener('click', () => this.zoom(0.25));
        document.getElementById('zoomOut').addEventListener('click', () => this.zoom(-0.25));
        
        // Tools (toggle behavior: clicking active tool deselects it)
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tool = e.target.closest('.tool-btn').dataset.tool;
                // If clicking on already active tool, reset to default
                if (this.currentTool === tool) {
                    this.resetToDefaultTool();
                } else {
                    this.selectTool(tool);
                }
            });
        });
        
        // Colors
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectColor(e.target.dataset.color));
        });
        
        // Save
        document.getElementById('saveBtn').addEventListener('click', () => this.saveAnnotations());
        
        // Sidebar toggle
        document.getElementById('toggleSidebar').addEventListener('click', () => {
            document.getElementById('sidebar').classList.add('collapsed');
            document.getElementById('showSidebar').style.display = 'inline-block';
        });
        
        // Show sidebar button
        document.getElementById('showSidebar').addEventListener('click', () => {
            document.getElementById('sidebar').classList.remove('collapsed');
            document.getElementById('showSidebar').style.display = 'none';
        });
        
        // Click outside PDF container: reset tool to default
        document.addEventListener('click', (e) => this.handleDocumentClick(e));
        
        // Canvas and annotations layer interactions
        // Canvas for when tool is 'select'
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        
        // Annotations layer for when tools are active (note, highlight)
        this.annotationsLayer.addEventListener('click', (e) => this.handleCanvasClick(e));
        this.annotationsLayer.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.annotationsLayer.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.annotationsLayer.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        
        // Mouse wheel for page navigation (only in PDF area)
        this.pdfContainer.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });
        
        // Note modal
        document.getElementById('closeNoteModal').addEventListener('click', () => this.closeNoteModal());
        document.getElementById('saveNote').addEventListener('click', () => this.saveCurrentNote());
        document.getElementById('deleteNote').addEventListener('click', () => this.deleteCurrentNote());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
    }
    
    goToPage(pageNum) {
        if (pageNum < 1 || pageNum > this.totalPages) return;
        this.renderPage(pageNum);
    }
    
    handleWheel(e) {
        // Only change pages if not zooming (Ctrl key not pressed)
        if (e.ctrlKey) return;
        
        // Prevent default scroll behavior
        e.preventDefault();
        
        // Debounce wheel events
        if (this.wheelTimeout) return;
        
        this.wheelTimeout = setTimeout(() => {
            this.wheelTimeout = null;
        }, 150);
        
        // Scroll down = next page, scroll up = previous page
        if (e.deltaY > 0) {
            this.goToPage(this.currentPage + 1);
        } else if (e.deltaY < 0) {
            this.goToPage(this.currentPage - 1);
        }
    }
    
    zoom(delta) {
        this.scale = Math.max(0.25, Math.min(3, this.scale + delta));
        document.getElementById('zoomLevel').textContent = `${Math.round(this.scale * 100)}%`;
        this.renderPage(this.currentPage);
    }
    
    selectTool(tool) {
        this.currentTool = tool;
        
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tool === tool);
        });
        
        this.pdfContainer.className = 'pdf-container';
        if (tool !== 'select') {
            this.pdfContainer.classList.add(`tool-${tool}`);
            this.annotationsLayer.classList.add('active');
        } else {
            this.annotationsLayer.classList.remove('active');
        }
    }
    
    /**
     * Reset to default navigation tool (select)
     */
    resetToDefaultTool() {
        this.selectTool('select');
    }
    
    selectColor(color) {
        this.currentColor = color;
        
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.color === color);
        });
    }
    
    /**
     * Handle clicks on the document to reset tool when clicking outside PDF page
     */
    handleDocumentClick(e) {
        // Only reset if a tool is currently active (not select mode)
        if (this.currentTool === 'select') return;
        
        // Check if click is directly on the PDF page (canvas or annotations layer)
        const isOnPdfPage = e.target.closest('.pdf-page-wrapper') ||
                           e.target.closest('#pdfCanvas') ||
                           e.target.closest('#annotationsLayer');
        
        // Check if click is on a tool button or color picker (don't reset when selecting tools)
        const isOnToolbar = e.target.closest('.tool-btn') || 
                           e.target.closest('.color-btn') ||
                           e.target.closest('.color-picker');
        
        // Check if click is on the note modal (don't reset when editing a note)
        const isOnNoteModal = e.target.closest('#noteModal');
        
        // Check if click is on sidebar (don't reset when interacting with sidebar)
        const isOnSidebar = e.target.closest('.viewer-sidebar');
        
        // Check if click is on the gray area of PDF container (outside the page wrapper)
        const pdfContainer = document.getElementById('pdfContainer');
        const isOnPdfContainerGrayArea = e.target === pdfContainer;
        
        // Reset tool if:
        // - Click is outside PDF page AND not on toolbar/modal/sidebar
        // - OR click is on the gray area surrounding the PDF page
        if ((!isOnPdfPage && !isOnToolbar && !isOnNoteModal && !isOnSidebar) || isOnPdfContainerGrayArea) {
            this.resetToDefaultTool();
        }
    }
    
    getCanvasCoordinates(e) {
        // Use canvas rect for coordinates calculation (works for both canvas and annotations layer clicks)
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: (e.clientX - rect.left) / this.scale,
            y: (e.clientY - rect.top) / this.scale
        };
    }
    
    handleCanvasClick(e) {
        // Ignore clicks on existing annotations (note icons, highlight rects)
        if (e.target.closest('.note') || e.target.closest('.highlight-rect')) {
            return;
        }
        
        if (this.currentTool === 'note') {
            const coords = this.getCanvasCoordinates(e);
            this.createNote(coords.x, coords.y);
        }
    }
    
    handleMouseDown(e) {
        if (this.currentTool === 'highlight') {
            this.isDrawing = true;
            this.selectionStart = this.getCanvasCoordinates(e);
        }
    }
    
    handleMouseMove(e) {
        if (this.isDrawing && this.currentTool === 'highlight') {
            // Show selection preview
            const current = this.getCanvasCoordinates(e);
            this.showSelectionPreview(this.selectionStart, current);
        }
    }
    
    handleMouseUp(e) {
        if (this.isDrawing && this.currentTool === 'highlight') {
            const end = this.getCanvasCoordinates(e);
            this.createHighlight(this.selectionStart, end);
            this.isDrawing = false;
            this.selectionStart = null;
            this.clearSelectionPreview();
        }
    }
    
    showSelectionPreview(start, end) {
        let preview = document.getElementById('selectionPreview');
        if (!preview) {
            preview = document.createElement('div');
            preview.id = 'selectionPreview';
            preview.className = 'text-selection';
            this.annotationsLayer.appendChild(preview);
        }
        
        const x = Math.min(start.x, end.x) * this.scale;
        const y = Math.min(start.y, end.y) * this.scale;
        const width = Math.abs(end.x - start.x) * this.scale;
        const height = Math.abs(end.y - start.y) * this.scale;
        
        preview.style.left = `${x}px`;
        preview.style.top = `${y}px`;
        preview.style.width = `${width}px`;
        preview.style.height = `${height}px`;
    }
    
    clearSelectionPreview() {
        const preview = document.getElementById('selectionPreview');
        if (preview) preview.remove();
    }
    
    createNote(x, y) {
        const note = {
            id: `note_${Date.now()}`,
            page: this.currentPage,
            x: x,
            y: y,
            width: 200,
            height: 150,
            content: '',
            color: this.currentColor,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
        
        this.openNoteModal(note, true);
    }
    
    createHighlight(start, end) {
        const MIN_HIGHLIGHT_SIZE = 5; // Minimum size in pixels
        
        const x = Math.min(start.x, end.x);
        const y = Math.min(start.y, end.y);
        let width = Math.abs(end.x - start.x);
        let height = Math.abs(end.y - start.y);
        
        // Enforce minimum size
        if (width < MIN_HIGHLIGHT_SIZE || height < MIN_HIGHLIGHT_SIZE) return;
        
        const highlight = {
            id: `highlight_${Date.now()}`,
            page: this.currentPage,
            rects: [{ x, y, width, height }],
            color: this.currentColor,
            created_at: new Date().toISOString()
        };
        
        this.annotations.highlights.push(highlight);
        this.markAsModified();
        this.renderAnnotations();
        this.updateAnnotationsList();
        
        // Reset to default tool after creating a highlight
        this.resetToDefaultTool();
    }
    
    openNoteModal(note, isNew = false) {
        this.currentNote = note;
        this.isNewNote = isNew;
        
        document.getElementById('noteContent').value = note.content || '';
        document.getElementById('noteHeader').style.backgroundColor = note.color;
        document.getElementById('deleteNote').style.display = isNew ? 'none' : 'block';
        document.getElementById('noteModal').style.display = 'flex';
        
        document.getElementById('noteContent').focus();
    }
    
    closeNoteModal() {
        document.getElementById('noteModal').style.display = 'none';
        this.currentNote = null;
        this.isNewNote = false;
    }
    
    saveCurrentNote() {
        if (!this.currentNote) return;
        
        this.currentNote.content = document.getElementById('noteContent').value;
        this.currentNote.updated_at = new Date().toISOString();
        
        if (this.isNewNote) {
            this.annotations.notes.push(this.currentNote);
        } else {
            const index = this.annotations.notes.findIndex(n => n.id === this.currentNote.id);
            if (index !== -1) {
                this.annotations.notes[index] = this.currentNote;
            }
        }
        
        this.markAsModified();
        this.closeNoteModal();
        this.renderAnnotations();
        this.updateAnnotationsList();
        
        // Reset to default tool after creating/editing a note
        this.resetToDefaultTool();
    }
    
    deleteCurrentNote() {
        if (!this.currentNote) return;
        
        this.annotations.notes = this.annotations.notes.filter(n => n.id !== this.currentNote.id);
        this.markAsModified();
        this.closeNoteModal();
        this.renderAnnotations();
        this.updateAnnotationsList();
    }
    
    renderAnnotations() {
        this.annotationsLayer.innerHTML = '';
        
        // Render highlights for current page
        this.annotations.highlights
            .filter(h => h.page === this.currentPage)
            .forEach(highlight => {
                highlight.rects.forEach((rect, rectIndex) => {
                    const div = document.createElement('div');
                    div.className = 'highlight-rect';
                    div.style.left = `${rect.x * this.scale}px`;
                    div.style.top = `${rect.y * this.scale}px`;
                    div.style.width = `${rect.width * this.scale}px`;
                    div.style.height = `${rect.height * this.scale}px`;
                    div.style.backgroundColor = highlight.color;
                    div.dataset.id = highlight.id;
                    div.dataset.rectIndex = rectIndex;
                    
                    // Add move icon on hover
                    const moveIcon = document.createElement('div');
                    moveIcon.className = 'highlight-move-icon';
                    moveIcon.innerHTML = '✥';
                    div.appendChild(moveIcon);
                    
                    // Add resize handle on hover
                    const resizeHandle = document.createElement('div');
                    resizeHandle.className = 'highlight-resize-handle';
                    resizeHandle.addEventListener('mousedown', (e) => {
                        e.stopPropagation();
                        this.startHighlightResize(e, highlight, rectIndex);
                    });
                    div.appendChild(resizeHandle);
                    
                    // Click to highlight in sidebar
                    div.addEventListener('click', (e) => {
                        if (!this.isDraggingHighlight && !this.isResizingHighlight) {
                            e.stopPropagation();
                            this.flashHighlightInSidebar(highlight.id);
                        }
                    });
                    
                    // Drag to move
                    div.addEventListener('mousedown', (e) => this.startHighlightDrag(e, highlight, rectIndex));
                    
                    this.annotationsLayer.appendChild(div);
                });
            });
        
        // Render notes for current page
        this.annotations.notes
            .filter(n => n.page === this.currentPage)
            .forEach(note => {
                const div = document.createElement('div');
                div.className = 'note';
                div.style.left = `${note.x * this.scale}px`;
                div.style.top = `${note.y * this.scale}px`;
                div.dataset.id = note.id;
                
                div.innerHTML = `
                    <div class="note-icon" style="background-color: ${note.color}">📝</div>
                    <div class="note-preview">${this.escapeHtml(note.content) || 'Empty note'}</div>
                `;
                
                // Click to flash in sidebar, double-click to edit
                div.addEventListener('click', (e) => {
                    if (!this.isDraggingNote) {
                        e.stopPropagation();
                        this.flashNoteInSidebar(note.id);
                    }
                });
                
                div.addEventListener('dblclick', (e) => {
                    e.stopPropagation();
                    this.openNoteModal(note, false);
                });
                
                // Drag to move
                div.addEventListener('mousedown', (e) => this.startNoteDrag(e, note));
                
                this.annotationsLayer.appendChild(div);
            });
    }
    
    deleteHighlight(id) {
        if (confirm('Delete this highlight?')) {
            this.annotations.highlights = this.annotations.highlights.filter(h => h.id !== id);
            this.markAsModified();
            this.renderAnnotations();
            this.updateAnnotationsList();
        }
    }
    
    startHighlightDrag(e, highlight, rectIndex) {
        if (e.button !== 0) return; // Only left click
        
        e.preventDefault();
        e.stopPropagation();
        
        this.isDraggingHighlight = false;
        this.dragHighlight = highlight;
        this.dragRectIndex = rectIndex;
        this.dragStartPos = this.getCanvasCoordinates(e);
        this.dragOriginalRect = { ...highlight.rects[rectIndex] };
        
        const onMouseMove = (moveEvent) => {
            this.isDraggingHighlight = true;
            const currentPos = this.getCanvasCoordinates(moveEvent);
            const deltaX = currentPos.x - this.dragStartPos.x;
            const deltaY = currentPos.y - this.dragStartPos.y;
            
            // Update highlight position
            highlight.rects[rectIndex].x = this.dragOriginalRect.x + deltaX;
            highlight.rects[rectIndex].y = this.dragOriginalRect.y + deltaY;
            
            // Re-render
            this.renderAnnotations();
        };
        
        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            
            // Mark as modified if moved
            if (this.isDraggingHighlight) {
                this.markAsModified();
            }
            
            // Reset drag state after a short delay to prevent click event
            setTimeout(() => {
                this.isDraggingHighlight = false;
                this.dragHighlight = null;
                this.dragRectIndex = null;
            }, 50);
        };
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }
    
    startHighlightResize(e, highlight, rectIndex) {
        if (e.button !== 0) return; // Only left click
        
        const MIN_HIGHLIGHT_SIZE = 5;
        
        e.preventDefault();
        e.stopPropagation();
        
        this.isResizingHighlight = false;
        this.resizeHighlight = highlight;
        this.resizeRectIndex = rectIndex;
        this.resizeStartPos = this.getCanvasCoordinates(e);
        this.resizeOriginalRect = { ...highlight.rects[rectIndex] };
        
        const onMouseMove = (moveEvent) => {
            this.isResizingHighlight = true;
            const currentPos = this.getCanvasCoordinates(moveEvent);
            const deltaX = currentPos.x - this.resizeStartPos.x;
            const deltaY = currentPos.y - this.resizeStartPos.y;
            
            // Calculate new size with minimum constraint
            const newWidth = Math.max(MIN_HIGHLIGHT_SIZE, this.resizeOriginalRect.width + deltaX);
            const newHeight = Math.max(MIN_HIGHLIGHT_SIZE, this.resizeOriginalRect.height + deltaY);
            
            // Update highlight size
            highlight.rects[rectIndex].width = newWidth;
            highlight.rects[rectIndex].height = newHeight;
            
            // Re-render
            this.renderAnnotations();
        };
        
        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            
            // Mark as modified if resized
            if (this.isResizingHighlight) {
                this.markAsModified();
            }
            
            // Reset resize state after a short delay
            setTimeout(() => {
                this.isResizingHighlight = false;
                this.resizeHighlight = null;
                this.resizeRectIndex = null;
            }, 50);
        };
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }
    
    flashHighlightInSidebar(highlightId) {
        // Find the highlight item in sidebar
        const sidebarItem = document.querySelector(`.annotation-item[data-id="${highlightId}"]`);
        if (sidebarItem) {
            // Expand accordion if collapsed
            const highlight = this.annotations.highlights.find(h => h.id === highlightId);
            if (highlight) {
                const section = document.querySelector(`.accordion-section[data-page="${highlight.page}"]`);
                if (section && !section.classList.contains('active')) {
                    this.toggleAccordion(highlight.page);
                }
            }
            
            // Scroll into view
            sidebarItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Add flash animation
            sidebarItem.classList.add('flash');
            setTimeout(() => {
                sidebarItem.classList.remove('flash');
            }, 1500);
        }
    }
    
    startNoteDrag(e, note) {
        if (e.button !== 0) return; // Only left click
        
        e.preventDefault();
        e.stopPropagation();
        
        this.isDraggingNote = false;
        this.dragNote = note;
        this.dragStartPos = this.getCanvasCoordinates(e);
        this.dragOriginalNotePos = { x: note.x, y: note.y };
        
        const noteElement = e.target.closest('.note');
        if (noteElement) {
            noteElement.classList.add('dragging');
        }
        
        const onMouseMove = (moveEvent) => {
            this.isDraggingNote = true;
            const currentPos = this.getCanvasCoordinates(moveEvent);
            const deltaX = currentPos.x - this.dragStartPos.x;
            const deltaY = currentPos.y - this.dragStartPos.y;
            
            // Update note position
            note.x = this.dragOriginalNotePos.x + deltaX;
            note.y = this.dragOriginalNotePos.y + deltaY;
            
            // Re-render
            this.renderAnnotations();
        };
        
        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            
            if (noteElement) {
                noteElement.classList.remove('dragging');
            }
            
            // Mark as modified if moved
            if (this.isDraggingNote) {
                this.markAsModified();
            }
            
            // Reset drag state after a short delay to prevent click event
            setTimeout(() => {
                this.isDraggingNote = false;
                this.dragNote = null;
            }, 50);
        };
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }
    
    flashNoteInSidebar(noteId) {
        // Find the note item in sidebar
        const sidebarItem = document.querySelector(`.annotation-item[data-id="${noteId}"]`);
        if (sidebarItem) {
            // Expand accordion if collapsed
            const note = this.annotations.notes.find(n => n.id === noteId);
            if (note) {
                const section = document.querySelector(`.accordion-section[data-page="${note.page}"]`);
                if (section && !section.classList.contains('active')) {
                    this.toggleAccordion(note.page);
                }
            }
            
            // Scroll into view
            sidebarItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Add flash animation
            sidebarItem.classList.add('flash');
            setTimeout(() => {
                sidebarItem.classList.remove('flash');
            }, 1500);
        }
    }
    
    updateAnnotationsList() {
        const accordion = document.getElementById('pagesAccordion');
        
        // Save the state of expanded sections before rebuilding
        const expandedPages = new Set();
        accordion.querySelectorAll('.accordion-section.active').forEach(section => {
            expandedPages.add(parseInt(section.dataset.page));
        });
        
        accordion.innerHTML = '';
        
        // Group annotations by page
        const pageAnnotations = {};
        
        // Group notes by page
        this.annotations.notes.forEach(note => {
            if (!pageAnnotations[note.page]) {
                pageAnnotations[note.page] = { notes: [], highlights: [] };
            }
            pageAnnotations[note.page].notes.push(note);
        });
        
        // Group highlights by page
        this.annotations.highlights.forEach(highlight => {
            if (!pageAnnotations[highlight.page]) {
                pageAnnotations[highlight.page] = { notes: [], highlights: [] };
            }
            pageAnnotations[highlight.page].highlights.push(highlight);
        });
        
        // Create accordion sections only for pages with annotations
        const pagesToShow = new Set();
        Object.keys(pageAnnotations).forEach(page => {
            const p = parseInt(page);
            if (pageAnnotations[p].notes.length > 0 || pageAnnotations[p].highlights.length > 0) {
                pagesToShow.add(p);
            }
        });
        
        // Sort pages
        const sortedPages = Array.from(pagesToShow).sort((a, b) => a - b);
        
        // Show message if no annotations
        if (sortedPages.length === 0) {
            accordion.innerHTML = '<p class="no-annotations">No annotations in this document</p>';
            return;
        }
        
        sortedPages.forEach(page => {
            const data = pageAnnotations[page];
            const isCurrentPage = page === this.currentPage;
            const wasExpanded = expandedPages.has(page);
            const shouldBeActive = isCurrentPage || wasExpanded;
            const notesCount = data.notes.length;
            const highlightsCount = data.highlights.length;
            
            // Build header text
            let headerText = `Page ${page}`;
            const parts = [];
            if (notesCount > 0) parts.push(`Notes (${notesCount})`);
            if (highlightsCount > 0) parts.push(`Highlights (${highlightsCount})`);
            if (parts.length > 0) {
                headerText += ` - ${parts.join(' - ')}`;
            }
            
            const section = document.createElement('div');
            section.className = `accordion-section${shouldBeActive ? ' active' : ''}`;
            section.dataset.page = page;
            
            section.innerHTML = `
                <div class="accordion-header" onclick="viewer.toggleAccordion(${page})">
                    <span class="accordion-icon">${shouldBeActive ? '▼' : '▶'}</span>
                    <span class="accordion-title">${headerText}</span>
                </div>
                <div class="accordion-content" style="${shouldBeActive ? '' : 'display: none;'}">
                    ${this.renderPageAnnotations(data, page)}
                </div>
            `;
            
            accordion.appendChild(section);
        });
    }
    
    renderPageAnnotations(data, page) {
        let html = '';
        
        if (data.notes.length > 0) {
            html += `<div class="annotation-subsection">
                <div class="subsection-title">📝 Notes (${data.notes.length})</div>
                <div class="annotation-list">`;
            
            data.notes.forEach(note => {
                html += `
                    <div class="annotation-item" data-id="${note.id}" data-type="note">
                        <div class="annotation-item-content" onclick="viewer.goToAnnotation('note', '${note.id}')">
                            <div class="content">${this.escapeHtml(note.content) || 'Empty note'}</div>
                        </div>
                        <button class="annotation-delete-btn" onclick="event.stopPropagation(); viewer.confirmDeleteAnnotation('note', '${note.id}')" title="Delete">×</button>
                    </div>
                `;
            });
            
            html += `</div></div>`;
        }
        
        if (data.highlights.length > 0) {
            html += `<div class="annotation-subsection">
                <div class="subsection-title">🖍️ Highlights (${data.highlights.length})</div>
                <div class="annotation-list">`;
            
            data.highlights.forEach(highlight => {
                html += `
                    <div class="annotation-item highlight" style="border-left-color: ${highlight.color}" data-id="${highlight.id}" data-type="highlight">
                        <div class="annotation-item-content" onclick="viewer.goToAnnotation('highlight', '${highlight.id}')">
                            <div class="content">Highlight</div>
                        </div>
                        <button class="annotation-delete-btn" onclick="event.stopPropagation(); viewer.confirmDeleteAnnotation('highlight', '${highlight.id}')" title="Delete">×</button>
                    </div>
                `;
            });
            
            html += `</div></div>`;
        }
        
        return html;
    }
    
    toggleAccordion(page) {
        const section = document.querySelector(`.accordion-section[data-page="${page}"]`);
        if (!section) return;
        
        const isActive = section.classList.contains('active');
        const content = section.querySelector('.accordion-content');
        const icon = section.querySelector('.accordion-icon');
        
        if (isActive) {
            section.classList.remove('active');
            content.style.display = 'none';
            icon.textContent = '▶';
        } else {
            section.classList.add('active');
            content.style.display = 'block';
            icon.textContent = '▼';
        }
    }
    
    confirmDeleteAnnotation(type, id) {
        const typeName = type === 'note' ? 'cette note' : 'ce surlignage';
        if (confirm(`Voulez-vous vraiment supprimer ${typeName} ?`)) {
            if (type === 'note') {
                this.annotations.notes = this.annotations.notes.filter(n => n.id !== id);
            } else {
                this.annotations.highlights = this.annotations.highlights.filter(h => h.id !== id);
            }
            this.markAsModified();
            this.renderAnnotations();
            this.updateAnnotationsList();
        }
    }
    
    goToAnnotation(type, id) {
        let annotation;
        if (type === 'note') {
            annotation = this.annotations.notes.find(n => n.id === id);
        } else {
            annotation = this.annotations.highlights.find(h => h.id === id);
        }
        
        if (annotation && annotation.page !== this.currentPage) {
            this.goToPage(annotation.page);
        }
    }
    
    async loadAnnotations() {
        try {
            // Build headers with proper auth
            const headers = this.getAuthHeaders();
            const authParam = this.getAuthQueryParam();
            
            const response = await fetch(`/api/getAnnotations?documentId=${window.OPENMARK.documentId}&${authParam}`, {
                headers: headers
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.annotations = data.annotations;
                this.renderAnnotations();
                this.updateAnnotationsList();
            }
        } catch (error) {
            console.error('Failed to load annotations:', error);
        }
    }
    
    async saveAnnotations() {
        try {
            // Build headers with proper auth
            const headers = {
                'Content-Type': 'application/json',
                ...this.getAuthHeaders()
            };
            const authParam = this.getAuthQueryParam();
            
            const response = await fetch(`/api/saveAnnotations?${authParam}`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    documentId: window.OPENMARK.documentId,
                    annotations: this.annotations
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.clearUnsavedChanges();
                this.showToast('Annotations saved successfully', 'success');
            } else {
                this.showToast('Failed to save annotations', 'error');
            }
        } catch (error) {
            console.error('Failed to save annotations:', error);
            this.showToast('Failed to save annotations', 'error');
        }
    }
    
    markAsModified() {
        if (!this.hasUnsavedChanges) {
            this.hasUnsavedChanges = true;
            const saveBtn = document.getElementById('saveBtn');
            saveBtn.classList.add('unsaved');
        }
    }
    
    clearUnsavedChanges() {
        this.hasUnsavedChanges = false;
        const saveBtn = document.getElementById('saveBtn');
        saveBtn.classList.remove('unsaved');
    }
    
    handleKeydown(e) {
        // Escape to close modal
        if (e.key === 'Escape') {
            this.closeNoteModal();
        }
        
        // Ctrl+S to save
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            this.saveAnnotations();
        }
        
        // Arrow keys for navigation
        if (e.key === 'ArrowLeft') {
            this.goToPage(this.currentPage - 1);
        } else if (e.key === 'ArrowRight') {
            this.goToPage(this.currentPage + 1);
        }
    }
    
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.style.display = 'block';
        
        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize viewer
let viewer;
document.addEventListener('DOMContentLoaded', () => {
    viewer = new PDFViewer();
});
