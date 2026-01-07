#!/usr/bin/env python3
"""Generate a sample PDF for testing OpenMark."""

from fpdf import FPDF

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)

# Page 1 - Overview
pdf.add_page()
pdf.set_font('Helvetica', 'B', 24)
pdf.cell(0, 15, 'OpenMark', ln=True, align='C')
pdf.set_font('Helvetica', '', 12)
pdf.cell(0, 10, 'PDF Viewer with Annotations', ln=True, align='C')
pdf.ln(10)

pdf.set_font('Helvetica', 'B', 16)
pdf.cell(0, 10, 'Features', ln=True)
pdf.set_font('Helvetica', '', 11)

features = [
    'PDF Visualization - View PDF documents in your browser',
    'Sticky Notes - Create virtual post-it notes on documents',
    'Text Highlighting - Highlight text with customizable colors',
    'Secure Authentication - Multiple auth backends supported',
    'Usage Statistics - Track document views and annotations',
    'History Tracking - View consultation history',
    'Plugin System - Extensible architecture'
]

for feat in features:
    pdf.cell(0, 8, f'  * {feat}', ln=True)

pdf.ln(5)
pdf.set_font('Helvetica', 'B', 16)
pdf.cell(0, 10, 'Quick Start', ln=True)
pdf.set_font('Courier', '', 10)
pdf.multi_cell(0, 6, '''1. python -m venv venv
2. source venv/bin/activate
3. pip install -r requirements.txt
4. python run.py
5. Open http://localhost:5000''')

pdf.ln(5)
pdf.set_font('Helvetica', 'B', 16)
pdf.cell(0, 10, 'Default Credentials', ln=True)
pdf.set_font('Helvetica', '', 11)
pdf.cell(0, 8, '  Username: admin', ln=True)
pdf.cell(0, 8, '  Password: admin123', ln=True)

pdf.ln(5)
pdf.set_font('Helvetica', 'B', 16)
pdf.cell(0, 10, 'API Endpoints', ln=True)
pdf.set_font('Courier', '', 10)

endpoints = [
    'POST /api/authenticate - User authentication',
    'POST /api/requestDocument - Request PDF access',
    'GET  /api/viewDocument - View PDF with annotations',
    'POST /api/saveAnnotations - Save annotations',
    'GET  /api/getAnnotations - Get annotations',
    'GET  /api/statistics - Usage statistics',
    'GET  /api/history - Consultation history',
    'POST /api/logout - Logout'
]

for ep in endpoints:
    pdf.cell(0, 7, f'  {ep}', ln=True)

pdf.ln(5)
pdf.set_font('Helvetica', 'I', 10)
pdf.cell(0, 10, 'This is a sample PDF for testing OpenMark', ln=True, align='C')

# Page 2 - Architecture
pdf.add_page()
pdf.set_font('Helvetica', 'B', 20)
pdf.cell(0, 15, 'Page 2 - Architecture', ln=True, align='C')
pdf.ln(10)
pdf.set_font('Helvetica', '', 11)
pdf.multi_cell(0, 8, '''OpenMark follows a modular architecture with a plugin system for extensibility.

Components:
- Flask Backend: Handles API requests and serves the web interface
- Plugin Manager: Loads and manages authentication, PDF source, and annotations plugins
- PDF Viewer: JavaScript-based viewer using PDF.js library
- Annotations Layer: Overlay for notes and highlights on PDF pages

The application can be deployed using Docker for easy containerization.''')

# Page 3 - Plugin Development
pdf.add_page()
pdf.set_font('Helvetica', 'B', 20)
pdf.cell(0, 15, 'Page 3 - Plugin Development', ln=True, align='C')
pdf.ln(10)
pdf.set_font('Helvetica', '', 11)
pdf.multi_cell(0, 8, '''OpenMark supports three types of plugins:

1. Authentication Plugins
   - Handle user authentication
   - Built-in: Local file-based auth

2. PDF Source Plugins  
   - Retrieve PDF documents
   - Built-in: HTTP/HTTPS and local file

3. Annotations Plugins
   - Store and retrieve annotations
   - Built-in: Local JSON and MongoDB

Each plugin type has a base class that defines the required interface.
Create custom plugins by extending these base classes.''')

# Save PDF
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, 'sample.pdf')
pdf.output(output_path)
print(f'PDF created: {output_path}')
