"""
api/index.py
=============
Entrypoint Vercel's Python runtime (@vercel/python) loads as the
serverless function for every request under /api/*.

Vercel forwards the FULL original path (e.g. "/api/auth/login") to this
function, but the backend's routes are defined without an "/api" prefix
(e.g. "/auth/login" in backend/app/main.py). Mounting the backend app at
"/api" on an outer FastAPI instance reconciles that, the same way you'd
mount a sub-application at a path prefix in any ASGI app.

IMPORTANT (read the caveat in the top-level README / chat reply before
relying on this in production): QuestionPaperSystem holds all state
in-memory (users, sessions, audit log, encrypted vault, KMS keypair).
A serverless function has no guaranteed process continuity between
invocations, so this mount makes the app *routable* on Vercel, but does
not make its in-memory design *correct* there. See "Deploying for real"
in the chat reply.
"""

import os
import sys

# backend/ is a sibling of api/ at the repo root; add it to sys.path so
# `from app.main import ...` resolves backend/app as the "app" package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi import FastAPI
from app.main import app as backend_app  # noqa: E402  (import after sys.path fix)
