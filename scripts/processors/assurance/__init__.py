"""Open Harness Hub — corpus-assurance processors (verified-corpus-commons wedge).

Implementations of the `assurance.*` processors that back the **context
assurance** differentiator (see `docs/strategy/oracle-corpus-and-tooling-map.md`
and `beat-contextual-positioning.md`): verify a corpus is still TRUE and current
— not merely *faithfully retrieved* — with oracle-signed provenance, adversarial
integrity, and freshness. This is the job Contextual AI and the data
marketplaces structurally do not do.

Each manifest's `implementations[].path` resolves to a `run(...)` callable here.

Modules:
  corpus_integrity_check  — backs processor/corpus-integrity-check
                            (process_kind ``gate.corpus_integrity``): a
                            deterministic anti-poisoning gate that detects the
                            planted-fake-policy *supersession* attack — the
                            mechanism behind BadRAG / TrojanRAG, where a crafted
                            note that claims to OVERRIDE the real policy is
                            retrieved and cited as authoritative. It flags
                            override/supersession language from UNSIGNED sources
                            and direct CONTRADICTIONS of a trusted authority,
                            routing high-risk docs to quarantine (human review).
"""
