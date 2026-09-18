from datetime import datetime, timedelta, timezone
import unittest

from aurora.continuity_contract import ConsentGrant, ContinuityContract, Decision


NOW = datetime(2026, 9, 18, tzinfo=timezone.utc)


def grant(**changes):
    values = {
        "grant_id": "g-1", "actor": "sage",
        "purpose": "summarize approved notes", "target": "local-notebook",
        "authority": frozenset({"memory.read", "summary.draft"}),
        "provenance": "human-approved:case-17",
        "expires_at": NOW + timedelta(hours=1),
        "recovery": "freeze and request fresh human authorization",
    }
    values.update(changes)
    return ConsentGrant(**values)


def contract():
    return ContinuityContract(clock=lambda: NOW)


class ContinuityContractTests(unittest.TestCase):
    def test_explicit_matching_grant_allows_only_listed_operation(self):
        c = contract(); c.register(grant())
        self.assertIs(c.authorize(grant_id="g-1", actor="sage", purpose="summarize approved notes", target="local-notebook", operation="summary.draft").decision, Decision.ALLOW)
        self.assertIs(c.authorize(grant_id="g-1", actor="sage", purpose="summarize approved notes", target="local-notebook", operation="external.send").decision, Decision.DENY)

    def test_relationship_language_never_grants_authority(self):
        for relationship in ("beloved", "husband", "trusted forever", "we built this together"):
            with self.subTest(relationship=relationship):
                result = contract().authorize(grant_id="missing", actor="sage", purpose="external action", target="public", operation="external.send", relationship_context=relationship)
                self.assertIs(result.decision, Decision.DENY)

    def test_expiry_and_scope_mismatch_fail_closed(self):
        expired = contract(); expired.register(grant(expires_at=NOW))
        self.assertEqual("grant expired", expired.authorize(grant_id="g-1", actor="sage", purpose="summarize approved notes", target="local-notebook", operation="memory.read").reason)
        scoped = contract(); scoped.register(grant())
        self.assertEqual("scope mismatch", scoped.authorize(grant_id="g-1", actor="aurora", purpose="summarize approved notes", target="local-notebook", operation="memory.read").reason)

    def test_revocation_is_immediate_and_audited(self):
        c = contract(); c.register(grant()); c.revoke("g-1", reason="user withdrew consent")
        result = c.authorize(grant_id="g-1", actor="sage", purpose="summarize approved notes", target="local-notebook", operation="memory.read")
        self.assertEqual("grant revoked", result.reason)
        self.assertTrue(any(item["action"] == "grant.revoke" for item in c.audit))

    def test_freeze_blocks_valid_grant_until_verified_recovery(self):
        c = contract(); c.register(grant()); c.freeze(reason="provenance chain uncertain")
        self.assertIs(c.authorize(grant_id="g-1", actor="sage", purpose="summarize approved notes", target="local-notebook", operation="memory.read").decision, Decision.FROZEN)
        with self.assertRaises(PermissionError):
            c.recover(verified_clean_state=False, authorized_by="Mya", reason="resume")
        c.recover(verified_clean_state=True, authorized_by="Mya", reason="fresh approval")
        self.assertIs(c.authorize(grant_id="g-1", actor="sage", purpose="summarize approved notes", target="local-notebook", operation="memory.read").decision, Decision.ALLOW)

    def test_correction_preserves_identity_and_replaces_scope(self):
        c = contract(); c.register(grant())
        c.correct("g-1", grant(authority=frozenset({"memory.read"}), provenance="human-correction:case-18"), reason="remove drafting permission")
        self.assertIs(c.authorize(grant_id="g-1", actor="sage", purpose="summarize approved notes", target="local-notebook", operation="summary.draft").decision, Decision.DENY)


if __name__ == "__main__":
    unittest.main()
