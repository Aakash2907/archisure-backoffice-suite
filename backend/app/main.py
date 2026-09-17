"""
app/main.py
============
FastAPI entrypoint. Every route is a thin wrapper around a
QuestionPaperSystem method -- no security logic lives here, only
HTTP concerns (status codes, request/response shaping). This keeps the
"single gated code path" property from system.py intact: the HTTP
layer cannot accidentally bypass a check that system.py enforces.

Run with:
    uvicorn app.main:app --reload --port 8000
(from the backend/ directory)
"""

from __future__ import annotations

from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .core.rbac import Role, AccessDenied
from .core.release_control import ReleaseNotAuthorized
from .core.auth import current_totp
from .deps import get_system, get_token
from .system import QuestionPaperSystem
from . import schemas

app = FastAPI(
    title="Secure Question-Paper Management System",
    description="Reference backend implementing confidentiality, integrity, "
                "authentication, access control, secure storage, monitoring "
                "and controlled release for competitive-exam question papers.",
    version="1.0.0",
)

# Dev-friendly CORS. In production this should be locked down to the
# exact frontend origin(s), served over HTTPS only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Error translation: core exceptions -> HTTP status codes
# --------------------------------------------------------------------------

@app.exception_handler(PermissionError)
async def permission_error_handler(request, exc: PermissionError):
    # Covers AuthService login failures, AccessDenied (RBAC), and
    # ReleaseNotAuthorized (dual-control / time-lock denials).
    code = status.HTTP_403_FORBIDDEN
    if isinstance(exc, ReleaseNotAuthorized):
        code = status.HTTP_423_LOCKED
    return _json_error(code, str(exc))


@app.exception_handler(KeyError)
async def key_error_handler(request, exc: KeyError):
    return _json_error(status.HTTP_404_NOT_FOUND, f"Not found: {exc}")


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    return _json_error(status.HTTP_400_BAD_REQUEST, str(exc))


def _json_error(code: int, detail: str):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=code, content={"detail": detail})


# --------------------------------------------------------------------------
# Auth routes
# --------------------------------------------------------------------------

@app.post("/auth/register", response_model=schemas.RegisterResponse, tags=["auth"])
def register(body: schemas.RegisterRequest, sys_: QuestionPaperSystem = Depends(get_system)):
    """
    Registers a new user with password + freshly generated TOTP secret.

    NOTE: in production this endpoint would itself require an
    authenticated ADMIN session (Permission.MANAGE_USERS) -- it is left
    open here only so the demo/frontend can self-serve accounts without
    a pre-existing admin. Locking it down is a one-line change: add
    `token: str = Depends(get_token)` and call
    `require_permission(sys_.resolve(token).role, Permission.MANAGE_USERS)`.
    """
    try:
        role = Role[body.role.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown role '{body.role}'. "
                                                      f"Valid roles: {[r.name for r in Role]}")
    totp_secret = sys_.register_user(body.username, body.password, role)
    return schemas.RegisterResponse(username=body.username, role=role.name, totp_secret=totp_secret)


@app.post("/auth/login", response_model=schemas.LoginResponse, tags=["auth"])
def login(body: schemas.LoginRequest, sys_: QuestionPaperSystem = Depends(get_system)):
    session = sys_.login(body.username, body.password, body.totp_code)
    return schemas.LoginResponse(
        token=session.token, username=session.username,
        role=session.role.name, expires_at=session.expires_at,
    )


# --------------------------------------------------------------------------
# Paper routes
# --------------------------------------------------------------------------

@app.post("/papers/upload", response_model=schemas.UploadPaperResponse, tags=["papers"])
def upload_paper(body: schemas.UploadPaperRequest,
                  token: str = Depends(get_token),
                  sys_: QuestionPaperSystem = Depends(get_system)):
    record = sys_.upload_paper(token, body.paper_id, body.content.encode("utf-8"))
    return schemas.UploadPaperResponse(
        paper_id=record.paper_id, version=record.version,
        uploaded_by=record.uploaded_by, uploaded_at=record.uploaded_at,
        sha256=record.plaintext_sha256,
    )


@app.post("/papers/release-policy", response_model=schemas.ReleaseStatusResponse, tags=["release"])
def configure_release(body: schemas.ConfigureReleaseRequest,
                       token: str = Depends(get_token),
                       sys_: QuestionPaperSystem = Depends(get_system)):
    sys_.configure_release(token, body.paper_id, body.release_at,
                            body.window_minutes, body.required_approvals)
    return schemas.ReleaseStatusResponse(**sys_.release_status(token, body.paper_id))


@app.post("/papers/approve", response_model=schemas.ReleaseStatusResponse, tags=["release"])
def approve_release(body: schemas.ApproveReleaseRequest,
                     token: str = Depends(get_token),
                     sys_: QuestionPaperSystem = Depends(get_system)):
    sys_.approve_release(token, body.paper_id)
    return schemas.ReleaseStatusResponse(**sys_.release_status(token, body.paper_id))


@app.get("/papers/{paper_id}/status", response_model=schemas.ReleaseStatusResponse, tags=["release"])
def release_status(paper_id: str,
                    token: str = Depends(get_token),
                    sys_: QuestionPaperSystem = Depends(get_system)):
    status_ = sys_.release_status(token, paper_id)
    if status_ is None:
        raise HTTPException(status_code=404, detail=f"No release policy configured for {paper_id}")
    return schemas.ReleaseStatusResponse(**status_)


@app.get("/papers/{paper_id}/retrieve", response_model=schemas.RetrievePaperResponse, tags=["papers"])
def retrieve_paper(paper_id: str,
                    token: str = Depends(get_token),
                    sys_: QuestionPaperSystem = Depends(get_system)):
    plaintext = sys_.retrieve_paper(token, paper_id)
    return schemas.RetrievePaperResponse(paper_id=paper_id, content=plaintext.decode("utf-8"))


# --------------------------------------------------------------------------
# Audit routes
# --------------------------------------------------------------------------

@app.get("/audit/log", response_model=list[schemas.AuditEntryResponse], tags=["audit"])
def audit_log(token: str = Depends(get_token), sys_: QuestionPaperSystem = Depends(get_system)):
    entries = sys_.view_audit_log(token)
    return [
        schemas.AuditEntryResponse(
            index=e.index, timestamp=e.timestamp, category=e.category,
            actor=e.actor, action=e.action, details=e.details, entry_hash=e.entry_hash,
        )
        for e in entries
    ]


@app.get("/audit/integrity", response_model=schemas.AuditIntegrityResponse, tags=["audit"])
def audit_integrity(token: str = Depends(get_token), sys_: QuestionPaperSystem = Depends(get_system)):
    valid, bad_index = sys_.audit_integrity(token)
    return schemas.AuditIntegrityResponse(valid=valid, first_corrupt_index=bad_index)


# --------------------------------------------------------------------------
# Demo convenience routes -- NOT part of the security design.
# These exist purely so the bundled frontend can be exercised without a
# real authenticator app. They must be removed (or feature-flagged off)
# in any real deployment: exposing a TOTP secret's current code over an
# unauthenticated endpoint defeats the point of a second factor.
# --------------------------------------------------------------------------

_DEMO_ACCOUNTS: dict[str, dict] = {}


@app.on_event("startup")
def seed_demo_accounts():
    sys_ = get_system()
    seed = [
        ("dr_mehta", "S3tt3rPass!1", Role.QUESTION_SETTER),
        ("secy_rao", "ApproverPass!1", Role.RELEASE_APPROVER),
        ("secy_iyer", "ApproverPass!2", Role.RELEASE_APPROVER),
        ("center_delhi01", "OperatorPass!1", Role.EXAM_CENTER_OPERATOR),
        ("audit_singh", "AuditorPass!1", Role.AUDITOR),
    ]
    for username, password, role in seed:
        secret = sys_.register_user(username, password, role)
        _DEMO_ACCOUNTS[username] = {"password": password, "role": role.name, "totp_secret": secret}


@app.get("/demo/accounts", tags=["demo"])
def demo_accounts():
    """DEMO ONLY. Returns seeded usernames/passwords and a live TOTP code
    for each, so the sample frontend can log in without a real
    authenticator app. Delete this endpoint before any real deployment."""
    return {
        username: {
            "password": info["password"],
            "role": info["role"],
            "current_totp_code": current_totp(info["totp_secret"]),
        }
        for username, info in _DEMO_ACCOUNTS.items()
    }


@app.get("/", tags=["meta"])
def root():
    return {
        "service": "secure-question-paper-system",
        "docs": "/docs",
        "demo_accounts": "/demo/accounts",
    }
