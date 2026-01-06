/**
 * OpenMark - Authentication JavaScript
 */

const Auth = {
    TOKEN_KEY: 'openmark_token',
    
    /**
     * Get the stored authentication token
     */
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },
    
    /**
     * Store the authentication token
     */
    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },
    
    /**
     * Remove the stored token
     */
    removeToken() {
        localStorage.removeItem(this.TOKEN_KEY);
    },
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.getToken();
    },
    
    /**
     * Authenticate user with username and password
     */
    async login(username, password) {
        const response = await fetch('/api/authenticate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            this.setToken(data.token);
            return { success: true };
        }
        
        return { success: false, error: data.error || 'Authentication failed' };
    },
    
    /**
     * Logout the current user
     */
    async logout() {
        const token = this.getToken();
        
        if (token) {
            try {
                await fetch('/api/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
            } catch (e) {
                console.error('Logout error:', e);
            }
        }
        
        this.removeToken();
        window.location.href = '/';
    },
    
    /**
     * Make an authenticated API request
     */
    async apiRequest(url, options = {}) {
        const token = this.getToken();
        
        if (!token) {
            window.location.href = '/';
            return null;
        }
        
        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };
        
        if (options.body && typeof options.body === 'object') {
            headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }
        
        const response = await fetch(url, { ...options, headers });
        
        if (response.status === 401) {
            this.removeToken();
            window.location.href = '/';
            return null;
        }
        
        return response.json();
    }
};

// Handle login form
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        // If already authenticated, redirect to dashboard
        if (Auth.isAuthenticated()) {
            window.location.href = '/dashboard';
            return;
        }
        
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorMessage = document.getElementById('errorMessage');
            
            errorMessage.style.display = 'none';
            
            const result = await Auth.login(username, password);
            
            if (result.success) {
                window.location.href = '/dashboard';
            } else {
                errorMessage.textContent = result.error;
                errorMessage.style.display = 'block';
            }
        });
    }
    
    // Handle logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => Auth.logout());
    }
    
    // Check authentication on protected pages
    const protectedPages = ['/dashboard', '/statistics', '/history'];
    if (protectedPages.some(page => window.location.pathname.startsWith(page))) {
        if (!Auth.isAuthenticated()) {
            window.location.href = '/';
        }
    }
});
