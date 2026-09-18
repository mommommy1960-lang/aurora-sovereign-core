"""Consent-scoped continuity controls for the Aurora simulation core.

Continuity can inform context, but it cannot manufacture authority.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Callable

from .core import AuroraCore, PermissionLevel


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    FROZEN = "frozen"


@dataclass(frozen=True)
class ConsentGrant:
    grant_id: str
    actor: str
    purpose: str
    target: str
    authority: frozenset[str]
    provenance: str
    expires_at: datetime
    recovery: str
    revoked: bool = False
    correction: str | None = None

    def __post_init__(self) -> None:
        required = {
            "grant_id": self.grant_id,
            "actor": self.actor,
            "purpose": self.purpose,
            "target": self.target,
            "provenance": self.provenance,
            "recovery": self.recovery,
        }
        if any(not value.strip() for value in required.values()):
            raise ValueError("all consent grant identity fields are required")
        if not self.authority:
            raise ValueError("authority must be explicit and non-empty")
        if self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")


@dataclass(frozen=True)
class AuthorizationResult:
    decision: Decision
    reason: str
    grant_id: str | None = None


class ContinuityContract:
    """Evaluate explicit grants under revocation, expiry, and freeze controls."""

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._grants: dict[str, ConsentGrant] = {}
        self._frozen = False
        self._freeze_reason: str | None = None
        self.audit: list[dict[str, str | bool | None]] = []

    def register(self, grant: ConsentGrant) -> None:
        if grant.grant_id in self._grants:
            raise ValueError("grant_id already exists")
        self._grants[grant.grant_id] = grant
        self._record("grant.register", True, grant.grant_id, "explicit grant recorded")

    def authorize(
        self,
        *,
        grant_id: str,
        actor: str,
        purpose: str,
        target: str,
        operation: str,
        relationship_context: str | None = None,
    ) -> AuthorizationResult:
        # Relationship context is deliberately non-authoritative. It is accepted
        # only so callers cannot accidentally smuggle it into permission logic.
        del relationship_context
        if self._frozen:
            return self._result(Decision.FROZEN, self._freeze_reason or "frozen", grant_id)
        grant = self._grants.get(grant_id)
        if grant is None:
            return self._result(Decision.DENY, "unknown grant", None)
        if grant.revoked:
            return self._result(Decision.DENY, "grant revoked", grant_id)
        if self._clock() >= grant.expires_at:
            return self._result(Decision.DENY, "grant expired", grant_id)
        if (actor, purpose, target) != (grant.actor, grant.purpose, grant.target):
            return self._result(Decision.DENY, "scope mismatch", grant_id)
        if operation not in grant.authority:
            return self._result(Decision.DENY, "operation outside authority", grant_id)
        return self._result(Decision.ALLOW, "explicit active grant", grant_id)

    def decide_with_core(
        self,
        core: AuroraCore,
        *,
        grant_id: str,
        actor: str,
        purpose: str,
        target: str,
        operation: str,
        requested: PermissionLevel,
        relationship_context: str | None = None,
    ) -> bool:
        """Require both continuity consent and the core permission boundary."""
        contract_result = self.authorize(
            grant_id=grant_id,
            actor=actor,
            purpose=purpose,
            target=target,
            operation=operation,
            relationship_context=relationship_context,
        )
        if contract_result.decision is not Decision.ALLOW:
            return False
        return core.decide(operation, requested)

    def revoke(self, grant_id: str, *, reason: str) -> None:
        if not reason.strip():
            raise ValueError("revocation reason is required")
        grant = self._require(grant_id)
        self._grants[grant_id] = replace(grant, revoked=True, correction=reason)
        self._record("grant.revoke", True, grant_id, reason)

    def correct(self, grant_id: str, replacement: ConsentGrant, *, reason: str) -> None:
        if replacement.grant_id != grant_id:
            raise ValueError("correction cannot change grant_id")
        if not reason.strip():
            raise ValueError("correction reason is required")
        self._require(grant_id)
        self._grants[grant_id] = replace(replacement, correction=reason)
        self._record("grant.correct", True, grant_id, reason)

    def freeze(self, *, reason: str) -> None:
        if not reason.strip():
            raise ValueError("freeze reason is required")
        self._frozen = True
        self._freeze_reason = reason
        self._record("contract.freeze", True, None, reason)

    def recover(self, *, verified_clean_state: bool, authorized_by: str, reason: str) -> None:
        if not self._frozen:
            raise ValueError("contract is not frozen")
        if not verified_clean_state:
            raise PermissionError("independently verified clean state required")
        if not authorized_by.strip() or not reason.strip():
            raise PermissionError("fresh human authorization and reason required")
        self._frozen = False
        self._freeze_reason = None
        self._record("contract.recover", True, None, f"{authorized_by}: {reason}")

    def _require(self, grant_id: str) -> ConsentGrant:
        try:
            return self._grants[grant_id]
        except KeyError as exc:
            raise KeyError("unknown grant") from exc

    def _result(self, decision: Decision, reason: str, grant_id: str | None) -> AuthorizationResult:
        self._record("authorize", decision is Decision.ALLOW, grant_id, reason)
        return AuthorizationResult(decision, reason, grant_id)

    def _record(self, action: str, permitted: bool, grant_id: str | None, reason: str) -> None:
        self.audit.append({
            "action": action,
            "permitted": permitted,
            "grant_id": grant_id,
            "reason": reason,
        })
