"""Safe Aurora simulation demonstration."""
from .core import AuroraCore, PermissionLevel


def main() -> None:
    aurora = AuroraCore()
    aurora.awaken_simulation()
    aurora.grant("planning.suggest", PermissionLevel.SUGGEST)
    print({
        "system": "Aurora",
        "state": aurora.state.value,
        "planning_authorized": aurora.decide(
            "planning.suggest", PermissionLevel.SUGGEST
        ),
        "external_action_authorized": aurora.decide(
            "external.act", PermissionLevel.ACT
        ),
        "audit_valid": aurora.verify_audit(),
        "evidence_level": "simulation",
    })


if __name__ == "__main__":
    main()
