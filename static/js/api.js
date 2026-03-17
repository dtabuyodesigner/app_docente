// static/js/api.js

class ApiClient {
    constructor() {
        this.csrfToken = null;
    }

    async init() {
        if (this.initPromise) return this.initPromise;
        
        this.initPromise = (async () => {
            if (!this.csrfToken) {
                try {
                    const response = await window.originalFetch('/api/csrf-token');
                    const data = await response.json();
                    if (data.ok) {
                        this.csrfToken = data.csrf_token;
                    }
                } catch (e) {
                    console.error('Error fetching CSRF token:', e);
                }
            }
        })();
        
        return this.initPromise;
    }

    async fetch(url, options = {}) {
        await this.init();

        const method = options.method ? options.method.toUpperCase() : 'GET';

        if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
            options.headers = options.headers || {};
            // For standard JSON payloads or explicit headers
            if (!(options.body instanceof FormData)) {
                if (!options.headers['Content-Type']) {
                    options.headers['Content-Type'] = 'application/json';
                }
            }
            if (this.csrfToken) {
                options.headers['X-CSRFToken'] = this.csrfToken;
            }
        }

        return window.originalFetch(url, options);
    }
}

// Intercept global fetch only once to prevent infinite recursion
if (!window.originalFetch) {
    window.originalFetch = window.fetch;
    window.apiClient = new ApiClient();
    window.fetch = (url, options) => window.apiClient.fetch(url, options);
}
