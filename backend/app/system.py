"""
app/system.py
==============
Wires every core module together into one façade class,
`QuestionPaperSystem`, so the API layer (main.py) never touches raw
crypto or storage directly -- every operation goes through: session
check -> RBAC check -> audit log -> the actual work.

A single process-wide instance is created in main.py and reused across
requests (see `get_system()` in deps.py), the same way you'd hold a
DB connection pool or KMS client for the lifetime of the app.
"""

from __future__ import annotations

from datetime import datetime

from .core.auth import AuthService
from .core.rbac import Role, Permission, require_permission
from .core.audit import AuditLog
from .core.storage import SecureStorage
from .core.release_control import ReleaseController, ReleasePolicy
from .core import crypto_utils as cu


class QuestionPaperSystem:
    def __init__(self, vault_root: str = "vault"):
        self.auth = AuthService()
        self.audit = AuditLog()
        self.storage = SecureStorage(root=vault_root)
        self.release = ReleaseController()

        # Org-wide Key Encryption Key pair -- stand-in for a cloud KMS/HSM.
        self._kek_private, self._kek_public = cu.generate_kek_keypair()
        # Separate signing keypair (key separation / defence in depth).
        self._sign_private, self._sign_public = cu.generate_kek_keypair(key_size=2048)

    # ---- Identity -----------------------------------------------------
    def register_user(self, username: str, password: str, role: Role) -> str:
        return self.auth.register_user(username, password, role)

    def login(self, username: str, password: str, totp_code: str):
        return self.auth.login(username, password, totp_code, audit=self.audit)

    def resolve(self, session_token: str):
        return self.auth.get_session(session_token)

    # ---- Upload ---------------------------------------------------------
    def upload_paper(self, session_token: str, paper_id: str, plaintext: bytes):
        session = self.resolve(session_token)
        require_permission(session.role, Permission.UPLOAD_PAPER)

        payload = cu.encrypt_document(plaintext, self._kek_public, self._sign_private)
        record = self.storage.store(paper_id, payload, uploaded_by=session.username)

        self.audit.log("DOCUMENT", session.username, "PAPER_UPLOADED", {
            "paper_id": paper_id,
            "version": record.version,
            "sha256": payload.plaintext_sha256,
        })
        return record

    # ---- Release configuration & approval --------------------------------
    def configure_release(self, session_token: str, paper_id: str,
                           release_at: datetime, window_minutes: int = 30,
                           required_approvals: int = 2):
        session = self.resolve(session_token)
        require_permission(session.role, Permission.APPROVE_RELEASE)
        policy = ReleasePolicy(paper_id=paper_id, release_at=release_at,
                                release_window_minutes=window_minutes,
                                required_approvals=required_approvals)
        self.release.set_policy(policy)
        self.audit.log("RELEASE", session.username, "POLICY_CONFIGURED", {
            "paper_id": paper_id,
            "release_at": release_at.isoformat(),
            "required_approvals": required_approvals,
        })
        return policy

    def approve_release(self, session_token: str, paper_id: str):
        session = self.resolve(session_token)
        require_permission(session.role, Permission.APPROVE_RELEASE)
        self.release.approve(paper_id, session.username, self.audit)
        return self.release._policies[paper_id]

    # ---- Controlled retrieval (decryption) -------------------------------
    def retrieve_paper(self, session_token: str, paper_id: str) -> bytes:
        session = self.resolve(session_token)
        require_permission(session.role, Permission.RETRIEVE_DECRYPTED)

        self.release.authorize_retrieval(paper_id, session.username, self.audit)

        record = self.storage.latest(paper_id)
        payload = self.storage.as_encrypted_payload(record)
        plaintext = cu.decrypt_document(payload, self._kek_private, self._sign_public)

        self.audit.log("DOCUMENT", session.username, "PAPER_RETRIEVED_DECRYPTED", {
            "paper_id": paper_id, "version": record.version,
        })
        return plaintext

    # ---- Read-only views ---------------------------------------------------
    def view_audit_log(self, session_token: str):
        session = self.resolve(session_token)
        require_permission(session.role, Permission.VIEW_AUDIT_LOG)
        return self.audit.entries()

    def audit_integrity(self, session_token: str):
        session = self.resolve(session_token)
        require_permission(session.role, Permission.VIEW_AUDIT_LOG)
        return self.audit.verify_integrity()

    def release_status(self, session_token: str, paper_id: str):
        self.resolve(session_token)  # any authenticated user may check status
        policy = self.release._policies.get(paper_id)
        if policy is None:
            return None
        authorized, reason = policy.is_authorized()
        return {
            "paper_id": paper_id,
            "release_at": policy.release_at.isoformat(),
            "window_minutes": policy.release_window_minutes,
            "required_approvals": policy.required_approvals,
            "approvals_received": len(policy.approvals),
            "approved_by": sorted(policy.approvals),
            "currently_authorized": authorized,
            "reason": reason,
        }
