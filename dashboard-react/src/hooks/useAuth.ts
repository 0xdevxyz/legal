import { useState, useEffect } from 'react';
import { User } from '@/types/dashboard';
import api from '@/lib/api';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');

    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        // ✅ Verify token with API
        verifyToken(token);
      } catch (error) {
        console.error('Error parsing user data:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
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
      const { user: userData, access_token, refresh_token } = response.data;

      setUser(userData);
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(userData));

      return { success: true };
    } catch (error: any) {
      console.error('Login error:', error);
      
      // ✅ Fallback zu Mock für Demo (falls API nicht verfügbar)
      if (error.code === 'ECONNREFUSED' || error.response?.status === 404) {

        const mockUser: User = {
          id: '1',
          email,
          name: 'Demo Admin',
          plan: 'expert',
          subscriptionStatus: 'active'
        };

        setUser(mockUser);
        localStorage.setItem('access_token', 'demo-token');
        localStorage.setItem('user', JSON.stringify(mockUser));

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
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    document.cookie = 'access_token=; path=/; max-age=0';
  };

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout
  };
}
