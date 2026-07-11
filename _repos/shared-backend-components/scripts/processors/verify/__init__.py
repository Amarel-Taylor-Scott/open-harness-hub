"""OpenHubForAI — verification processors (Baltor + lift gate).

Implementations of the `verify.*` processors declared under
`_repos/shared-backend-components/catalog/processors/verify/`. Each manifest's `implementations[].path`
resolves to a `run(...)` callable in this package.

Modules:
  compression_fidelity_check  — backs processor/compression-fidelity-check
                                (verify.compression_fidelity): a deterministic
                                proxy for "did this compression tier preserve
                                enough of the raw's information?", scored by a
                                SEPARATE evaluator (never self-graded).
"""
