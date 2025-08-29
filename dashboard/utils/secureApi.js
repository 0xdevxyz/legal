/**
 * Secure API Client for Complyo Frontend
 * JWT authentication, secure storage, and comprehensive error handling
 */

class SecureApiClient {
    constructor() {
        this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        this.tokenKey = 'complyo_access_token';
        this.refreshTokenKey = 'complyo_refresh_token';
        
        // Create secure storage interface
        this.storage = this.createSecureStorage();
        
        // Request interceptors
        this.requestInterceptors = [];
        this.responseInterceptors = [];
        
        // Setup default interceptors
        this.setupAuthInterceptor();
    }
    
    createSecureStorage() {
        /**
         * Secure storage that uses sessionStorage for tokens to prevent XSS
         */
        return {
            getItem: (key) => {
                if (typeof window === 'undefined') return null;
                
                // Use sessionStorage for better security (tokens cleared on tab close)
                try {
                    return sessionStorage.getItem(key) || localStorage.getItem(key);
                } catch (e) {
                    console.warn('Storage access failed:', e);
                    return null;
                }
            },
            
            setItem: (key, value, persistent = false) => {
                if (typeof window === 'undefined') return;
                
                try {
                    if (persistent) {
                        localStorage.setItem(key, value);
                    } else {
                        sessionStorage.setItem(key, value);
                    }
                } catch (e) {
                    console.warn('Storage write failed:', e);
                }
            },
            
            removeItem: (key) => {
                if (typeof window === 'undefined') return;
                
                try {
                    sessionStorage.removeItem(key);
                    localStorage.removeItem(key);
                } catch (e) {
                    console.warn('Storage removal failed:', e);
                }
            }
        };
    }
    
    setupAuthInterceptor() {
        /**
         * Automatically add JWT token to requests
         */
        this.addRequestInterceptor((config) => {
            const token = this.getAccessToken();
            if (token) {
                config.headers = config.headers || {};
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        });
        
        // Response interceptor for token refresh
        this.addResponseInterceptor(
            (response) => response,
            async (error) => {
                if (error.status === 401 && !error.config._retry) {
                    error.config._retry = true;
                    
                    try {
                        await this.refreshAccessToken();
                        // Retry original request with new token
                        return this.request(error.config);
                    } catch (refreshError) {
                        this.logout();
                        window.location.href = '/auth/login';
                        throw refreshError;
                    }
                }
                throw error;
            }
        );
    }
    
    addRequestInterceptor(interceptor) {
        this.requestInterceptors.push(interceptor);
    }
    
    addResponseInterceptor(onSuccess, onError) {
        this.responseInterceptors.push({ onSuccess, onError });
    }
    
    async request(config) {
        /**
         * Enhanced fetch with interceptors and error handling
         */
        try {
            // Apply request interceptors
            let finalConfig = { ...config };
            for (const interceptor of this.requestInterceptors) {
                finalConfig = interceptor(finalConfig) || finalConfig;
            }
            
            // Build URL
            const url = finalConfig.url.startsWith('http') 
                ? finalConfig.url 
                : `${this.baseURL}${finalConfig.url}`;
            
            // Prepare fetch options
            const options = {
                method: finalConfig.method || 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    ...finalConfig.headers
                }
            };
            
            // Add body for POST/PUT requests
            if (finalConfig.data && ['POST', 'PUT', 'PATCH'].includes(options.method)) {
                options.body = JSON.stringify(finalConfig.data);
            }
            
            // Make request
            const response = await fetch(url, options);
            
            // Handle response
            let responseData;
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json();
            } else {
                responseData = await response.text();
            }
            
            const result = {
                data: responseData,
                status: response.status,
                statusText: response.statusText,
                headers: response.headers,
                config: finalConfig
            };
            
            if (!response.ok) {
                const error = new Error(responseData?.message || response.statusText);
                error.response = result;
                error.status = response.status;
                error.config = finalConfig;
                throw error;
            }
            
            // Apply response interceptors
            let finalResult = result;
            for (const interceptor of this.responseInterceptors) {
                if (interceptor.onSuccess) {
                    finalResult = interceptor.onSuccess(finalResult) || finalResult;
                }
            }
            
            return finalResult;
            
        } catch (error) {
            // Apply error interceptors
            for (const interceptor of this.responseInterceptors) {
                if (interceptor.onError) {
                    try {
                        return await interceptor.onError(error);
                    } catch (e) {
                        error = e;
                    }
                }
            }
            throw error;
        }
    }
    
    // Convenience methods
    get(url, config = {}) {
        return this.request({ ...config, method: 'GET', url });
    }
    
    post(url, data, config = {}) {
        return this.request({ ...config, method: 'POST', url, data });
    }
    
    put(url, data, config = {}) {
        return this.request({ ...config, method: 'PUT', url, data });
    }
    
    delete(url, config = {}) {
        return this.request({ ...config, method: 'DELETE', url });
    }
    
    // Authentication methods
    getAccessToken() {
        return this.storage.getItem(this.tokenKey);
    }
    
    getRefreshToken() {
        return this.storage.getItem(this.refreshTokenKey);
    }
    
    setTokens(accessToken, refreshToken, rememberMe = false) {
        this.storage.setItem(this.tokenKey, accessToken, rememberMe);
        if (refreshToken) {
            this.storage.setItem(this.refreshTokenKey, refreshToken, rememberMe);
        }
    }
    
    clearTokens() {
        this.storage.removeItem(this.tokenKey);
        this.storage.removeItem(this.refreshTokenKey);
    }
    
    async login(email, password, rememberMe = false) {
        try {
            const response = await this.post('/api/auth/login', {
                email,
                password,
                remember_me: rememberMe
            });
            
            const { access_token, refresh_token } = response.data;
            this.setTokens(access_token, refresh_token, rememberMe);
            
            return response.data;
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    }
    
    async register(userData) {
        try {
            const response = await this.post('/api/auth/register', userData);
            return response.data;
        } catch (error) {
            console.error('Registration failed:', error);
            throw error;
        }
    }
    
    async logout() {
        try {
            // Call logout endpoint to blacklist token
            await this.post('/api/auth/logout');
        } catch (error) {
            console.warn('Logout API call failed:', error);
        } finally {
            // Always clear local tokens
            this.clearTokens();
        }
    }
    
    async refreshAccessToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }
        
        try {
            const response = await this.post('/api/auth/refresh', {
                refresh_token: refreshToken
            });
            
            const { access_token, refresh_token: newRefreshToken } = response.data;
            this.setTokens(access_token, newRefreshToken || refreshToken);
            
            return response.data;
        } catch (error) {
            this.clearTokens();
            throw error;
        }
    }
    
    async getCurrentUser() {
        try {
            const response = await this.get('/api/auth/me');
            return response.data;
        } catch (error) {
            console.error('Failed to get current user:', error);
            throw error;
        }
    }
    
    isAuthenticated() {
        return !!this.getAccessToken();
    }
    
    // Workflow API methods
    async startJourney(websiteUrl, skillLevel = 'beginner') {
        try {
            const response = await this.post('/api/workflow/start-journey', {
                website_url: websiteUrl,
                skill_level: skillLevel
            });
            return response.data;
        } catch (error) {
            console.error('Failed to start journey:', error);
            throw error;
        }
    }
    
    async getCurrentStep() {
        try {
            const response = await this.get('/api/workflow/current-step');
            return response.data;
        } catch (error) {
            console.error('Failed to get current step:', error);
            throw error;
        }
    }
    
    async completeStep(stepId, validationData) {
        try {
            const response = await this.post('/api/workflow/complete-step', {
                step_id: stepId,
                validation_data: validationData
            });
            return response.data;
        } catch (error) {
            console.error('Failed to complete step:', error);
            throw error;
        }
    }
    
    async getProgress() {
        try {
            const response = await this.get('/api/workflow/progress');
            return response.data;
        } catch (error) {
            console.error('Failed to get progress:', error);
            throw error;
        }
    }
    
    // Error handling helper
    handleApiError(error) {
        console.error('API Error:', error);
        
        // Rate limiting
        if (error.status === 429) {
            const retryAfter = error.response?.headers?.get('Retry-After');
            return {
                type: 'rate_limit',
                message: `Too many requests. Please wait ${retryAfter || '60'} seconds.`,
                retryAfter: parseInt(retryAfter) || 60
            };
        }
        
        // Authentication errors
        if (error.status === 401) {
            return {
                type: 'auth_error',
                message: 'Please log in to continue.',
                requiresAuth: true
            };
        }
        
        // Validation errors
        if (error.status === 400) {
            return {
                type: 'validation_error',
                message: error.response?.data?.message || 'Invalid request data.',
                details: error.response?.data
            };
        }
        
        // Server errors
        if (error.status >= 500) {
            return {
                type: 'server_error',
                message: 'Server error. Please try again later.',
                shouldRetry: true
            };
        }
        
        // Network errors
        if (!error.status) {
            return {
                type: 'network_error',
                message: 'Network error. Please check your connection.',
                shouldRetry: true
            };
        }
        
        return {
            type: 'unknown_error',
            message: error.message || 'An unexpected error occurred.',
            shouldRetry: false
        };
    }
}

// Create and export singleton instance
const secureApi = new SecureApiClient();

export default secureApi;

// Export individual methods for convenience
export const {
    login,
    register,
    logout,
    getCurrentUser,
    isAuthenticated,
    startJourney,
    getCurrentStep,
    completeStep,
    getProgress,
    handleApiError
} = secureApi;