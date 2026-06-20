# Conflict Detection — section card

Section: `conflict_detection` (category: reconciliation) · critical-path.

## Purpose

Before context can be served, contradictions between facts must be SURFACED, not silently averaged away.
Conflict detection runs deterministic detectors over the artifact ledger — rules you can prove, no model in
the loop: deadline/numeric mismatch (Reg E "10 business days" vs FAQ "30 days"), field-value mismatch (same
complaint_id + field + different current value), and source-handle divergence (same source_handle, different
content_hash). Each detected `conflict` is the input the reconciler resolves and the gate refuses to serve
until resolved.

## Owner module

`scripts/artifact_graph/conflict_detector.py` — `ConflictDetector.detect(...)`. Every `conflict_id` is a
deterministic hash of the conflicting artifacts + rule, so detections are content-addressed and stable.

## Contracts

Input: `atomic_fact`. Output: `conflict`. Registered runtime owner `ConflictDetector`
(`architecture/runtime_ownership.json#ConflictDetector`).

## Proof scripts

`scripts/check_cfpb_conflict_detection.py` (registered in the flywheel) — asserts the Reg E vs FAQ deadline
conflict (and the other rule classes) are detected deterministically.

## Commands

```bash
PYTHONPATH=. python3 scripts/check_cfpb_conflict_detection.py --self-test
```

## Limitations

Detectors are rule-based and topic-scoped (deadline/numeric, field-value, source-handle); semantic
contradictions outside these rules are not yet detected. No model is used by design — that is the guarantee,
and also the bound.

## Opportunities

Add detector classes for new conflict shapes behind the same `conflict` contract; feed detection signals into
the freshness watchtower for volatile facts.
