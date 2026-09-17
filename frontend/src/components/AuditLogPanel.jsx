import React, { useState } from "react";
import { api } from "../api.js";

export default function AuditLogPanel({ session }) {
  const [entries, setEntries] = useState(null);
  const [integrity, setIntegrity] = useState(null);
  const [error, setError] = useState("");

  async function loadLog() {
    setError("");
    try {
      const [log, check] = await Promise.all([
        api.auditLog(session.token),
        api.auditIntegrity(session.token),
      ]);
      setEntries(log);
      setIntegrity(check);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h3>Audit log (read-only, hash-chained)</h3>
      <p className="hint">
        Each entry hashes in the previous entry's hash. If any row were
        edited after the fact, the chain breaks at that point -- detectable
        without needing to trust the storage layer.
      </p>
      <button onClick={loadLog}>Load audit log</button>

      {error && <p className="error">{error}</p>}

      {integrity && (
        <p className={integrity.valid ? "ok" : "warn"}>
          Chain integrity: {integrity.valid ? "VALID" : `BROKEN at entry #${integrity.first_corrupt_index}`}
        </p>
      )}

      {entries && (
        <table className="audit-table">
          <thead>
            <tr>
              <th>#</th><th>Time</th><th>Category</th><th>Actor</th><th>Action</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.index}>
                <td>{e.index}</td>
                <td>{new Date(e.timestamp).toLocaleTimeString()}</td>
                <td>{e.category}</td>
                <td>{e.actor}</td>
                <td>{e.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
