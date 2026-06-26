"""OpenHubForAI — platform-action processor implementations.

This package holds the Python implementations of the deterministic
"Platform actions (on-platform)" bucket processors declared in
``catalog/processors/platform/``. Each manifest's
``implementations[].path`` resolves to a ``run(...)`` callable in the
matching module here.

Design contract (one source of truth is the manifest, not this prose):
  * Each ``run()`` takes the manifest's named ``inputs`` and returns a dict
    carrying the manifest's named ``outputs``.
  * These are PLANNERS, not live-infra clients: they compute a deterministic,
    content-addressed representation of the platform write (the row/plan that
    *would* be persisted) and never open a network/database/object-store
    connection. That keeps them side-effect free, reproducible, and safe to run
    in CI — the same posture as the ``scripts/db/*`` load planners. Actual
    application is a separate, explicitly-approved step.
  * Determinism: identical inputs produce identical content hashes and ids, so a
    re-run collapses on the platform's natural key instead of duplicating.

Shared helpers live in ``_platform_base`` so the per-action modules stay thin
and the hashing/id/plan-row logic is defined exactly once (no-magic-values).
"""
