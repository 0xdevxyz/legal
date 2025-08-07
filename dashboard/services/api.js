const API_URL = 'https://api.complyo.tech';

export const fetchWithAuth = async (url, options = {}) => {
  const token = localStorage.getItem('auth_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers
  };
  
  const response = await fetch(url, {
    ...options,
    headers
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API error: ${response.status}`);
  }
  
  return response.json();
};

// Scan-bezogene API-Aufrufe
export const scanWebsite = async (url) => {
  return fetchWithAuth(`${API_URL}/api/analyze`, {
    method: 'POST',
    body: JSON.stringify({ url })
  });
};

export const getScans = async () => {
  return fetchWithAuth(`${API_URL}/api/scans`);
};

// Benutzer-bezogene API-Aufrufe
export const login = async (email, password) => {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await fetch(`${API_URL}/api/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: formData
  });
  
  if (!response.ok) {
    throw new Error('Login fehlgeschlagen');
  }
  
  const data = await response.json();
  localStorage.setItem('auth_token', data.access_token);
  return data;
};

export const register = async (userData) => {
  return fetch(`${API_URL}/api/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(userData)
  }).then(response => {
    if (!response.ok) {
      throw new Error('Registrierung fehlgeschlagen');
    }
    return response.json();
  });
};

export const getUserProfile = async () => {
  return fetchWithAuth(`${API_URL}/api/users/me`);
};

// Bericht-bezogene API-Aufrufe
export const generateReport = async (scanId, options = {}) => {
  return fetchWithAuth(`${API_URL}/api/reports/generate`, {
    method: 'POST',
    body: JSON.stringify({
      scan_id: scanId,
      include_details: options.includeDetails ?? true,
      language: options.language ?? 'de'
    })
  });
};

export const getReports = async () => {
  return fetchWithAuth(`${API_URL}/api/reports/list`);
};

// Bericht-bezogene API-Aufrufe
export const generateReport = async (scanId, options = {}) => {
  return fetchWithAuth(`${API_URL}/api/reports/generate`, {
    method: 'POST',
    body: JSON.stringify({
      scan_id: scanId,
      include_details: options.includeDetails ?? true,
      language: options.language ?? 'de'
    })
  });
};

export const getReports = async () => {
  return fetchWithAuth(`${API_URL}/api/reports/list`);
};
