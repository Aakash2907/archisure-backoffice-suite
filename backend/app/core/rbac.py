"""
rbac.py
=======
Role-Based Access Control -- the "Access Control" goal.

Principle of least privilege: each role gets only the permissions it
needs. Nobody -- not even an Admin -- has a permission that lets a
single person both UPLOAD and unilaterally RELEASE a paper; release
requires dual control (see release_control.py).
"""

from __future__ import annotations
from enum import Enum, auto


class Role(Enum):
    QUESTION_SETTER = auto()   # authors/uploads question papers
    REVIEWER = auto()          # reviews content for correctness (no decrypt)
    RELEASE_APPROVER = auto()  # authorizes scheduled release (e.g. senior official)
    EXAM_CENTER_OPERATOR = auto()  # retrieves decrypted paper AT exam time only
    AUDITOR = auto()           # read-only access to logs, never to content
    ADMIN = auto()             # user/role management only -- NOT content access


class Permission(Enum):
    UPLOAD_PAPER = auto()
    VIEW_METADATA = auto()
    APPROVE_RELEASE = auto()
    RETRIEVE_DECRYPTED = auto()
    VIEW_AUDIT_LOG = auto()
    MANAGE_USERS = auto()


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.QUESTION_SETTER: {Permission.UPLOAD_PAPER, Permission.VIEW_METADATA},
    Role.REVIEWER: {Permission.VIEW_METADATA},
    Role.RELEASE_APPROVER: {Permission.VIEW_METADATA, Permission.APPROVE_RELEASE},
    Role.EXAM_CENTER_OPERATOR: {Permission.VIEW_METADATA, Permission.RETRIEVE_DECRYPTED},
    Role.AUDITOR: {Permission.VIEW_AUDIT_LOG, Permission.VIEW_METADATA},
    Role.ADMIN: {Permission.MANAGE_USERS, Permission.VIEW_AUDIT_LOG},
}


class AccessDenied(PermissionError):
    pass


def require_permission(role: Role, permission: Permission) -> None:
    if permission not in ROLE_PERMISSIONS.get(role, set()):
        raise AccessDenied(f"Role {role.name} lacks permission {permission.name}")
