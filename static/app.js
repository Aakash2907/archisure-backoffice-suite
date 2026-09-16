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
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;
  const errEl = document.getElementById('login-error');
  errEl.textContent = '';
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'login failed');
    API.token = data.token; API.role = data.role; API.username = data.username;
    API.customerId = data.customer_id;
    localStorage.setItem('token', data.token);
    localStorage.setItem('role', data.role);
    localStorage.setItem('username', data.username);
    localStorage.setItem('customerId', data.customer_id || '');
    startApp();
  } catch (err) {
    errEl.textContent = err.message;
  }
});

document.getElementById('logout-btn').addEventListener('click', logout);
function logout() {
  localStorage.clear();
  API.token = null;
  document.getElementById('app').classList.add('hidden');
  document.getElementById('login-screen').classList.remove('hidden');
}

function startApp() {
  document.getElementById('login-screen').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  document.getElementById('user-info').textContent = `${API.username} · ${API.role.replace('_', ' ')}`;
  applyRoleVisibility();
  loadDashboard();
}

function applyRoleVisibility() {
  const restricted = { finance_manager: ['dashboard', 'customers', 'analytics', 'financial'],
                        policy_officer: ['dashboard', 'customers', 'policies', 'insurance'],
                        customer: ['dashboard', 'customers'] };
  const allowed = restricted[API.role];
  document.querySelectorAll('#nav button').forEach(btn => {
    if (allowed && !allowed.includes(btn.dataset.view)) btn.style.display = 'none';
  });
}

// ---------- Navigation ----------
document.querySelectorAll('#nav button').forEach(btn => {
  btn.addEventListener('click', () => switchView(btn.dataset.view));
});
function switchView(view) {
  document.querySelectorAll('#nav button').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
  document.getElementById('view-' + view).classList.remove('hidden');
  const loaders = { dashboard: loadDashboard, customers: loadCustomers, policies: loadPolicies,
                     devices: loadDevices, analytics: loadAnalytics, insurance: loadInsurance,
                     financial: loadFinancial };
  loaders[view] && loaders[view]();
}

// ---------- Dashboard ----------
async function loadDashboard() {
  const d = await API.get('/dashboard');
  const grid = document.getElementById('kpi-grid');
  grid.innerHTML = kpiCard('Sales Target', `$${d.sales_target.toLocaleString()}`) +
    kpiCard('Revenue', `$${d.revenue.toLocaleString()}`, 'accent') +
    kpiCard('Costs', `$${d.costs.toLocaleString()}`) +
    kpiCard('Profit', `$${d.profit.toLocaleString()}`, d.profit >= 0 ? 'accent' : 'warn') +
    kpiCard('Customer Satisfaction', d.customer_satisfaction) +
    kpiCard('Customer Retention', d.retention_rate + '%') +
    kpiCard('Market Share', d.market_share + '%') +
    kpiCard('Active Policies', d.active_policies);

  const trends = await API.get('/dashboard/trends');
  renderChart('chart-rev-cost', { type: 'bar', data: { labels: trends.map(t => t.label),
    datasets: [{ label: 'Revenue', data: trends.map(t => t.revenue), backgroundColor: '#0e8f88' },
               { label: 'Costs', data: trends.map(t => t.cost), backgroundColor: '#d98a2b' }] },
    options: baseChartOpts() });
  renderChart('chart-profit', { type: 'line', data: { labels: trends.map(t => t.label),
    datasets: [{ label: 'Profit', data: trends.map(t => t.profit), borderColor: '#0e8f88',
                 backgroundColor: 'rgba(14,143,136,.15)', fill: true, tension: .3 }] },
    options: baseChartOpts() });
}
function kpiCard(label, value, cls = '') {
  return `<div class="kpi-card"><div class="label">${label}</div><div class="value ${cls}">${value}</div></div>`;
}
function baseChartOpts() { return { responsive: true, plugins: { legend: { labels: { boxWidth: 10 } } } }; }

// ---------- Customers ----------
async function loadCustomers(q = '') {
  const data = await API.get('/customers?per_page=50' + (q ? `&q=${encodeURIComponent(q)}` : ''));
  const tbody = document.querySelector('#customer-table tbody');
  tbody.innerHTML = data.customers.map(c => `
    <tr>
      <td>${c.name}</td><td>${c.email}</td><td>${c.satisfaction_score}</td>
      <td><span class="badge ${c.retained ? 'active' : 'cancelled'}">${c.retained ? 'Retained' : 'Lost'}</span></td>
      <td><button onclick="viewCustomer(${c.id})">View</button></td>
    </tr>`).join('');
}
document.getElementById('customer-search').addEventListener('input', (e) => loadCustomers(e.target.value));
document.getElementById('customer-add-btn').addEventListener('click', () => {
  openModal('Add customer', [
    { name: 'name', label: 'Full name' }, { name: 'email', label: 'Email' }, { name: 'phone', label: 'Phone' },
  ], async (values) => { await API.post('/customers', values); loadCustomers(); });
});
async function viewCustomer(id) {
  const c = await API.get(`/customers/${id}`);
  const panel = document.getElementById('customer-detail');
  panel.classList.remove('hidden');
  panel.innerHTML = `
    <h3>${c.name}</h3>
    <p class="muted">${c.email} · ${c.phone || 'no phone'} · satisfaction ${c.satisfaction_score}</p>
    <strong>Policies</strong>
    <ul>${c.policies.map(p => `<li>${p.product} — $${p.premium} (${p.status})</li>`).join('') || '<li>None</li>'}</ul>
    <strong>Smart devices</strong>
    <ul>${c.devices.map(d => `<li>${d.type} — ${d.status}</li>`).join('') || '<li>None</li>'}</ul>
    <strong>Recent activity</strong>
    <ul>${c.recent_behavior.slice(0, 6).map(b => `<li>${b.action} (${b.service}) — ${new Date(b.timestamp).toLocaleDateString()}</li>`).join('') || '<li>None</li>'}</ul>`;
}

// ---------- Policies ----------
async function loadPolicies(q = '') {
  const policies = await API.get('/policies' + (q ? `?q=${encodeURIComponent(q)}` : ''));
  const tbody = document.querySelector('#policy-table tbody');
  tbody.innerHTML = policies.map(p => `
    <tr>
      <td>${p.customer_name}</td><td>${p.product}</td><td>$${p.premium}</td>
      <td><span class="badge ${p.status}">${p.status}</span></td>
      <td>${p.renewal_date ? new Date(p.renewal_date).toLocaleDateString() : '—'}</td>
      <td>
        <button onclick="renewPolicy(${p.id})">Renew</button>
        <button onclick="cancelPolicy(${p.id})">Cancel</button>
      </td>
    </tr>`).join('');
}
document.getElementById('policy-search').addEventListener('input', (e) => loadPolicies(e.target.value));
async function renewPolicy(id) { await API.post(`/policies/${id}/renew`); loadPolicies(); }
async function cancelPolicy(id) { await API.post(`/policies/${id}/cancel`); loadPolicies(); }
document.getElementById('policy-add-btn').addEventListener('click', async () => {
  const customers = (await API.get('/customers?per_page=100')).customers;
  openModal('New policy', [
    { name: 'customer_id', label: 'Customer', type: 'select',
      options: customers.map(c => ({ value: c.id, label: c.name })) },
    { name: 'product', label: 'Product', type: 'select',
      options: ['Auto Insurance', 'Home Insurance', 'Life Insurance', 'Health Insurance'].map(p => ({ value: p, label: p })) },
    { name: 'premium', label: 'Premium ($)' },
  ], async (values) => { await API.post('/policies', values); loadPolicies(); });
});

// ---------- Devices ----------
async function loadDevices() {
  const devices = await API.get('/devices');
  const tbody = document.querySelector('#device-table tbody');
  tbody.innerHTML = devices.map(d => `
    <tr>
      <td>#${d.customer_id}</td><td>${d.type}</td>
      <td><span class="badge ${d.status}">${d.status}</span></td>
      <td>${new Date(d.last_activity).toLocaleDateString()}</td>
      <td><button onclick="removeDevice(${d.id})">Remove</button></td>
    </tr>`).join('');
}
async function removeDevice(id) { await API.del(`/devices/${id}`); loadDevices(); }
document.getElementById('device-add-btn').addEventListener('click', async () => {
  const customers = (await API.get('/customers?per_page=100')).customers;
  openModal('Register smart device', [
    { name: 'customer_id', label: 'Customer', type: 'select',
      options: customers.map(c => ({ value: c.id, label: c.name })) },
    { name: 'device_type', label: 'Device type', type: 'select',
      options: ['Smart Car Tracker', 'Home Sensor', 'Wearable Health Monitor', 'Smart Thermostat']
        .map(t => ({ value: t, label: t })) },
  ], async (values) => { await API.post('/devices', values); loadDevices(); });
});

// ---------- Analytics ----------
async function loadAnalytics() {
  const a = await API.get('/analytics/behavior');
  renderChart('chart-actions', { type: 'bar', data: {
    labels: Object.keys(a.action_counts), datasets: [{ data: Object.values(a.action_counts), backgroundColor: '#0e8f88' }] },
    options: { ...baseChartOpts(), plugins: { legend: { display: false } } } });
  renderChart('chart-services', { type: 'doughnut', data: {
    labels: Object.keys(a.service_counts), datasets: [{ data: Object.values(a.service_counts),
      backgroundColor: ['#0e8f88', '#d98a2b', '#3b5a8c', '#c14a4a'] } ] }, options: baseChartOpts() });
  const tbody = document.querySelector('#at-risk-table tbody');
  tbody.innerHTML = a.at_risk_customers.map(c => `<tr><td>${c.name}</td><td>${c.satisfaction_score}</td></tr>`).join('')
    || '<tr><td colspan="2">No at-risk customers right now.</td></tr>';
}

// ---------- Data-Driven Insurance ----------
async function loadInsurance() {
  const data = await API.get('/customers?per_page=100');
  const select = document.getElementById('risk-customer-select');
  select.innerHTML = data.customers.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
}
document.getElementById('risk-calc-btn').addEventListener('click', async () => {
  const id = document.getElementById('risk-customer-select').value;
  const r = await API.get(`/insurance/risk/${id}`);
  const el = document.getElementById('risk-result');
  el.classList.remove('hidden');
  el.innerHTML = `
    <h3>Risk score: ${r.risk_score} / 100</h3>
    <p>Recommended premium: <strong>$${r.recommended_premium}</strong></p>
    <p class="muted">Active devices: ${r.factors.active_devices} · Satisfaction: ${r.factors.satisfaction_score} · Claims filed: ${r.factors.claims_filed}</p>
    <p class="muted">${r.note}</p>`;
});

// ---------- Financial ----------
async function loadFinancial() {
  const s = await API.get('/financial/summary');
  document.getElementById('financial-kpi-grid').innerHTML =
    kpiCard('Total Revenue', `$${s.total_revenue.toLocaleString()}`, 'accent') +
    kpiCard('Total Costs', `$${s.total_cost.toLocaleString()}`) +
    kpiCard('Net Profit', `$${s.net_profit.toLocaleString()}`, s.net_profit >= 0 ? 'accent' : 'warn') +
    kpiCard('Profit Margin', s.profit_margin + '%') +
    kpiCard('Personnel Costs', `$${s.personnel_cost.toLocaleString()}`) +
    kpiCard('Maintenance Costs', `$${s.maintenance_cost.toLocaleString()}`);
  renderChart('chart-costs', { type: 'pie', data: {
    labels: ['Personnel', 'Maintenance', 'Other'],
    datasets: [{ data: [s.personnel_cost, s.maintenance_cost,
      Math.max(0, s.total_cost - s.personnel_cost - s.maintenance_cost)],
      backgroundColor: ['#3b5a8c', '#d98a2b', '#9aa5b6'] }] }, options: baseChartOpts() });
}
document.getElementById('cost-add-btn').addEventListener('click', () => {
  openModal('Record cost', [
    { name: 'type', label: 'Type', type: 'select',
      options: [{ value: 'personnel', label: 'Personnel' }, { value: 'maintenance', label: 'Maintenance' }, { value: 'other', label: 'Other' }] },
    { name: 'amount', label: 'Amount ($)' },
  ], async (values) => { await API.post('/costs', { ...values, amount: parseFloat(values.amount) }); loadFinancial(); });
});
document.getElementById('revenue-add-btn').addEventListener('click', () => {
  openModal('Record revenue', [{ name: 'source', label: 'Source' }, { name: 'amount', label: 'Amount ($)' }],
    async (values) => { await API.post('/revenue', { ...values, amount: parseFloat(values.amount) }); loadFinancial(); });
});

// ---------- Generic modal ----------
function openModal(title, fields, onSubmit) {
  const root = document.getElementById('modal-root');
  const fieldsHtml = fields.map(f => {
    if (f.type === 'select') {
      return `<label>${f.label}</label><select name="${f.name}">${f.options.map(o => `<option value="${o.value}">${o.label}</option>`).join('')}</select>`;
    }
    return `<label>${f.label}</label><input name="${f.name}">`;
  }).join('');
  root.innerHTML = `
    <div class="modal-backdrop">
      <form class="modal">
        <h3>${title}</h3>
        ${fieldsHtml}
        <div class="modal-actions">
          <button type="button" class="secondary" id="modal-cancel">Cancel</button>
          <button type="submit" class="primary">Save</button>
        </div>
      </form>
    </div>`;
  const form = root.querySelector('form');
  root.querySelector('#modal-cancel').addEventListener('click', () => root.innerHTML = '');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const values = {};
    fields.forEach(f => values[f.name] = form.elements[f.name].value);
    try { await onSubmit(values); root.innerHTML = ''; }
    catch (err) { alert(err.message); }
  });
}

// ---------- Boot ----------
if (API.token) startApp();
