/**
 * OpenMark - Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    const openDocumentForm = document.getElementById('openDocumentForm');
    const documentIdInput = document.getElementById('documentId');
    const hideAnnotationsToolsCheckbox = document.getElementById('hideAnnotationsTools');
    const hideAnnotationsCheckbox = document.getElementById('hideAnnotations');
    const hideLogoCheckbox = document.getElementById('hideLogo');
    const generatedUrlDisplay = document.getElementById('generatedUrl');
    const copyUrlBtn = document.getElementById('copyUrlBtn');
    const copySuccess = document.getElementById('copySuccess');
    
    // Method URL displays
    const method1Url = document.getElementById('method1Url');
    const method2Url = document.getElementById('method2Url');
    
    /**
     * Get current options string based on checkboxes
     */
    function getOptionsString() {
        let options = '';
        if (hideAnnotationsToolsCheckbox && hideAnnotationsToolsCheckbox.checked) {
            options += '&hideAnnotationsTools=true';
        }
        if (hideAnnotationsCheckbox && hideAnnotationsCheckbox.checked) {
            options += '&hideAnnotations=true';
        }
        if (hideLogoCheckbox && hideLogoCheckbox.checked) {
            options += '&hideLogo=true';
        }
        return options;
    }
    
    /**
     * Update the method URLs to reflect current options
     */
    function updateMethodUrls() {
        const options = getOptionsString();
        
        // Update Method 1 URL (now using DAT)
        if (method1Url) {
            method1Url.textContent = `/api/viewDocument?dat=<Document Access Token>${options}`;
        }
        
        // Update Method 2 URL (now using DAT)
        if (method2Url) {
            method2Url.textContent = `/api/viewDocument?dat=<Document Access Token>${options}`;
        }
    }
    
    /**
     * Generate the preview URL based on current form values
     */
    function generatePreviewUrl() {
        const documentId = documentIdInput ? documentIdInput.value.trim() : '';
        
        // Update method URLs with current options
        updateMethodUrls();
        
        if (!documentId) {
            if (generatedUrlDisplay) {
                generatedUrlDisplay.textContent = 'Enter a document ID to generate URL';
                generatedUrlDisplay.classList.remove('has-url');
            }
            if (copyUrlBtn) {
                copyUrlBtn.disabled = true;
            }
            return null;
        }
        
        const baseUrl = window.location.origin;
        let url = `${baseUrl}/api/viewDocument?dat=<Document Access Token>`;
        url += getOptionsString();
        
        if (generatedUrlDisplay) {
            generatedUrlDisplay.textContent = url;
            generatedUrlDisplay.classList.add('has-url');
        }
        if (copyUrlBtn) {
            copyUrlBtn.disabled = false;
        }
        
        return url;
    }
    
    /**
     * Copy text to clipboard with visual feedback
     */
    async function copyToClipboard(text, feedbackElement) {
        try {
            await navigator.clipboard.writeText(text);
            showCopySuccess(feedbackElement);
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showCopySuccess(feedbackElement);
        }
    }
    
    /**
     * Show copy success feedback
     */
    function showCopySuccess(element) {
        if (element) {
            element.style.display = 'inline';
            setTimeout(() => {
                element.style.display = 'none';
            }, 2000);
        }
    }
    
    // Update URL preview when inputs change
    if (documentIdInput) {
        documentIdInput.addEventListener('input', generatePreviewUrl);
    }
    if (hideAnnotationsToolsCheckbox) {
        hideAnnotationsToolsCheckbox.addEventListener('change', generatePreviewUrl);
    }
    if (hideAnnotationsCheckbox) {
        hideAnnotationsCheckbox.addEventListener('change', generatePreviewUrl);
    }
    if (hideLogoCheckbox) {
        hideLogoCheckbox.addEventListener('change', generatePreviewUrl);
    }
    
    // Copy Live URL button
    if (copyUrlBtn) {
        copyUrlBtn.addEventListener('click', async () => {
            const url = generatedUrlDisplay.textContent;
            if (url && !copyUrlBtn.disabled) {
                await copyToClipboard(url, copySuccess);
            }
        });
    }
    
    // Copy URL buttons for method 1 and method 2
    document.querySelectorAll('.copy-url-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const targetId = btn.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            const feedbackElement = btn.nextElementSibling;
            
            if (targetElement) {
                await copyToClipboard(targetElement.textContent, feedbackElement);
            }
        });
    });
    
    // Form submission
    if (openDocumentForm) {
        openDocumentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const documentId = documentIdInput.value;
            const hideAnnotationsTools = hideAnnotationsToolsCheckbox.checked;
            const hideAnnotations = hideAnnotationsCheckbox.checked;
            const hideLogo = hideLogoCheckbox.checked;
            const errorMessage = document.getElementById('errorMessage');
            
            errorMessage.style.display = 'none';
            
            try {
                // Request document with optional parameters
                const result = await Auth.apiRequest('/api/requestDocument', {
                    method: 'POST',
                    body: { 
                        documentId,
                        hideAnnotationsTools,
                        hideAnnotations,
                        hideLogo
                    }
                });
                
                if (result && result.success) {
                    // Use DAT (Document Access Token) if available, fallback to legacy format
                    let viewUrl;
                    if (result.dat) {
                        viewUrl = `/api/viewDocument?dat=${result.dat}`;
                    } else {
                        // Fallback to legacy format
                        const token = Auth.getToken();
                        viewUrl = `/api/viewDocument?tempDocumentId=${result.tempDocumentId}&token=${token}`;
                        if (hideAnnotationsTools) viewUrl += '&hideAnnotationsTools=true';
                        if (hideAnnotations) viewUrl += '&hideAnnotations=true';
                        if (hideLogo) viewUrl += '&hideLogo=true';
                    }
                    
                    window.location.href = viewUrl;
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
    
    // Initialize URL preview
    generatePreviewUrl();
});
