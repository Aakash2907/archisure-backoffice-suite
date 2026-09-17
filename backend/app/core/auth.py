"""
auth.py
=======
Authentication layer: covers the "Authentication" and part of the
"Monitoring" goals from the requirements brief.

Features:
  - Passwords are never stored in plaintext: PBKDF2-HMAC-SHA256, 260k
    iterations, unique salt per user (OWASP-recommended parameters).
  - Time-based One-Time Password (TOTP) second factor (RFC 6238),
    implemented from stdlib `hmac`/`hashlib` only -- mandatory for any
    role that can approve a release or view decrypted content.
  - Account lockout after repeated failed attempts (brute-force defence).
  - Session tokens are opaque, cryptographically random (secrets.token_urlsafe),
    short-lived, and bound to the role at issue time.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

PBKDF2_ITERATIONS = 260_000
LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION = timedelta(minutes=15)
SESSION_TTL = timedelta(minutes=20)


# --------------------------------------------------------------------------
# Password hashing
# --------------------------------------------------------------------------

def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        _, iterations, salt_hex, hash_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


# --------------------------------------------------------------------------
# TOTP (RFC 6238) - second factor, stdlib only
# --------------------------------------------------------------------------

def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(10)).decode()


def _hotp(secret_b32: str, counter: int, digits: int = 6) -> str:
    key = base64.b32decode(secret_b32)
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = (struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)


def current_totp(secret_b32: str, step: int = 30, digits: int = 6) -> str:
    counter = int(time.time() // step)
    return _hotp(secret_b32, counter, digits)


def verify_totp(secret_b32: str, code: str, step: int = 30, digits: int = 6, window: int = 1) -> bool:
    counter = int(time.time() // step)
    for offset in range(-window, window + 1):
        if hmac.compare_digest(_hotp(secret_b32, counter + offset, digits), code):
            return True
    return False


# --------------------------------------------------------------------------
# Users + sessions
# --------------------------------------------------------------------------

@dataclass
class User:
    username: str
    role: "Role"
    password_hash: str
    totp_secret: str
    failed_attempts: int = 0
    locked_until: datetime | None = None
    mfa_enrolled: bool = True


@dataclass
class Session:
    token: str
    username: str
    role: "Role"
    expires_at: datetime


class AuthService:
    """In-memory user directory + session store (stand-in for an IdP)."""

    def __init__(self):
        self._users: dict[str, User] = {}
        self._sessions: dict[str, Session] = {}

    def register_user(self, username: str, password: str, role: "Role") -> str:
        """Returns the TOTP secret so it can be shown once (like a QR enrollment)."""
        totp_secret = generate_totp_secret()
        self._users[username] = User(
            username=username,
            role=role,
            password_hash=hash_password(password),
            totp_secret=totp_secret,
        )
        return totp_secret

    def login(self, username: str, password: str, totp_code: str, audit=None) -> Session:
        user = self._users.get(username)
        now = datetime.now(timezone.utc)

        if user is None:
            if audit:
                audit.log("AUTH", "unknown", "LOGIN_FAILED", {"username": username, "reason": "no such user"})
            raise PermissionError("Invalid credentials")

        if user.locked_until and now < user.locked_until:
            if audit:
                audit.log("AUTH", username, "LOGIN_BLOCKED", {"reason": "account locked", "until": str(user.locked_until)})
            raise PermissionError(f"Account locked until {user.locked_until.isoformat()}")

        password_ok = verify_password(password, user.password_hash)
        totp_ok = verify_totp(user.totp_secret, totp_code)

        if not (password_ok and totp_ok):
            user.failed_attempts += 1
            if user.failed_attempts >= LOCKOUT_THRESHOLD:
                user.locked_until = now + LOCKOUT_DURATION
                if audit:
                    audit.log("AUTH", username, "ACCOUNT_LOCKED",
                               {"failed_attempts": user.failed_attempts})
            if audit:
                audit.log("AUTH", username, "LOGIN_FAILED",
                           {"password_ok": password_ok, "totp_ok": totp_ok,
                            "attempt": user.failed_attempts})
            raise PermissionError("Invalid credentials")

        # success
        user.failed_attempts = 0
        user.locked_until = None
        token = secrets.token_urlsafe(32)
        session = Session(token=token, username=username, role=user.role,
                           expires_at=now + SESSION_TTL)
        self._sessions[token] = session
        if audit:
            audit.log("AUTH", username, "LOGIN_SUCCESS", {"role": user.role.name})
        return session

    def get_session(self, token: str) -> Session:
        session = self._sessions.get(token)
        if session is None:
            raise PermissionError("No such session")
        if datetime.now(timezone.utc) > session.expires_at:
            del self._sessions[token]
            raise PermissionError("Session expired")
        return session

    def get_user(self, username: str) -> User:
        return self._users[username]
