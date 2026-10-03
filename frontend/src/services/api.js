// API Client Helper with Token Interception, Auto-Retry, Pre-Warming, and Cold-Start Resilience

export const API_BASE = import.meta.env.VITE_API_URL || '/api';

// Pre-warm backend immediately on script load so Render starts spinning up before the user clicks anything
try {
  fetch(`${API_BASE}/health`, { mode: 'cors' }).catch(() => {});
} catch (_) {}

export function getSelfieUrl(filename) {
  if (!filename) return null;
  if (filename.startsWith('data:') || filename.startsWith('http')) return filename;
  const token = localStorage.getItem('logitrack_token') || '';
  return `${API_BASE}/attendance/selfie/${filename}?token=${token}`;
}

let activeSlowRequests = 0;

function notifyWarming(isWarming) {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('server-warming', { detail: { warming: isWarming } }));
  }
}

export async function apiRequest(endpoint, options = {}, retries = 2) {
  const token = localStorage.getItem('logitrack_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

  // Start a timer to inform the UI if server is taking > 2.0s to respond (cold start / spin-up)
  let slowTimer = null;
  let markedSlow = false;

  slowTimer = setTimeout(() => {
    markedSlow = true;
    activeSlowRequests++;
    notifyWarming(true);
  }, 2000);

  // Set timeout controller for request (50 seconds to accommodate Render free container cold-start)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeout || 50000);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: options.signal || controller.signal,
    });

    clearTimeout(timeoutId);
    if (slowTimer) clearTimeout(slowTimer);
    if (markedSlow) {
      activeSlowRequests = max(0, activeSlowRequests - 1);
      if (activeSlowRequests === 0) notifyWarming(false);
    }

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
    clearTimeout(timeoutId);
    if (slowTimer) clearTimeout(slowTimer);
    if (markedSlow) {
      activeSlowRequests = max(0, activeSlowRequests - 1);
      if (activeSlowRequests === 0) notifyWarming(false);
    }

    // Auto-retry on network errors or cold-start timeouts (GET or idempotent, or during initial wake up)
    const isNetworkError = error.name === 'AbortError' || error.name === 'TypeError' || error.message.includes('Failed to fetch');
    if (retries > 0 && isNetworkError) {
      console.warn(`[API] Retrying ${endpoint} (${retries} attempts left) due to:`, error.message);
      // Wait 1.5s before retry
      await new Promise(res => setTimeout(res, 1500));
      return apiRequest(endpoint, options, retries - 1);
    }

    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

function max(a, b) {
  return a > b ? a : b;
}
