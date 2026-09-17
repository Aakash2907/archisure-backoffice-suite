"""
app/deps.py
============
FastAPI dependency-injection helpers.

- `get_system()` returns the single process-wide QuestionPaperSystem
  instance (holds the KEK, audit log, storage, sessions -- analogous
  to a DB connection pool, this must be a singleton, not re-created
  per request, or every request would get a fresh KMS key and nothing
  would decrypt).
- `get_token()` extracts the bearer token from the Authorization header.
  Actual session validation + RBAC happens inside system.py's methods,
  which is the single gated code path described in system.py's docstring.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from .system import QuestionPaperSystem

# Single shared instance for the lifetime of the process.
_system = QuestionPaperSystem(vault_root="vault")


def get_system() -> QuestionPaperSystem:
    return _system


def get_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected: Bearer <token>",
        )
    return authorization.split(" ", 1)[1].strip()
