/**
 * OpenMark - PDF Viewer JavaScript
 */

// PDF.js configuration
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

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
        
        this.canvas = document.getElementById('pdfCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.annotationsLayer = document.getElementById('annotationsLayer');
        this.pdfContainer = document.getElementById('pdfContainer');
        
        this.init();
    }
    
    async init() {
        await this.loadPDF();
        this.bindEvents();
        await this.loadAnnotations();
    }
    
    async loadPDF() {
        try {
            const loadingTask = pdfjsLib.getDocument(window.OPENMARK.pdfUrl);
            this.pdfDoc = await loadingTask.promise;
            this.totalPages = this.pdfDoc.numPages;
            
            document.getElementById('totalPages').textContent = this.totalPages;
            
            await this.renderPage(1);
        } catch (error) {
            console.error('Error loading PDF:', error);
            this.showToast('Failed to load PDF', 'error');
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
        
        // Tools
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectTool(e.target.closest('.tool-btn').dataset.tool));
        });
        
        // Colors
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectColor(e.target.dataset.color));
        });
        
        // Save
        document.getElementById('saveBtn').addEventListener('click', () => this.saveAnnotations());
        
        // Sidebar toggle
        document.getElementById('toggleSidebar').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('collapsed');
        });
        
        // Canvas interactions
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        
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
    
    selectColor(color) {
        this.currentColor = color;
        
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.color === color);
        });
    }
    
    getCanvasCoordinates(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: (e.clientX - rect.left) / this.scale,
            y: (e.clientY - rect.top) / this.scale
        };
    }
    
    handleCanvasClick(e) {
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
        const x = Math.min(start.x, end.x);
        const y = Math.min(start.y, end.y);
        const width = Math.abs(end.x - start.x);
        const height = Math.abs(end.y - start.y);
        
        if (width < 10 || height < 5) return; // Minimum size
        
        const highlight = {
            id: `highlight_${Date.now()}`,
            page: this.currentPage,
            rects: [{ x, y, width, height }],
            color: this.currentColor,
            created_at: new Date().toISOString()
        };
        
        this.annotations.highlights.push(highlight);
        this.renderAnnotations();
        this.updateAnnotationsList();
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
        
        this.closeNoteModal();
        this.renderAnnotations();
        this.updateAnnotationsList();
    }
    
    deleteCurrentNote() {
        if (!this.currentNote) return;
        
        this.annotations.notes = this.annotations.notes.filter(n => n.id !== this.currentNote.id);
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
                highlight.rects.forEach(rect => {
                    const div = document.createElement('div');
                    div.className = 'highlight-rect';
                    div.style.left = `${rect.x * this.scale}px`;
                    div.style.top = `${rect.y * this.scale}px`;
                    div.style.width = `${rect.width * this.scale}px`;
                    div.style.height = `${rect.height * this.scale}px`;
                    div.style.backgroundColor = highlight.color;
                    div.dataset.id = highlight.id;
                    div.addEventListener('click', () => this.deleteHighlight(highlight.id));
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
                
                div.addEventListener('click', () => this.openNoteModal(note, false));
                this.annotationsLayer.appendChild(div);
            });
    }
    
    deleteHighlight(id) {
        if (confirm('Delete this highlight?')) {
            this.annotations.highlights = this.annotations.highlights.filter(h => h.id !== id);
            this.renderAnnotations();
            this.updateAnnotationsList();
        }
    }
    
    updateAnnotationsList() {
        // Update notes list
        const notesList = document.getElementById('notesList');
        notesList.innerHTML = this.annotations.notes.map(note => `
            <div class="annotation-item" onclick="viewer.goToAnnotation('note', '${note.id}')">
                <div class="page-num">Page ${note.page}</div>
                <div class="content">${this.escapeHtml(note.content) || 'Empty note'}</div>
            </div>
        `).join('') || '<p style="color: #999; font-size: 12px;">No notes yet</p>';
        
        document.getElementById('notesCount').textContent = this.annotations.notes.length;
        
        // Update highlights list
        const highlightsList = document.getElementById('highlightsList');
        highlightsList.innerHTML = this.annotations.highlights.map(highlight => `
            <div class="annotation-item highlight" style="border-left-color: ${highlight.color}" 
                 onclick="viewer.goToAnnotation('highlight', '${highlight.id}')">
                <div class="page-num">Page ${highlight.page}</div>
                <div class="content">Highlight</div>
            </div>
        `).join('') || '<p style="color: #999; font-size: 12px;">No highlights yet</p>';
        
        document.getElementById('highlightsCount').textContent = this.annotations.highlights.length;
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
            const response = await fetch(`/api/getAnnotations?documentId=${window.OPENMARK.documentId}`, {
                headers: {
                    'Authorization': `Bearer ${window.OPENMARK.token}`
                }
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
            const response = await fetch('/api/saveAnnotations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${window.OPENMARK.token}`
                },
                body: JSON.stringify({
                    documentId: window.OPENMARK.documentId,
                    annotations: this.annotations
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Annotations saved successfully', 'success');
            } else {
                this.showToast('Failed to save annotations', 'error');
            }
        } catch (error) {
            console.error('Failed to save annotations:', error);
            this.showToast('Failed to save annotations', 'error');
        }
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
