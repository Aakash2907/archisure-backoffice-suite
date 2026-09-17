"""
audit.py
========
Tamper-evident audit trail -- the "Monitoring" goal.

Every security-relevant event (login, upload, view, approval, release,
denied access) is appended to a hash chain: each entry stores
sha256(previous_entry_hash + this_entry_content). This means nobody
-- including a DB administrator -- can silently edit or delete a past
entry without breaking the chain, which verify_integrity() detects.

This is the same core idea used in transparency logs / basic blockchains,
applied to a single append-only ledger rather than a distributed system.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AuditEntry:
    index: int
    timestamp: str
    category: str      # e.g. "AUTH", "DOCUMENT", "RELEASE"
    actor: str
    action: str
    details: dict[str, Any]
    prev_hash: str
    entry_hash: str = field(init=False)

    def __post_init__(self):
        self.entry_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "category": self.category,
                "actor": self.actor,
                "action": self.action,
                "details": self.details,
                "prev_hash": self.prev_hash,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(payload.encode()).hexdigest()


GENESIS_HASH = "0" * 64


class AuditLog:
    def __init__(self):
        self._entries: list[AuditEntry] = []

    def log(self, category: str, actor: str, action: str, details: dict | None = None) -> AuditEntry:
        prev_hash = self._entries[-1].entry_hash if self._entries else GENESIS_HASH
        entry = AuditEntry(
            index=len(self._entries),
            timestamp=datetime.now(timezone.utc).isoformat(),
            category=category,
            actor=actor,
            action=action,
            details=details or {},
            prev_hash=prev_hash,
        )
        self._entries.append(entry)
        return entry

    def verify_integrity(self) -> tuple[bool, int | None]:
        """Returns (is_valid, index_of_first_corruption_or_None)."""
        prev_hash = GENESIS_HASH
        for entry in self._entries:
            if entry.prev_hash != prev_hash:
                return False, entry.index
            recomputed = entry._compute_hash()
            if recomputed != entry.entry_hash:
                return False, entry.index
            prev_hash = entry.entry_hash
        return True, None

    def tamper_with_entry_for_demo(self, index: int, new_action: str) -> None:
        """FOR DEMO PURPOSES ONLY: simulates an attacker editing a log row
        directly in the database, without recomputing the hash chain --
        exactly what verify_integrity() is designed to catch."""
        self._entries[index].action = new_action

    def entries(self) -> list[AuditEntry]:
        return list(self._entries)

    def print_log(self):
        for e in self._entries:
            print(f"[{e.index:03d}] {e.timestamp} | {e.category:9s} | {e.actor:12s} | "
                  f"{e.action:20s} | {e.details} | hash={e.entry_hash[:12]}...")
