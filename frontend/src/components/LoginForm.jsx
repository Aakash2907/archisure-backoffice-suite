import React, { useEffect, useState } from "react";
import { api } from "../api.js";

export default function LoginForm({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [error, setError] = useState("");
  const [demoAccounts, setDemoAccounts] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.demoAccounts().then(setDemoAccounts).catch(() => {});
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const session = await api.login(username, password, totpCode);
      onLogin(session);
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setBusy(false);
    }
  }function fillDemo(name, info) {
    setUsername(name);
    setPassword(info.password);
    setTotpCode(info.current_totp_code);
  }

  return (
    <div className="card">
      <h2>Sign in</h2>
      <form onSubmit={handleSubmit}>
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} required />

        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />

        <label>TOTP code (6 digits)</label>
        <input
          value={totpCode}
          onChange={(e) => setTotpCode(e.target.value)}
          maxLength={6}
          required
        />

        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
    </form>

      {demoAccounts && (
        <div className="demo-box">
          <p className="hint">
            Demo accounts (password + a <em>live</em> TOTP code, fetched from a
            demo-only endpoint that a real deployment would remove). Click one to
            autofill:
          </p>
          <ul>
            {Object.entries(demoAccounts).map(([name, info]) => (
              <li key={name}>
                <button type="button" className="link-btn" onClick={() => fillDemo(name, info)}>
                  {name} &mdash; {info.role}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}