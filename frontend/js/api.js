let API_BASE = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
  ? window.location.origin
  : window.location.origin;

if (API_BASE === window.location.origin && !API_BASE.includes('8000')) {
  API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`;
}

const api = {
  getToken: () => localStorage.getItem('ftp_token'),
  setToken: (t) => localStorage.setItem('ftp_token', t),
  clearToken: () => localStorage.removeItem('ftp_token'),
  getUser: () => {
    try { return JSON.parse(localStorage.getItem('ftp_user')); } catch { return null; }
  },
  setUser: (u) => localStorage.setItem('ftp_user', JSON.stringify(u)),
  clearUser: () => localStorage.removeItem('ftp_user'),

  headers: (auth = false) => {
    const h = { 'Content-Type': 'application/json' };
    if (auth && api.getToken()) h['Authorization'] = `Bearer ${api.getToken()}`;
    return h;
  },

  get: async (url, auth = false) => {
    const r = await fetch(`${API_BASE}${url}`, { headers: api.headers(auth) });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${r.status}`); }
    return r.json();
  },

  post: async (url, data, auth = false) => {
    const r = await fetch(`${API_BASE}${url}`, {
      method: 'POST',
      headers: api.headers(auth),
      body: JSON.stringify(data),
    });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${r.status}`); }
    return r.json();
  },

  register: (data) => api.post('/api/auth/register', data),
  login: (data) => api.post('/api/auth/login', data),
  getMe: () => api.get('/api/auth/me', true),
  getPackages: () => api.get('/api/packages'),
  getPublicDashboard: () => api.get('/api/public/dashboard'),
  getUserDashboard: () => api.get('/api/user/dashboard', true),
  subscribe: (data) => api.post('/api/payment/subscribe', data, true),
  getActivities: () => api.get('/api/user/activities', true),
};

function logout() {
  api.clearToken();
  api.clearUser();
  window.location.href = '/frontend/login.html';
}

function formatPKR(n) {
  if (n === 0) return 'PKR 0';
  return 'PKR ' + n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function getUrgencyBadge(urgency) {
  const m = { high: 'danger', medium: 'warning', low: 'info' };
  return `<span class="badge badge-${m[urgency] || 'info'}">${urgency.toUpperCase()}</span>`;
}