"""
storage.py
==========
"Secure Storage" goal. Simulates an encrypted cloud object store
(e.g. S3/Blob Storage + KMS) using the local filesystem. Only ciphertext,
wrapped keys, hashes and signatures ever touch disk -- never plaintext.

Each document is stored with an immutable version history: a paper is
never overwritten in place. If a question setter uploads a corrected
version, a NEW version record is appended, so any prior (possibly
leaked) version remains individually traceable and the previous
ciphertext is still auditable.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from .crypto_utils import EncryptedPayload


@dataclass
class StoredDocumentVersion:
    paper_id: str
    version: int
    uploaded_by: str
    uploaded_at: str
    ciphertext: bytes
    nonce: bytes
    wrapped_dek: bytes
    plaintext_sha256: str
    signature: bytes


class SecureStorage:
    def __init__(self, root: str = "vault"):
        self.root = root
        os.makedirs(self.root, exist_ok=True)
        self._index: dict[str, list[StoredDocumentVersion]] = {}

    def store(self, paper_id: str, payload: EncryptedPayload, uploaded_by: str) -> StoredDocumentVersion:
        versions = self._index.setdefault(paper_id, [])
        version_no = len(versions) + 1
        record = StoredDocumentVersion(
            paper_id=paper_id,
            version=version_no,
            uploaded_by=uploaded_by,
            uploaded_at=datetime.now(timezone.utc).isoformat(),
            ciphertext=payload.ciphertext,
            nonce=payload.nonce,
            wrapped_dek=payload.wrapped_dek,
            plaintext_sha256=payload.plaintext_sha256,
            signature=payload.signature,
        )
        versions.append(record)
        self._persist(record)
        return record

    def latest(self, paper_id: str) -> StoredDocumentVersion:
        versions = self._index.get(paper_id)
        if not versions:
            raise KeyError(f"No such paper: {paper_id}")
        return versions[-1]

    def as_encrypted_payload(self, record: StoredDocumentVersion) -> EncryptedPayload:
        return EncryptedPayload(
            ciphertext=record.ciphertext,
            nonce=record.nonce,
            wrapped_dek=record.wrapped_dek,
            plaintext_sha256=record.plaintext_sha256,
            signature=record.signature,
        )

    def _persist(self, record: StoredDocumentVersion) -> None:
        """Writes ciphertext to disk purely for demonstration -- shows that
        what lands in the 'cloud bucket' is opaque bytes, never plaintext."""
        path = os.path.join(self.root, f"{record.paper_id}_v{record.version}.enc")
        with open(path, "wb") as f:
            f.write(record.nonce + b"::" + record.ciphertext)
