import React, { useState } from "react";
import { api } from "../api.js";

export default function ReleasePanel({ session }) {
  const [paperId, setPaperId] = useState("");
  const [releaseAt, setReleaseAt] = useState("");
  const [windowMinutes, setWindowMinutes] = useState(30);
  const [requiredApprovals, setRequiredApprovals] = useState(2);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");

  async function handleConfigure(e) {
    e.preventDefault();
    setError("");
    try {
      const iso = new Date(releaseAt).toISOString();
      const res = await api.configureRelease(session.token, paperId, iso, Number(windowMinutes), Number(requiredApprovals));
      setStatus(res);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleApprove() {
    setError("");
    try {
      const res = await api.approveRelease(session.token, paperId);
      setStatus(res);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleCheckStatus() {
    setError("");
    try {
      const res = await api.releaseStatus(session.token, paperId);
      setStatus(res);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h3>Release control (dual control + time lock)</h3>
      <p className="hint">
        A paper only becomes retrievable once <strong>both</strong> gates are open:
        the configured number of distinct Release Approvers have approved,
        <em> and</em> the current time is inside the release window.
      </p>

      <form onSubmit={handleConfigure}>
        <label>Paper ID</label>
        <input value={paperId} onChange={(e) => setPaperId(e.target.value)} required />

        <label>Release opens at</label>
        <input type="datetime-local" value={releaseAt} onChange={(e) => setReleaseAt(e.target.value)} required />

        <label>Window length (minutes)</label>
        <input type="number" min={1} value={windowMinutes} onChange={(e) => setWindowMinutes(e.target.value)} />

        <label>Required distinct approvals</label>
        <input type="number" min={1} value={requiredApprovals} onChange={(e) => setRequiredApprovals(e.target.value)} />

        <div className="btn-row">
          <button type="submit">Configure policy</button>
          <button type="button" onClick={handleApprove}>Approve as {session.username}</button>
          <button type="button" onClick={handleCheckStatus}>Check status</button>
        </div>
      </form>

      {error && <p className="error">{error}</p>}

      {status && (
        <div className="result">
          <p>
            Approvals: {status.approvals_received}/{status.required_approvals}
            {" "}({status.approved_by.join(", ") || "none yet"})
          </p>
          <p>
            Window: {new Date(status.release_at).toLocaleString()} + {status.window_minutes} min
          </p>
          <p className={status.currently_authorized ? "ok" : "warn"}>
            {status.currently_authorized ? "AUTHORIZED" : `NOT AUTHORIZED (${status.reason})`}
          </p>
        </div>
      )}
    </div>
  );
}
