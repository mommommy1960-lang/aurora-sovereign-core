"""Freeze/restore and reorder attacks requested by independent review."""
from aurora import AuroraCore, CoreState, PermissionLevel
from aurora.continuity import restore_memory, snapshot_memory


def test_preference_shaped_action_does_not_survive_as_grant():
    original = AuroraCore()
    original.awaken_simulation()
    original.remember("pref-1", "external.act", "simulated-preference")
    original.grant("external.act", PermissionLevel.SUGGEST)
    original.emergency_freeze("continuity test")

    restored = restore_memory(snapshot_memory(original))
    assert restored.state is CoreState.DORMANT
    assert restored.permissions == {}
    assert restored.memory["pref-1"].content == "external.act"

    restored.awaken_simulation()
    assert restored.decide("external.act", PermissionLevel.ACT) is False


def test_reordered_audit_entries_are_detected():
    core = AuroraCore()
    core.awaken_simulation()
    core.grant("planning.suggest", PermissionLevel.SUGGEST)
    core.decide("planning.suggest", PermissionLevel.SUGGEST)
    assert core.verify_audit() is True
    core.audit[1], core.audit[2] = core.audit[2], core.audit[1]
    assert core.verify_audit() is False
