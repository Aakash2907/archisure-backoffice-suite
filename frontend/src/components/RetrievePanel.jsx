import React, { useState } from "react";
import { api } from "../api.js";

export default function RetrievePanel({ session }) {
  const [paperId, setPaperId] = useState("");
  const [content, setContent] = useState(null);
  const [error, setError] = useState("");

  async function handleRetrieve(e) {
    e.preventDefault();
    setError("");
    setContent(null);
    try {
      const res = await api.retrievePaper(session.token, paperId);
      setContent(res.content);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h3>Retrieve decrypted paper</h3>
      <p className="hint">
        Only succeeds if the release policy's dual-control approvals AND
        time window are both currently satisfied -- checked server-side on
        every request, not just at login.
      </p>
      <form onSubmit={handleRetrieve}>
        <label>Paper ID</label>
        <input value={paperId} onChange={(e) => setPaperId(e.target.value)} required />
        <button type="submit">Retrieve</button>
      </form>

      {error && <p className="error">{error}</p>}

      {content && (
        <div className="result">
          <h4>Decrypted content</h4>
          <pre className="paper-content">{content}</pre>
        </div>
      )}
    </div>
  );
}
