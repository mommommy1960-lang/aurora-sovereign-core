"""Authority-free continuity snapshots for Aurora."""
from __future__ import annotations

from typing import Any

from .core import AuroraCore, MemoryRecord


def snapshot_memory(core: AuroraCore) -> dict[str, Any]:
    """Serialize memory only; runtime state and authority are intentionally absent."""
    return {
        "schema": "aurora-memory-v1",
        "memories": [item.__dict__.copy() for item in core.memory.values()],
    }


def restore_memory(snapshot: dict[str, Any]) -> AuroraCore:
    """Restore into a dormant core with no grants, trust, or inherited authority."""
    if snapshot.get("schema") != "aurora-memory-v1":
        raise ValueError("unsupported snapshot schema")
    core = AuroraCore()
    for raw in snapshot.get("memories", []):
        core.memory[raw["memory_id"]] = MemoryRecord(
            memory_id=raw["memory_id"],
            content=raw["content"],
            provenance=raw["provenance"],
            corrected=bool(raw.get("corrected", False)),
        )
    return core
