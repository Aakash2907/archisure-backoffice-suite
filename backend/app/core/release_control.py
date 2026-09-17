"""
release_control.py
===================
"Controlled Release" goal -- arguably the most important control for
this domain: a leaked paper is a leaked paper regardless of how well it
was encrypted at rest, so the release step is deliberately hard to
trigger accidentally or unilaterally.

Two independent gates must BOTH open before RETRIEVE_DECRYPTED is
permitted for a given paper:

  1. TIME LOCK      -- now() must be within the configured release
                        window (e.g. exam start time, +/- a few minutes).
  2. DUAL CONTROL    -- at least `required_approvals` DISTINCT people
                        holding Role.RELEASE_APPROVER must have approved
                        this specific paper_id. No single administrator,
                        however senior, can release a paper alone.

Both conditions, and every approval, are written to the audit log.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


class ReleaseNotAuthorized(PermissionError):
    pass


@dataclass
class ReleasePolicy:
    paper_id: str
    release_at: datetime          # earliest moment release is allowed
    release_window_minutes: int   # how long the window stays open after release_at
    required_approvals: int = 2
    approvals: set[str] = field(default_factory=set)  # usernames who approved

    def approve(self, username: str, audit) -> None:
        self.approvals.add(username)
        audit.log("RELEASE", username, "APPROVAL_RECORDED",
                   {"paper_id": self.paper_id, "total_approvals": len(self.approvals)})

    def _within_time_window(self, now: datetime) -> bool:
        window_end = self.release_at.timestamp() + self.release_window_minutes * 60
        return self.release_at.timestamp() <= now.timestamp() <= window_end

    def is_authorized(self, now: datetime | None = None) -> tuple[bool, str]:
        now = now or datetime.now(timezone.utc)
        if len(self.approvals) < self.required_approvals:
            return False, (f"Only {len(self.approvals)}/{self.required_approvals} "
                            f"required approvals recorded")
        if not self._within_time_window(now):
            if now < self.release_at:
                return False, f"Too early: release opens at {self.release_at.isoformat()}"
            return False, "Release window has closed"
        return True, "Authorized"


class ReleaseController:
    def __init__(self):
        self._policies: dict[str, ReleasePolicy] = {}

    def set_policy(self, policy: ReleasePolicy) -> None:
        self._policies[policy.paper_id] = policy

    def approve(self, paper_id: str, username: str, audit) -> None:
        self._policies[paper_id].approve(username, audit)

    def authorize_retrieval(self, paper_id: str, actor: str, audit) -> None:
        """Raises ReleaseNotAuthorized if either gate is closed. Logs the
        outcome either way -- attempted-but-denied retrievals are exactly
        the kind of event security monitoring needs to see."""
        policy = self._policies.get(paper_id)
        if policy is None:
            audit.log("RELEASE", actor, "RETRIEVAL_DENIED",
                       {"paper_id": paper_id, "reason": "no release policy configured"})
            raise ReleaseNotAuthorized(f"No release policy configured for {paper_id}")

        ok, reason = policy.is_authorized()
        if not ok:
            audit.log("RELEASE", actor, "RETRIEVAL_DENIED",
                       {"paper_id": paper_id, "reason": reason})
            raise ReleaseNotAuthorized(reason)

        audit.log("RELEASE", actor, "RETRIEVAL_AUTHORIZED", {"paper_id": paper_id})
