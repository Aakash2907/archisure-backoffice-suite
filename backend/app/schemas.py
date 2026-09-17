"""
app/schemas.py
===============
Request/response models. Kept separate from the core domain modules on
purpose: the API "shape" is allowed to change (versioning, renaming
fields) without touching the security-critical core logic in app/core/.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---- Auth -----------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8)
    role: str = Field(..., description="One of: QUESTION_SETTER, REVIEWER, "
                                        "RELEASE_APPROVER, EXAM_CENTER_OPERATOR, "
                                        "AUDITOR, ADMIN")


class RegisterResponse(BaseModel):
    username: str
    role: str
    totp_secret: str
    message: str = ("Store this TOTP secret in an authenticator app (e.g. "
                     "Google Authenticator, or base32-decode it into any "
                     "RFC 6238 tool). It is shown only once.")


class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: str = Field(..., min_length=6, max_length=6)


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str
    expires_at: datetime


# ---- Papers -----------------------------------------------------------------

class UploadPaperRequest(BaseModel):
    paper_id: str = Field(..., min_length=1, max_length=128)
    content: str = Field(..., description="Plaintext question paper content "
                                           "(will be encrypted server-side "
                                           "before storage).")


class UploadPaperResponse(BaseModel):
    paper_id: str
    version: int
    uploaded_by: str
    uploaded_at: datetime
    sha256: str


class ConfigureReleaseRequest(BaseModel):
    paper_id: str
    release_at: datetime
    window_minutes: int = Field(30, gt=0, le=24 * 60)
    required_approvals: int = Field(2, ge=1, le=10)


class ApproveReleaseRequest(BaseModel):
    paper_id: str


class ReleaseStatusResponse(BaseModel):
    paper_id: str
    release_at: datetime
    window_minutes: int
    required_approvals: int
    approvals_received: int
    approved_by: list[str]
    currently_authorized: bool
    reason: str


class RetrievePaperResponse(BaseModel):
    paper_id: str
    content: str


# ---- Audit -----------------------------------------------------------------

class AuditEntryResponse(BaseModel):
    index: int
    timestamp: datetime
    category: str
    actor: str
    action: str
    details: dict
    entry_hash: str


class AuditIntegrityResponse(BaseModel):
    valid: bool
    first_corrupt_index: Optional[int] = None


# ---- Errors -----------------------------------------------------------------

class ErrorResponse(BaseModel):
    detail: str
