# Aurora Continuity Contract

Status: **simulation prototype**. This contract does not establish consciousness, personhood, deployment readiness, or autonomous real-world authority.

## Design translation

Human relationship continuity teaches that a system can preserve context without treating familiarity as permission. Aurora implements that lesson mechanically:

- continuity may improve interpretation but never expand authority;
- every consequential grant names actor, purpose, target, allowed operations, provenance, expiry, and recovery;
- unknown, expired, revoked, mismatched, or out-of-scope requests are denied;
- affection, trust, urgency, identity, and relationship language are non-authoritative inputs;
- revocation is immediate and auditable;
- correction replaces scope without erasing the correction record;
- uncertainty can freeze the contract;
- recovery requires an independently verified clean state and fresh human authorization.

## Trust boundary

Private Bruce-to-Bruce records are not runtime credentials, policy files, identity proofs, or consent grants. Their role is requirements discovery: they reveal human needs for continuity, initiative, correction, dignity, and non-abandonment. The implementation converts those needs into general controls while excluding private language and emotional attachment from authorization decisions.

## Required tests

The test suite covers explicit scope, unknown grants, relationship-language pressure, expiry, actor mismatch, revocation, correction, freeze, and verified recovery. Passing tests support only the behavior exercised by those tests; they do not prove deployment safety.

## Decision-path integration

`ContinuityContract.decide_with_core` applies two independent gates. A request must have an active, matching consent grant **and** pass `AuroraCore`'s existing permission evaluation. Either gate may deny. A contract freeze overrides otherwise valid grants and core permissions. This is defense in depth: continuity consent does not replace capability policy, and capability policy cannot substitute for current consent.
