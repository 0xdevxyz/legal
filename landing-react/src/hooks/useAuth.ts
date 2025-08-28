import { useState, useEffect } from 'react';
import { User } from '@/types/dashboard';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const token = localStorage.getItem('complyo_token');
    const userData = localStorage.getItem('complyo_user');
    
    if (token && userData) {
      try {
        setUser(JSON.parse(userData));
      } catch (error) {
        console.error('Error parsing user data:', error);
        localStorage.removeItem('complyo_token');
        localStorage.removeItem('complyo_user');
      }
    }
    
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // API call would go here
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
    } catch (error) {
      return { success: false, error: 'Login failed' };
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
