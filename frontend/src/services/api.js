// API Client Helper with Token Interception

export const API_BASE = import.meta.env.VITE_API_URL || '/api';

export function getSelfieUrl(filename) {
  if (!filename) return null;
  if (filename.startsWith('data:') || filename.startsWith('http')) return filename;
  const token = localStorage.getItem('logitrack_token') || '';
  return `${API_BASE}/attendance/selfie/${filename}?token=${token}`;
}

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('logitrack_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json().catch(() => ({}));

    if (response.status === 401) {
      // Clear token on 401 unauthorized
      localStorage.removeItem('logitrack_token');
      localStorage.removeItem('logitrack_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      throw new Error(data.message || 'Session expired. Please log in again.');
    }

    if (!response.ok) {
      throw new Error(data.message || `Request failed with status ${response.status}`);
    }

    return data;
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}
