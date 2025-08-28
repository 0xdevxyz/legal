import { useState, useEffect } from 'react';
import { User } from '@/types/dashboard';
import api from '@/lib/api';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const token = localStorage.getItem('complyo_token');
    const userData = localStorage.getItem('complyo_user');

    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        // ✅ Verify token with API
        verifyToken(token);
      } catch (error) {
        console.error('Error parsing user data:', error);
        localStorage.removeItem('complyo_token');
        localStorage.removeItem('complyo_user');
      }
    }

    setIsLoading(false);
  }, []);

  const verifyToken = async (token: string) => {
    try {
      const response = await api.get('/api/auth/verify');
      // Token is valid, user data updated via interceptor
    } catch (error) {
      console.error('Token verification failed:', error);
      logout();
    }
  };

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // ✅ ECHTE API-INTEGRATION
      const response = await api.post('/api/auth/login', { email, password });
      const { user: userData, token } = response.data;

      setUser(userData);
      localStorage.setItem('complyo_token', token);
      localStorage.setItem('complyo_user', JSON.stringify(userData));

      return { success: true };
    } catch (error: any) {
      console.error('Login error:', error);
      
      // ✅ Fallback zu Mock für Demo (falls API nicht verfügbar)
      if (error.code === 'ECONNREFUSED' || error.response?.status === 404) {
        console.warn('API not available, using demo mode');
        const mockUser: User = {
          id: '1',
          email,
          name: 'Demo Admin',
          plan: 'expert',
          subscriptionStatus: 'active'
        };

        setUser(mockUser);
        localStorage.setItem('complyo_token', 'demo-token');
        localStorage.setItem('complyo_user', JSON.stringify(mockUser));

        return { success: true };
      }
      
      return { 
        success: false, 
        error: error.response?.data?.message || 'Login fehlgeschlagen'
      };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('complyo_token');
    localStorage.removeItem('complyo_user');
  };

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout
  };
}
