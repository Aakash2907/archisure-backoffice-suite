from __future__ import annotations

from fastapi import Header, HTTPException, status

from .system import QuestionPaperSystem

# Vercel Functions have a read-only filesystem.
# /tmp is the writable scratch directory.
_system = QuestionPaperSystem(vault_root="/tmp/vault")


def get_system() -> QuestionPaperSystem:
    return _system


def get_token(
    authorization: str | None = Header(default=None),
) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected: Bearer <token>",
        )

    return authorization.split(" ", 1)[1].strip()