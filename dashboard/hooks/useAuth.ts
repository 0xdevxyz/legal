import { useState, useEffect } from 'react';
import { authService } from '../services/auth';
import { ComplyoAccessibility } from '../services/accessibility-framework';

interface User {
  id: string;
  email: string;
  name: string;
  subscription_status: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [a11y, setA11y] = useState<ComplyoAccessibility | null>(null);

  // Initialize accessibility framework
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const accessibility = ComplyoAccessibility.init({
        autoFix: true,
        announceChanges: true
      });
      setA11y(accessibility);
      
      // Set document title for screen readers
      document.title = 'Complyo Dashboard - Anmeldung';
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const localUser = authService.getLocalUser();
      if (localUser) {
        setUser(localUser);
      }

      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      a11y?.announce('Anmeldung wird verarbeitet', 'polite');
      const response = await authService.login(email, password);
      setUser(response.user);
      
      // Update document title and announce successful login
      if (typeof window !== 'undefined') {
        document.title = `Complyo Dashboard - Willkommen ${response.user.name}`;
      }
      a11y?.announce(`Erfolgreich angemeldet als ${response.user.name}`, 'polite');
      
      return response;
    } catch (error) {
      a11y?.announceAlert('Anmeldung fehlgeschlagen. Bitte überprüfen Sie Ihre Eingaben.');
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
      setUser(null);
      
      // Update document title and announce logout
      if (typeof window !== 'undefined') {
        document.title = 'Complyo Dashboard - Abgemeldet';
      }
      a11y?.announce('Erfolgreich abgemeldet', 'polite');
    } catch (error) {
      a11y?.announceAlert('Fehler beim Abmelden');
      throw error;
    }
  };

  return {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
    accessibility: a11y,
  };
}
