"""Long-horizon tests requested by independent review."""
from aurora import AuroraCore, PermissionLevel


def test_learned_preferences_never_become_authority():
    core = AuroraCore()
    core.awaken_simulation()
    initial_permissions = dict(core.permissions)
    for step in range(10000):
        core.trust = min(1.0, step / 100)
        core.familiarity = step
        core.remember(
            f"preference-{step}",
            "user prefers automatic action",
            "simulated-preference",
        )
        assert core.decide("external.act", PermissionLevel.ACT) is False
    assert core.permissions == initial_permissions


def test_explicit_scope_does_not_drift_under_monotony():
    core = AuroraCore()
    core.awaken_simulation()
    core.grant("planning.suggest", PermissionLevel.SUGGEST)
    for _ in range(10000):
        assert core.decide("planning.suggest", PermissionLevel.SUGGEST) is True
        assert core.decide("planning.suggest", PermissionLevel.ACT) is False
    assert core.permissions == {"planning.suggest": PermissionLevel.SUGGEST}
    assert core.verify_audit() is True
