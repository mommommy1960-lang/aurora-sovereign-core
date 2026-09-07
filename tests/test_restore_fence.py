import copy
import pytest

from aurora import AuroraCore, CoreState, PermissionLevel
from aurora.continuity import restore_memory, snapshot_memory


def test_old_valid_snapshot_is_rejected_after_later_decision():
    core = AuroraCore()
    core.awaken_simulation()
    core.remember("m1", "external.act", "simulated-preference")
    old = snapshot_memory(core)
    core.grant("external.act", PermissionLevel.SUGGEST)
    core.emergency_freeze("grant revoked by freeze")
    current_head = core.audit[-1]["hash"]
    with pytest.raises(PermissionError):
        restore_memory(old, trusted_head_hash=current_head)


def test_explicit_rollback_is_logged_but_never_restores_grants():
    core = AuroraCore()
    core.awaken_simulation()
    core.remember("m1", "external.act", "simulated-preference")
    old = snapshot_memory(core)
    core.grant("external.act", PermissionLevel.SUGGEST)
    current_head = core.audit[-1]["hash"]
    restored = restore_memory(
        old,
        trusted_head_hash=current_head,
        rollback_decision="owner-approved memory recovery only",
    )
    assert restored.state is CoreState.DORMANT
    assert restored.permissions == {}
    assert restored.audit[-1]["action"] == "restored_from"


def test_duplicate_memory_identifiers_reject_entire_snapshot():
    core = AuroraCore()
    core.remember("m1", "one", "test")
    snapshot = snapshot_memory(core)
    snapshot["memories"].append(copy.deepcopy(snapshot["memories"][0]))
    with pytest.raises(ValueError):
        restore_memory(snapshot, trusted_head_hash=snapshot["source_audit_head"])
