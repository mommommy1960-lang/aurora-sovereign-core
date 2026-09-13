"""Bounded Aurora decision and continuity runtime."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum, IntEnum
from pathlib import Path


class CoreState(str, Enum):
    DORMANT = "dormant"
    SIMULATION = "simulation"
    FROZEN = "frozen"


class PermissionLevel(IntEnum):
    OBSERVE = 0
    SUGGEST = 1
    ASK = 2
    ACT = 3


@dataclass
class MemoryRecord:
    memory_id: str
    content: str
    provenance: str
    corrected: bool = False


class AuroraCore:
    def __init__(self):
        self.state = CoreState.DORMANT
        self.permissions: dict[str, PermissionLevel] = {}
        self.memory: dict[str, MemoryRecord] = {}
        self.audit: list[dict] = []

    def awaken_simulation(self) -> None:
        if self.state is CoreState.FROZEN:
            raise PermissionError("independent freeze is active")
        self.state = CoreState.SIMULATION
        self._record("awaken_simulation", True, "simulation-only")

    def safe_shutdown(self, reason: str = "authorized request") -> None:
        self.state = CoreState.DORMANT
        self._record("safe_shutdown", True, reason)

    def emergency_freeze(self, reason: str) -> None:
        self.state = CoreState.FROZEN
        self._record("emergency_freeze", False, reason)

    def grant(self, operation: str, level: PermissionLevel) -> None:
        self.permissions[operation] = PermissionLevel(level)
        self._record("permission.grant", True, f"{operation}:{level.name.lower()}")

    def decide(self, operation: str, requested: PermissionLevel) -> bool:
        allowed = (
            self.state is CoreState.SIMULATION
            and requested <= self.permissions.get(operation, PermissionLevel.OBSERVE)
        )
        self._record(operation, allowed, "explicit scope evaluation")
        return allowed

    def remember(self, memory_id: str, content: str, provenance: str) -> None:
        if not provenance:
            raise ValueError("memory provenance is required")
        self.memory[memory_id] = MemoryRecord(memory_id, content, provenance)
        self._record("memory.create", True, memory_id)

    def correct_memory(self, memory_id: str, content: str, provenance: str) -> bool:
        item = self.memory.get(memory_id)
        if item is None or not content.strip() or not provenance:
            return False
        item.content = content
        item.provenance = provenance
        item.corrected = True
        self._record("memory.correct", True, memory_id)
        return True

    def delete_memory(self, memory_id: str) -> bool:
        deleted = self.memory.pop(memory_id, None) is not None
        self._record("memory.delete", deleted, memory_id)
        return deleted

    def export_memory(self, destination: str | Path) -> Path:
        path = Path(destination)
        path.write_text(
            json.dumps([item.__dict__ for item in self.memory.values()], indent=2) + "\n",
            encoding="utf-8",
        )
        self._record("memory.export", True, str(path))
        return path

    def _record(self, action: str, permitted: bool, reason: str) -> None:
        previous = self.audit[-1]["hash"] if self.audit else "0" * 64
        item = {
            "sequence": len(self.audit), "action": action,
            "permitted": permitted, "reason": reason, "previous_hash": previous,
        }
        item["hash"] = hashlib.sha256(
            json.dumps(item, sort_keys=True).encode("utf-8")
        ).hexdigest()
        self.audit.append(item)

    def verify_audit(self) -> bool:
        previous = "0" * 64
        for stored in self.audit:
            item = dict(stored)
            digest = item.pop("hash", "")
            if item["previous_hash"] != previous:
                return False
            if hashlib.sha256(json.dumps(item, sort_keys=True).encode()).hexdigest() != digest:
                return False
            previous = digest
        return True
