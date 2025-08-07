import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Beim App-Start prüfen, ob ein Token vorhanden ist
    const token = localStorage.getItem('auth_token');
    if (token) {
      try {
        // In Produktion würden wir hier einen API-Call machen, um den Benutzer zu verifizieren
        // Für Demozwecke setzen wir einen Mock-Benutzer
        setUser({
          email: "demo@complyo.tech",
          full_name: "Demo Benutzer",
          subscription_tier: "basic", // free, basic, expert
          company: "Complyo GmbH",
          api_key: "demo-api-key-12345",
          created_at: new Date().toISOString()
        });
      } catch (err) {
        console.error('Authentifizierungsfehler:', err);
        localStorage.removeItem('auth_token');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    setError(null);
    try {
      // In Produktion würden wir hier einen API-Call machen
      // Für Demozwecke simulieren wir eine erfolgreiche Anmeldung
      if (email && password) {
        // Simulieren Sie einen Token
        const mockToken = "demo-jwt-token-" + Math.random().toString(36).substring(2);
        localStorage.setItem('auth_token', mockToken);
        
        // Benutzer setzen
        setUser({
          email: email,
          full_name: email.split('@')[0],
          subscription_tier: "basic", // Demo-Benutzer bekommt basic
          company: "Complyo GmbH",
          api_key: "demo-api-key-" + Math.random().toString(36).substring(2),
          created_at: new Date().toISOString()
        });
        return true;
      } else {
        setError("Bitte geben Sie E-Mail und Passwort ein");
        return false;
      }
    } catch (err) {
      setError(err.message || "Anmeldung fehlgeschlagen");
      return false;
    }
  };

  const register = async (userData) => {
    setError(null);
    try {
      // In Produktion würden wir hier einen API-Call machen
      // Für Demozwecke simulieren wir eine erfolgreiche Registrierung
      if (userData.email && userData.password) {
        // Direkt nach Registrierung anmelden
        return await login(userData.email, userData.password);
      } else {
        setError("Bitte füllen Sie alle erforderlichen Felder aus");
        return false;
      }
    } catch (err) {
      setError(err.message || "Registrierung fehlgeschlagen");
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}
