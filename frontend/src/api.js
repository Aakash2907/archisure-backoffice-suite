// src/api.js
// Thin wrapper around fetch(). All calls go through /api, which the Vite
// dev server proxies to the FastAPI backend (see vite.config.js) --
// in production, replace BASE_URL with your deployed backend origin.

const BASE_URL = "/api";

async function request(path, { method = "GET", token, body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await res.json() : await res.text();

  if (!res.ok) {
    const detail = (isJson && data && data.detail) || res.statusText;
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return data;
}

export const api = {
  demoAccounts: () => request("/demo/accounts"),
  register: (username, password, role) =>
    request("/auth/register", { method: "POST", body: { username, password, role } }),
  login: (username, password, totp_code) =>
    request("/auth/login", { method: "POST", body: { username, password, totp_code } }),

  uploadPaper: (token, paper_id, content) =>
    request("/papers/upload", { method: "POST", token, body: { paper_id, content } }),

  configureRelease: (token, paper_id, release_at, window_minutes, required_approvals) =>
    request("/papers/release-policy", {
      method: "POST",
      token,
      body: { paper_id, release_at, window_minutes, required_approvals },
    }),

  approveRelease: (token, paper_id) =>
    request("/papers/approve", { method: "POST", token, body: { paper_id } }),

  releaseStatus: (token, paper_id) =>
    request(`/papers/${encodeURIComponent(paper_id)}/status`, { token }),

  retrievePaper: (token, paper_id) =>
    request(`/papers/${encodeURIComponent(paper_id)}/retrieve`, { token }),

  auditLog: (token) => request("/audit/log", { token }),
  auditIntegrity: (token) => request("/audit/integrity", { token }),
};
