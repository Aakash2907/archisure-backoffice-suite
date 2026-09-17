import React, { useState } from "react";
import { api } from "../api.js";

export default function UploadPanel({ session }) {
  const [paperId, setPaperId] = useState("");
  const [content, setContent] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function handleUpload(e) {
    e.preventDefault();
    setError("");
    setResult(null);
    try {
      const res = await api.uploadPaper(session.token, paperId, content);
      setResult(res);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h3>Upload question paper</h3>
      <p className="hint">
        Content is encrypted (AES-256-GCM, per-document key wrapped with RSA)
        before it ever touches storage. Only ciphertext is persisted.
      </p>
      <form onSubmit={handleUpload}>
        <label>Paper ID</label>
        <input value={paperId} onChange={(e) => setPaperId(e.target.value)} required />

        <label>Question paper content</label>
        <textarea rows={6} value={content} onChange={(e) => setContent(e.target.value)} required />

        {error && <p className="error">{error}</p>}
        <button type="submit">Encrypt &amp; upload</button>
      </form>

      {result && (
        <div className="result">
          <p>Uploaded <strong>{result.paper_id}</strong> (version {result.version})</p>
          <p className="mono">sha256: {result.sha256}</p>
        </div>
      )}
    </div>
  );
}
