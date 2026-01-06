/**
 * OpenMark - Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    const openDocumentForm = document.getElementById('openDocumentForm');
    
    if (openDocumentForm) {
        openDocumentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const documentId = document.getElementById('documentId').value;
            const errorMessage = document.getElementById('errorMessage');
            
            errorMessage.style.display = 'none';
            
            try {
                // Request document
                const result = await Auth.apiRequest('/api/requestDocument', {
                    method: 'POST',
                    body: { documentId }
                });
                
                if (result && result.success) {
                    // Redirect to viewer
                    const token = Auth.getToken();
                    window.location.href = `/api/viewDocument?tempDocumentId=${result.tempDocumentId}&token=${token}`;
                } else {
                    errorMessage.textContent = result?.error || 'Failed to open document';
                    errorMessage.style.display = 'block';
                }
            } catch (error) {
                errorMessage.textContent = 'An error occurred. Please try again.';
                errorMessage.style.display = 'block';
            }
        });
    }
});
