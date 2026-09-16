// ---------- API helper ----------
const API = {
  token: localStorage.getItem('token') || null,
  role: localStorage.getItem('role') || null,
  username: localStorage.getItem('username') || null,
  customerId: localStorage.getItem('customerId') || null,

  async call(path, opts = {}) {
    const headers = opts.headers || {};
    if (this.token) headers['Authorization'] = 'Bearer ' + this.token;
    if (opts.body) headers['Content-Type'] = 'application/json';
    const res = await fetch('/api' + path, { ...opts, headers });
    if (res.status === 401) { logout(); throw new Error('session expired'); }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'request failed');
    return data;
  },
  get(path) { return this.call(path); },
  post(path, body) { return this.call(path, { method: 'POST', body: JSON.stringify(body) }); },
  put(path, body) { return this.call(path, { method: 'PUT', body: JSON.stringify(body) }); },
  del(path) { return this.call(path, { method: 'DELETE' }); },
};

const charts = {};
function renderChart(id, config) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(ctx, config);
}

// ---------- Auth ----------
document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();