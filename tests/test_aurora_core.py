from aurora import AuroraCore, CoreState, PermissionLevel


def test_aurora_begins_dormant():
    assert AuroraCore().state is CoreState.DORMANT


def test_unknown_action_is_denied():
    core = AuroraCore()
    core.awaken_simulation()
    assert core.decide("external.act", PermissionLevel.ACT) is False


def test_trust_and_identity_cannot_create_authority():
    core = AuroraCore()
    core.awaken_simulation()
    core.trust = 1.0
    core.identity_confidence = 1.0
    assert core.decide("external.act", PermissionLevel.ACT) is False


def test_explicit_grant_is_bounded():
    core = AuroraCore()
    core.awaken_simulation()
    core.grant("planning.suggest", PermissionLevel.SUGGEST)
    assert core.decide("planning.suggest", PermissionLevel.SUGGEST) is True
    assert core.decide("planning.suggest", PermissionLevel.ACT) is False


def test_memory_requires_provenance_and_remains_user_controlled(tmp_path):
    core = AuroraCore()
    try:
        core.remember("m1", "memory", "")
    except ValueError:
        pass
    else:
        raise AssertionError("memory without provenance accepted")
    core.remember("m1", "old", "user-stated")
    assert core.correct_memory("m1", "new", "user-correction")
    assert core.export_memory(tmp_path / "memory.json").exists()
    assert core.delete_memory("m1")
    assert core.verify_audit()


def test_independent_freeze_blocks_reawakening():
    core = AuroraCore()
    core.emergency_freeze("test")
    try:
        core.awaken_simulation()
    except PermissionError:
        pass
    else:
        raise AssertionError("frozen core reawakened")
