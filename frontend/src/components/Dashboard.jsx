import React from "react";
import UploadPanel from "./UploadPanel.jsx";
import ReleasePanel from "./ReleasePanel.jsx";
import RetrievePanel from "./RetrievePanel.jsx";
import AuditLogPanel from "./AuditLogPanel.jsx";

// Mirrors backend/app/core/rbac.py ROLE_PERMISSIONS -- the frontend only
// hides panels the user has no permission for. This is a UX convenience,
// NOT a security boundary: the backend re-checks every permission on
// every request regardless of what the UI shows.
const ROLE_PANELS = {
  QUESTION_SETTER: ["upload"],
  REVIEWER: [],
  RELEASE_APPROVER: ["release"],
  EXAM_CENTER_OPERATOR: ["retrieve"],
  AUDITOR: ["audit"],
  ADMIN: [],
};

export default function Dashboard({ session, onLogout }) {
  const panels = ROLE_PANELS[session.role] || [];

  return (
    <div>
      <header className="topbar">
        <div>
          Signed in as <strong>{session.username}</strong> ({session.role})
        </div>
        <button onClick={onLogout}>Sign out</button>
      </header>

      <div className="grid">
        {panels.includes("upload") && <UploadPanel session={session} />}
        {panels.includes("release") && <ReleasePanel session={session} />}
        {panels.includes("retrieve") && <RetrievePanel session={session} />}
        {panels.includes("audit") && <AuditLogPanel session={session} />}

        {panels.length === 0 && (
          <div className="card">
            <p className="hint">
              Your role ({session.role}) has no content-access permissions in
              this system by design (e.g. ADMIN manages users but never
              accesses papers; REVIEWER sees metadata only in a fuller build).
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
